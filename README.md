This repo is forked from [https://github.com/vifly/arch-build](https://github.com/vifly/arch-build). For more technical details, refer to the original repo. 

This project publish a docker image for building aur packages. You can use it like below:
```Bash
docker run --rm \
        -v ${workspace}:/workspace \
        -w /workspace \
        -e PREINSTALL_PKGS=${packages that need to be installed before building} \
        ghcr.io/chenxiex/arch-build/build-aur-action-image:latest ${packages that need to be built}
```
`${workspace}` is the output path. Not only the specified packages but also the dependencies in aur will be there.

# Usage
The packages are located at Cloudflare R2 and GitHub releases, choose one of you like.

Add the following code snippet to your `/etc/pacman.conf` (choose one):

```
# Download from Cloudflare R2
[anlor]
Server = https://archrepo.anlor.top
```

or

```
# Download from GitHub releases
[anlor]
Server = https://github.com/chenxiex/arch-build/releases/latest/download
```

And import my pubkey:

```Bash
wget -O /tmp/anlor.asc 'https://archrepo.anlor.top/anlor.asc' && sudo pacman-key --add /tmp/anlor.asc
sudo pacman-key --lsign-key chenxiex@outlook.com
```

Then, run `sudo pacman -Syu` to update the repository and upgrade the system.

Now you can use `sudo pacman -S <pkg_name>` to install packages from my repository.

# Tips
Unlike the upstream repo, this repo use [nvchecker](https://github.com/lilydjwg/nvchecker) to build only the packages that need update. The packages to build is defined in [nvchecker.toml](nvchecker/nvchecker.toml). To force rebuilding a package, install [nvchecker](https://github.com/lilydjwg/nvchecker) and run:
```
nvtake -c nvchecker/nvchecker.toml PACKAGE_NAME=none
```
then commit and push.