#!/bin/bash
set -euo pipefail

target=${1:?Package name or package directory is required}
workspace=$PWD
build_mode=${BUILD_MODE:-aur}
pgp_keyserver=${PGP_KEYSERVER:-hkps://keyserver.ubuntu.com}

chmod -R a+rw .

sudo pacman -Syu --noconfirm

setup_gnupg() {
    sudo install -d -m 700 -o builder -g builder /home/builder/.gnupg
    sudo --set-home -u builder tee /home/builder/.gnupg/gpg.conf > /dev/null << EOF
keyserver $pgp_keyserver
keyserver-options auto-key-retrieve
auto-key-retrieve
EOF
    sudo --set-home -u builder gpg --batch --list-keys > /dev/null 2>&1 || true

    if [[ -n "${PGP_KEYS:-}" ]]; then
        # PGP_KEYS is intentionally split so callers can pass a key list.
        # shellcheck disable=SC2086
        sudo --set-home -u builder gpg --batch --keyserver "$pgp_keyserver" --recv-keys ${PGP_KEYS}
    fi
}

setup_gnupg

if [[ -n "${PREINSTALL_PKGS:-}" ]]; then
    # PREINSTALL_PKGS is intentionally split so callers can pass a package list.
    # shellcheck disable=SC2086
    sudo --set-home -u builder pikaur -S --noconfirm ${PREINSTALL_PKGS}
fi

collect_packages() {
    local source_dir=$1

    if compgen -G "${source_dir}/*.pkg.tar.*" > /dev/null; then
        mv "${source_dir}"/*.pkg.tar.* "$workspace"/
    fi
}

case "$build_mode" in
    aur)
        sudo --set-home -u builder pikaur -Sw --noconfirm --xdg-cache-home="$workspace" "$target"
        collect_packages "$workspace/pikaur/pkg"
        ;;
    local)
        pkgdir=$target
        if [[ ! -d "$pkgdir" ]]; then
            echo "Package directory does not exist: $pkgdir" >&2
            exit 1
        fi
        if [[ ! -f "$pkgdir/PKGBUILD" ]]; then
            echo "Package directory does not contain a PKGBUILD: $pkgdir" >&2
            exit 1
        fi

        cd "$pkgdir"
        sudo --set-home -u builder pikaur -P --noconfirm --xdg-cache-home="$workspace" ./PKGBUILD
        cd "$workspace"

        collect_packages "$workspace/pikaur/pkg"
        collect_packages "$pkgdir"
        ;;
    *)
        echo "Unsupported BUILD_MODE: $build_mode" >&2
        exit 1
        ;;
esac

rm -rf "$workspace/pikaur"
encode_name.py
