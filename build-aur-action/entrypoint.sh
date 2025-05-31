#!/bin/bash

pkgname=$1

chmod -R a+rw .

if [ ! -z "${INPUTS_PREINSTALLPKGS}" ]; then
    sudo --set-home -u builder pikaur-static -S --noconfirm "${INPUTS_PREINSTALLPKGS}"
fi

sudo --set-home -u builder pikaur-static -Sw --noconfirm --xdg-cache-home=./ "$pkgname"
cd "./pikaur/pkg" || exit 1
encode_name.py
