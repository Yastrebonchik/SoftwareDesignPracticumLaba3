FROM ubuntu:24.04@sha256:2198e4c65076e9cb0b3d695219df667c0e3b0072da64ca3c2648aca17dcecaf5
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends openssh-server python3 python3-apt ca-certificates curl procps \
    && rm -rf /var/lib/apt/lists/* /etc/ssh/ssh_host_*
COPY docker/node/sshd.conf /etc/ssh/sshd_config.d/lab.conf
COPY docker/node/entrypoint.sh /usr/local/bin/node-entrypoint
RUN chmod 755 /usr/local/bin/node-entrypoint
EXPOSE 22
ENTRYPOINT ["/usr/local/bin/node-entrypoint"]
