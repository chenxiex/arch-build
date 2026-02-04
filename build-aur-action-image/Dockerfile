FROM archlinux:latest

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN date
COPY makepkg.conf /etc/makepkg.conf.d/makepkg.conf
COPY encode_name.py /usr/local/bin/encode_name.py
COPY entrypoint.sh /entrypoint.sh

RUN pacman-key --init
RUN pacman -Syu --noconfirm
RUN pacman -S --needed --noconfirm base-devel git python 
RUN pacman -S --needed --noconfirm curl jq
RUN tee -a /etc/pacman.conf << 'EOF'
[archlinuxcn]
Server = https://repo.archlinuxcn.org/$arch
EOF
RUN pacman -Sy --noconfirm && pacman -S --noconfirm archlinuxcn-keyring
RUN pacman -S --needed --noconfirm pikaur

RUN useradd builder -m
RUN echo "builder ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
RUN git config --global --add safe.directory /workspace

ENTRYPOINT ["/entrypoint.sh"] 
