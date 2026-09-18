# syntax=docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e

ARG BASE_IMAGE
FROM ${BASE_IMAGE}

ARG USERNAME=luciole
ARG USER_UID=1000
ARG USER_GID=1000
ARG TZ=Asia/Shanghai
ARG PACKAGE_MIRROR=upstream
ARG SSH_MODE=disabled

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    PACKAGE_MIRROR=${PACKAGE_MIRROR} \
    SSH_MODE=${SSH_MODE} \
    TZ=${TZ} \
    USERNAME=${USERNAME}

COPY src/_scripts/system.sh src/_scripts/user.sh src/_scripts/ssh.sh \
    src/_scripts/finalize-mirror.sh /tmp/image-scripts/
COPY src/_assets/docker-entrypoint.sh /usr/local/bin/docker-entrypoint

RUN chmod +x /tmp/image-scripts/*.sh /usr/local/bin/docker-entrypoint \
    && /tmp/image-scripts/system.sh --timezone "${TZ}" \
    && /tmp/image-scripts/user.sh \
       --username "${USERNAME}" \
       --uid "${USER_UID}" \
       --gid "${USER_GID}" \
    && /tmp/image-scripts/ssh.sh --username "${USERNAME}" \
    && if [ "${PACKAGE_MIRROR}" = "aliyun" ]; then \
         /tmp/image-scripts/finalize-mirror.sh; \
       elif [ "${PACKAGE_MIRROR}" != "upstream" ]; then \
         echo "unsupported PACKAGE_MIRROR=${PACKAGE_MIRROR}" >&2; exit 64; \
       fi \
    && rm -rf /tmp/image-scripts

USER ${USERNAME}
WORKDIR /home/${USERNAME}
ENTRYPOINT ["/usr/local/bin/docker-entrypoint"]
CMD ["bash"]
