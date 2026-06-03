#!/bin/bash
set -euo pipefail

target=${1:?Package name or package directory is required}
workspace=$PWD
build_mode=${BUILD_MODE:-aur}
skip_pgp_check=${SKIP_PGP_CHECK:-true}
pikaur_args=(--noconfirm)

case "$skip_pgp_check" in
    1|true|TRUE|yes|YES)
        pikaur_args+=(--mflags=--skippgpcheck)
        ;;
esac

chmod -R a+rw .

sudo pacman -Syu --noconfirm

if [[ -n "${PREINSTALL_PKGS:-}" ]]; then
    # PREINSTALL_PKGS is intentionally split so callers can pass a package list.
    # shellcheck disable=SC2086
    sudo --set-home -u builder pikaur -S "${pikaur_args[@]}" ${PREINSTALL_PKGS}
fi

collect_packages() {
    local source_dir=$1

    if compgen -G "${source_dir}/*.pkg.tar.*" > /dev/null; then
        mv "${source_dir}"/*.pkg.tar.* "$workspace"/
    fi
}

case "$build_mode" in
    aur)
        sudo --set-home -u builder pikaur -Sw "${pikaur_args[@]}" --xdg-cache-home="$workspace" "$target"
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
        sudo --set-home -u builder pikaur -P "${pikaur_args[@]}" --xdg-cache-home="$workspace" ./PKGBUILD
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
