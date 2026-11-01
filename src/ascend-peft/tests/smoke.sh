#!/bin/bash
# Check PEFT package metadata on ARM64 without requiring NPU devices.
set -euo pipefail

test "$(uname -m)" = "aarch64"
ascend-pip-check
python3 - <<'PYTHON'
from importlib.metadata import version

assert version("torch").split("+")[0] == "2.14.0"
assert version("torch-npu") == "2.14.0"
assert version("accelerate") == "1.15.0"
assert version("huggingface-hub") == "1.30.0"
assert version("peft") == "0.20.0"
assert version("transformers") == "5.5.0"
assert version("torchvision") == "0.29.2"
PYTHON
