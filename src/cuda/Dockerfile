# syntax=docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e

ARG BASE_IMAGE
FROM ${BASE_IMAGE}

ARG DEFAULT_USER=root
ARG DEFAULT_UID=1000
ARG DEFAULT_GID=1000
ARG TZ=Asia/Shanghai
ARG CMAKE_VERSION=4.3.2
ARG DEVSHELL=false
ARG PACKAGE_MIRROR=upstream
ARG SSH_MODE=password
ARG WORKSPACE_DIR=/work

LABEL org.opencontainers.image.description="Linux amd64 NVIDIA CUDA development environment"

COPY --chmod=0755 src/_scripts/system.sh /tmp/image-scripts/system.sh
RUN /tmp/image-scripts/system.sh --timezone "${TZ}"

COPY --chmod=0755 src/_scripts/dev-tools.sh /tmp/image-scripts/dev-tools.sh
RUN /tmp/image-scripts/dev-tools.sh

COPY --chmod=0755 src/_scripts/python-install.sh /tmp/image-scripts/python-install.sh
RUN /tmp/image-scripts/python-install.sh

COPY --chmod=0755 src/_scripts/cmake.sh /tmp/image-scripts/cmake.sh
RUN /tmp/image-scripts/cmake.sh --version "${CMAKE_VERSION}"

COPY --chmod=0755 src/_scripts/pip-packages.sh /tmp/image-scripts/pip-packages.sh
RUN /tmp/image-scripts/pip-packages.sh

COPY --chmod=0755 src/_scripts/user.sh /tmp/image-scripts/user.sh
RUN /tmp/image-scripts/user.sh \
      --username "${DEFAULT_USER}" \
      --uid "${DEFAULT_UID}" \
      --gid "${DEFAULT_GID}"

COPY --chmod=0755 src/_scripts/ssh.sh /tmp/image-scripts/ssh.sh
RUN /tmp/image-scripts/ssh.sh \
      --default-user "${DEFAULT_USER}" \
      --mode "${SSH_MODE}"

COPY --chmod=0755 src/_scripts/workspace.sh /tmp/image-scripts/workspace.sh
RUN /tmp/image-scripts/workspace.sh \
      --path "${WORKSPACE_DIR}" \
      --owner "${DEFAULT_USER}"

COPY --chmod=0755 src/_scripts/devshell.sh /tmp/image-scripts/devshell.sh
USER ${DEFAULT_USER}
RUN /tmp/image-scripts/devshell.sh --enabled "${DEVSHELL}"
USER root

COPY --chmod=0755 src/_scripts/finalize-mirror.sh /tmp/image-scripts/finalize-mirror.sh
RUN /tmp/image-scripts/finalize-mirror.sh \
      --mirror "${PACKAGE_MIRROR}" \
    && rm -rf /tmp/image-scripts

COPY --chmod=0755 src/_assets/docker-entrypoint.sh /usr/local/bin/docker-entrypoint

ENV EDITOR=vim \
    DEFAULT_USER=${DEFAULT_USER} \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    PACKAGE_MIRROR=${PACKAGE_MIRROR} \
    SSH_MODE=${SSH_MODE} \
    TZ=${TZ} \
    VISUAL=vim \
    PAGER="less -FRX" \
    WORKSPACE_DIR=${WORKSPACE_DIR}

# The root name selects the existing account; any other valid name is created above.
USER ${DEFAULT_USER}
WORKDIR ${WORKSPACE_DIR}
EXPOSE 22
ENTRYPOINT ["/usr/local/bin/docker-entrypoint"]
CMD ["bash"]
