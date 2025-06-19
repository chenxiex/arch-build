This repo is forked from [https://github.com/vifly/arch-build](https://github.com/vifly/arch-build). For more technical details, refer to the original repo. 

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
