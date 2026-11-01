# syntax=docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e

FROM ascend_base

COPY src/ascend-peft/requirements.txt /tmp/image-scripts/peft-requirements.txt

COPY --chmod=0755 src/_scripts/python/ascend-python-packages.sh /tmp/image-scripts/ascend-python-packages.sh
RUN --mount=type=cache,target=/tmp/pip-cache,mode=0777 \
    PIP_CACHE_DIR=/tmp/pip-cache \
    /tmp/image-scripts/ascend-python-packages.sh --requirements /tmp/image-scripts/peft-requirements.txt \
    && rm -rf /tmp/image-scripts
