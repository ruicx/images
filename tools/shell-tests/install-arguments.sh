#!/bin/bash
# Verify the non-mutating getopt interface of parameterized install scripts.
set -euo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

scripts=(
    "src/_scripts/cmake.sh|--version"
    "src/_scripts/cpptrace.sh|--version"
    "src/_scripts/devshell.sh|--enabled"
    "src/_scripts/finalize-mirror.sh|--mirror"
    "src/_scripts/iceoryx.sh|--version"
    "src/_scripts/libdatachannel.sh|--version"
    "src/_scripts/llama-cpp.sh|--version"
    "src/_scripts/precommit.sh|--config"
    "src/_scripts/ros2.sh|--distro"
    "src/_scripts/rpclib.sh|--version"
    "src/_scripts/ssh.sh|--default-user"
    "src/_scripts/system.sh|--timezone"
    "src/_scripts/user.sh|--username"
    "src/_scripts/workspace.sh|--path"
)

no_argument_scripts=(
    "src/_scripts/dev-tools.sh"
)

expect_usage_error() {
    local script="$1"
    shift
    local status

    set +e
    bash "${script}" "$@" >/dev/null 2>&1
    status=$?
    set -e
    if [ "${status}" -ne 64 ]; then
        echo "expected exit 64 from ${script} $*, got ${status}" >&2
        exit 1
    fi
}

for specification in "${scripts[@]}"; do
    script="${REPOSITORY_ROOT}/${specification%%|*}"
    required_option="${specification##*|}"
    bash "${script}" --help >/dev/null
    expect_usage_error "${script}" --unknown-option
    expect_usage_error "${script}" "${required_option}"
    expect_usage_error "${script}" unexpected-positional
done

# Reject the removed account selector and exercise the remaining mode option.
ssh_script="${REPOSITORY_ROOT}/src/_scripts/ssh.sh"
expect_usage_error "${ssh_script}" --login-user default
expect_usage_error "${ssh_script}" --mode

# YAML booleans are stringified by the Python planner, so the script owns normalization.
devshell_script="${REPOSITORY_ROOT}/src/_scripts/devshell.sh"
for disabled_value in false False FALSE 0 no NO off disabled; do
    bash "${devshell_script}" --enabled "${disabled_value}"
done
expect_usage_error "${devshell_script}" --enabled sometimes

# Upstream is a non-mutating success path; mirror selection owns value validation.
mirror_script="${REPOSITORY_ROOT}/src/_scripts/finalize-mirror.sh"
bash "${mirror_script}" --mirror upstream >/dev/null
expect_usage_error "${mirror_script}" --mirror unsupported

# Exercise every value-taking option and format guard added to the llama.cpp capability.
llama_cpp_script="${REPOSITORY_ROOT}/src/_scripts/llama-cpp.sh"
expect_usage_error "${llama_cpp_script}" --cuda-version
expect_usage_error "${llama_cpp_script}" --version latest
expect_usage_error "${llama_cpp_script}" --cuda-version 12

# Selecting root must be a non-mutating success path owned by the user capability.
user_script="${REPOSITORY_ROOT}/src/_scripts/user.sh"
bash "${user_script}" --username root --uid 1000 --gid 1000

# Reject paths that could assign ownership to the filesystem root or escape lexically.
workspace_script="${REPOSITORY_ROOT}/src/_scripts/workspace.sh"
expect_usage_error "${workspace_script}" --path / --owner root
expect_usage_error "${workspace_script}" --path /work/../other --owner root
expect_usage_error "${workspace_script}" --path relative --owner root
expect_usage_error "${workspace_script}" --path /work --owner "Invalid Owner"
expect_usage_error "${workspace_script}" --path /work --owner user-that-does-not-exist

for script_name in "${no_argument_scripts[@]}"; do
    script="${REPOSITORY_ROOT}/${script_name}"
    bash "${script}" --help >/dev/null
    expect_usage_error "${script}" --unknown-option
    expect_usage_error "${script}" unexpected-positional
done
