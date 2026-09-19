#!/bin/bash
# Verify the non-mutating getopt interface of parameterized install scripts.
set -euo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

scripts=(
    "src/_scripts/cmake.sh|--version"
    "src/_scripts/cpptrace.sh|--version"
    "src/_scripts/devshell.sh|--enabled"
    "src/_scripts/iceoryx.sh|--version"
    "src/_scripts/libdatachannel.sh|--version"
    "src/_scripts/precommit.sh|--config"
    "src/_scripts/ros2.sh|--distro"
    "src/_scripts/rpclib.sh|--version"
    "src/_scripts/ssh.sh|--default-user"
    "src/_scripts/system.sh|--timezone"
    "src/_scripts/user.sh|--username"
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

# Exercise every value-taking option added to the SSH capability.
ssh_script="${REPOSITORY_ROOT}/src/_scripts/ssh.sh"
expect_usage_error "${ssh_script}" --login-user
expect_usage_error "${ssh_script}" --mode

# YAML booleans are stringified by the Python planner, so the script owns normalization.
devshell_script="${REPOSITORY_ROOT}/src/_scripts/devshell.sh"
for disabled_value in false False FALSE 0 no NO off disabled; do
    bash "${devshell_script}" --enabled "${disabled_value}"
done
expect_usage_error "${devshell_script}" --enabled sometimes

for script_name in "${no_argument_scripts[@]}"; do
    script="${REPOSITORY_ROOT}/${script_name}"
    bash "${script}" --help >/dev/null
    expect_usage_error "${script}" --unknown-option
    expect_usage_error "${script}" unexpected-positional
done
