This repo is forked from [https://github.com/vifly/arch-build](https://github.com/vifly/arch-build). For more technical details, refer to the original repo. 

该项目额外发布一个预构建镜像，可用于构建 AUR 软件包。使用方法：
```Bash
docker run --rm \
        -v ${工作目录}:/workspace \
        -w /workspace \
        -e PREINSTALL_PKGS=${需要提前安装的软件包，用于依赖无法自动识别的情况} \
        ghcr.io/chenxiex/arch-build/build-aur-action-image:latest ${需要构建的软件包名}
```
软件包，包括所有依赖的 AUR 包和提前安装的 AUR 包，会被输出到 `${工作目录}` 下。

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
