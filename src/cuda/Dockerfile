# syntax=docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e

ARG BASE_IMAGE
FROM ${BASE_IMAGE}

ARG DEFAULT_USER=root
ARG DEFAULT_UID=1000
ARG DEFAULT_GID=1000
ARG TZ=Asia/Shanghai
ARG CMAKE_VERSION=4.3.2
ARG PACKAGE_MIRROR=upstream
ARG SSH_MODE=password
ARG SSH_LOGIN_USER=default

LABEL org.opencontainers.image.description="Linux amd64 NVIDIA CUDA development environment"

COPY --chmod=0755 src/_scripts/system.sh /tmp/image-scripts/system.sh
RUN /tmp/image-scripts/system.sh --timezone "${TZ}"

COPY --chmod=0755 src/_scripts/dev-tools.sh /tmp/image-scripts/dev-tools.sh
RUN /tmp/image-scripts/dev-tools.sh

COPY --chmod=0755 src/_scripts/cmake.sh /tmp/image-scripts/cmake.sh
RUN /tmp/image-scripts/cmake.sh --version "${CMAKE_VERSION}"

COPY --chmod=0755 src/_scripts/user.sh src/_scripts/ssh.sh /tmp/image-scripts/
RUN if [ "${DEFAULT_USER}" != "root" ]; then \
      /tmp/image-scripts/user.sh \
        --username "${DEFAULT_USER}" \
        --uid "${DEFAULT_UID}" \
        --gid "${DEFAULT_GID}"; \
    fi \
    && /tmp/image-scripts/ssh.sh \
      --default-user "${DEFAULT_USER}" \
      --login-user "${SSH_LOGIN_USER}" \
      --mode "${SSH_MODE}" \
    && mkdir -p /work \
    && if [ "${DEFAULT_USER}" != "root" ]; then \
      chown "${DEFAULT_USER}:${DEFAULT_USER}" /work; \
    fi

COPY --chmod=0755 src/_scripts/finalize-mirror.sh /tmp/image-scripts/finalize-mirror.sh
RUN if [ "${PACKAGE_MIRROR}" = "aliyun" ]; then \
      /tmp/image-scripts/finalize-mirror.sh; \
    elif [ "${PACKAGE_MIRROR}" != "upstream" ]; then \
      echo "unsupported PACKAGE_MIRROR=${PACKAGE_MIRROR}" >&2; exit 64; \
    fi \
    && rm -rf /tmp/image-scripts

COPY --chmod=0755 src/_assets/docker-entrypoint.sh /usr/local/bin/docker-entrypoint

ENV EDITOR=vim \
    DEFAULT_USER=${DEFAULT_USER} \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    PACKAGE_MIRROR=${PACKAGE_MIRROR} \
    SSH_LOGIN_USER=${SSH_LOGIN_USER} \
    SSH_MODE=${SSH_MODE} \
    TZ=${TZ} \
    VISUAL=vim

# The root name selects the existing account; any other valid name is created above.
USER ${DEFAULT_USER}
WORKDIR /work
EXPOSE 22
ENTRYPOINT ["/usr/local/bin/docker-entrypoint"]
CMD ["bash"]
