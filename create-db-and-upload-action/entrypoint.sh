#!/bin/bash
set -e

init_path=$PWD
mkdir upload_packages
find "$local_path" -path "$init_path/upload_packages" -prune -o -path "./upload_packages" -prune -o -type f -name "*.pkg.*" -exec bash -c '
    for file; do cp -f -t ./upload_packages/ "$file" || exit 1; done
' _ {} +
BUILT_PACKAGES_MANIFEST=$(mktemp)
trap 'rm -f "$BUILT_PACKAGES_MANIFEST"' EXIT
find ./upload_packages -maxdepth 1 -type f -name '*.pkg.tar.*' ! -name '*.sig' -printf '%f\n' > "$BUILT_PACKAGES_MANIFEST"
if [[ "${REBUILD:-false}" == "true" && ! -s "$BUILT_PACKAGES_MANIFEST" ]]; then
    echo "No built package files found for rebuild" >&2
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

if [[ "${REBUILD:-false}" != "true" ]]; then
    echo "::group::Merging remote packages"

    repo-add "./${repo_name:?}.db.tar.gz" ./*.tar.zst

    python3 "$init_path/create-db-and-upload-action/sync.py"

    echo "::endgroup::"

    rm "./${repo_name:?}.db.tar.gz"
    rm "./${repo_name:?}.files.tar.gz"
fi

echo "::group::Generating repository database and signing packages"

declare -A built_packages=()
while IFS= read -r name; do
    built_packages["$name"]=1
done < "$BUILT_PACKAGES_MANIFEST"

for name in ./*.pkg.tar.*; do
    [[ -f "$name" && "$name" != *.sig ]] || continue
    if [ ! -z "$gpg_key" ]; then
        if [[ -n "${built_packages[${name#./}]:-}" || ! -f "$name.sig" ]]; then
            gpg --detach-sig --yes "$name"
        fi
        repo-add --verify --sign "./${repo_name:?}.db.tar.gz" "$name"
    else
        repo-add "./${repo_name:?}.db.tar.gz" "$name"
    fi
done

echo "::endgroup::" 

echo "::group::Uploading to remote"
python3 "$init_path/create-db-and-upload-action/upload.py"
echo "::endgroup::"
