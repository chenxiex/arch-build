#!/bin/bash
set -e

init_path=$PWD
mkdir upload_packages
find "$local_path" -path "$init_path/upload_packages" -prune -o -path "./upload_packages" -prune -o -type f -name "*.pkg.*" -exec bash -c '
    for file; do cp -f -t ./upload_packages/ "$file" || exit 1; done
' _ {} +
export REFRESH_MANIFEST
REFRESH_MANIFEST=$(mktemp)
find ./upload_packages -maxdepth 1 -type f -name '*.pkg.tar.*' ! -name '*.sig' -printf '%f\n' > "$REFRESH_MANIFEST"
if [[ "${FORCE_REUPLOAD:-false}" == "true" && ! -s "$REFRESH_MANIFEST" ]]; then
    echo "No built package files found to refresh" >&2
    exit 1
fi
cp -dr "$init_path/static/." ./upload_packages/

echo "$RCLONE_CONFIG_NAME"

if [ ! -f ~/.config/rclone/rclone.conf ]; then
    mkdir --parents ~/.config/rclone
    echo "$RCLONE_CONFIG_CONTENT" >> ~/.config/rclone/rclone.conf
fi

if [ ! -z "$gpg_key" ]; then
    echo "$gpg_key" | gpg --import
fi

cd upload_packages || exit 1

echo "::group::Removing old packages"

repo-add "./${repo_name:?}.db.tar.gz" ./*.tar.zst

python3 $init_path/create-db-and-upload-action/sync.py 

echo "::endgroup::" 

rm "./${repo_name:?}.db.tar.gz"
rm "./${repo_name:?}.files.tar.gz"

echo "::group::Signing packages"

if [ ! -z "$gpg_key" ]; then
    declare -A built_packages=()
    while IFS= read -r name; do
        built_packages["$name"]=1
    done < "$REFRESH_MANIFEST"

    for name in ./*.pkg.tar.*; do
        [[ -f "$name" && "$name" != *.sig ]] || continue
        if [[ -n "${built_packages[${name#./}]:-}" || ! -f "$name.sig" ]]; then
            gpg --detach-sig --yes "$name"
        fi
        if [[ "${FORCE_REUPLOAD:-false}" == "true" && -n "${built_packages[${name#./}]:-}" ]]; then
            printf '%s.sig\n' "${name#./}" >> "$REFRESH_MANIFEST"
        fi
        repo-add --verify --sign "./${repo_name:?}.db.tar.gz" "$name"
    done
fi

echo "::endgroup::" 

if [[ "${FORCE_REUPLOAD:-false}" == "true" ]]; then
    # Keep this separate from the built package list used for signing above.
    find -L "$init_path/static" -type f -printf '%P\n' >> "$REFRESH_MANIFEST"
fi

echo "::group::Uploading to remote"
python3 $init_path/create-db-and-upload-action/upload.py 
echo "::endgroup::"