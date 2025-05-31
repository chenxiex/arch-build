#!/bin/bash

pkgname=$1

WORKSPACE_DIR="$(pwd)"

chmod -R a+rw .

if [ ! -z "${INPUTS_PREINSTALLPKGS}" ]; then
    sudo --set-home -u builder pikaur-static -S --noconfirm "${INPUTS_PREINSTALLPKGS}"
fi

sudo --set-home -u builder pikaur-static -Sw --noconfirm --xdg-cache-home=./ "$pkgname"
cd "./pikaur/pkg" || exit 1
python3 "${WORKSPACE_DIR}/build-aur-action/encode_name.py"
