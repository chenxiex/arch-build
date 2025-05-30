FROM archlinux:latest

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN date
RUN pacman -Syu --noconfirm
RUN pacman -S --needed --noconfirm base-devel git python 
RUN pacman -S --needed --noconfirm curl jq
RUN VERSION=$(curl -s "https://api.github.com/repos/actionless/pikaur/releases/latest" | jq -r .tag_name); \
    curl --fail --retry 3 -sL "https://github.com/actionless/pikaur/releases/download/${VERSION}/pikaur-static-v${VERSION}.linux-x86_64.exe" -o /usr/bin/pikaur-static; \
    chmod +x /usr/bin/pikaur-static
COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"] 
