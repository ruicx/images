#!/bin/bash
# Check PEFT package metadata on ARM64 without requiring NPU devices.
set -euo pipefail

test "$(uname -m)" = "aarch64"
ascend-pip-check
python3 - <<'PYTHON'
from importlib.metadata import version
from pathlib import Path

base_versions = {}
for line in Path("/opt/image-python/base-constraints.txt").read_text(encoding="utf-8").splitlines():
    name, pinned_version = line.split("==", 1)
    base_versions[name.lower().replace("_", "-")] = pinned_version

for package in ("torch", "torch-npu"):
    expected = base_versions[package]
    actual = version(package)
    assert actual == expected, f"{package}: expected parent version {expected}, got {actual}"
for package in ("accelerate", "huggingface-hub", "peft", "transformers", "torchvision"):
    print(f"{package}=={version(package)}")
PYTHON
