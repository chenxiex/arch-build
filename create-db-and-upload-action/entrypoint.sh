#!/bin/bash
set -e

init_path=$PWD
mkdir upload_packages
find "$local_path" -path "./upload_packages" -prune -o -type f -name "*.pkg.*" -exec cp -t ./upload_packages/ {} +
cp -dr $init_path/static/* ./upload_packages/

echo "$RCLONE_CONFIG_NAME"

if [ ! -f ~/.config/rclone/rclone.conf ]; then
    mkdir --parents ~/.config/rclone
    echo "$RCLONE_CONFIG_CONTENT" >> ~/.config/rclone/rclone.conf
fi

if [ ! -z "$gpg_key" ]; then
    echo "$gpg_key" | gpg --import
fi

cd upload_packages || exit 1

echo "::group::Signing packages"

if [ ! -z "$gpg_key" ]; then
    packages=( "*.pkg.*" )
    for name in $packages
    do
        gpg --detach-sig --yes $name
    done
    repo-add --verify --sign "./${repo_name:?}.db.tar.gz" ./*.pkg.*
fi

echo "::endgroup::" 

echo "::group::Uploading to remote"
python3 $init_path/create-db-and-upload-action/upload.py 
echo "::endgroup::"