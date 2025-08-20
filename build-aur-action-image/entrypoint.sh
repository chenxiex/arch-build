#!/bin/bash

pkgname=$1

chmod -R a+rw .

sudo pacman -Syu --noconfirm

if [ ! -z "${PREINSTALL_PKGS}" ]; then
    sudo --set-home -u builder pikaur-static -S --noconfirm "${PREINSTALL_PKGS}"
fi

sudo --set-home -u builder pikaur-static -Sw --noconfirm --xdg-cache-home=./ "$pkgname"
mv ./pikaur/pkg/*.pkg.tar.* ./
rm -rf ./pikaur
encode_name.py
