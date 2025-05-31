#!/bin/bash

pkgname=$1

chmod -R a+rw .

if [ ! -z "${PREINSTALL_PKGS}" ]; then
    sudo --set-home -u builder pikaur-static -S --noconfirm "${PREINSTALL_PKGS}"
fi

sudo --set-home -u builder pikaur-static -Sw --noconfirm --xdg-cache-home=./ "$pkgname"
cd "./pikaur/pkg" || exit 1
encode_name.py
