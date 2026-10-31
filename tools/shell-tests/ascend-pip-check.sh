#!/bin/bash
# Verify that the Ascend exception never hides new dependency failures or pip errors.
set -euo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
checker="${REPOSITORY_ROOT}/src/_assets/ascend-pip-check.sh"
test_dir="$(mktemp -d)"
trap 'rm -rf "${test_dir}"' EXIT
cat >"${test_dir}/python3" <<'EOF'
#!/bin/bash
set -euo pipefail
test "$#" -eq 3
test "$1" = "-m"
test "$2" = "pip"
test "$3" = "check"
printf '%s\n' "${CHECK_OUTPUT}"
if [ -n "${CHECK_STDERR:-}" ]; then
    printf '%s\n' "${CHECK_STDERR}" >&2
fi
exit "${CHECK_STATUS}"
EOF
chmod +x "${test_dir}/python3"

check_case() {
    local pip_status="$1" diagnostic="$2" expected_status="$3" expected_text="$4"
    local actual_status=0 result
    result="$(CHECK_STATUS="${pip_status}" CHECK_OUTPUT="${diagnostic}" CHECK_STDERR="${5:-}" \
        PATH="${test_dir}:${PATH}" bash "${checker}" 2>&1)" || actual_status=$?
    if [ "${actual_status}" -ne "${expected_status}" ] || [[ "${result}" != *"${expected_text}"* ]]; then
        printf 'Unexpected check result: status=%s, output=%s\n' "${actual_status}" "${result}" >&2
        exit 1
    fi
}

known='mindstudio-kl 26.2.0 has requirement numpy<=1.26.4, but you have numpy 2.5.4.'
missing='msboost 26.2.0 requires colorlog, which is not installed.'
check_case 0 'No broken requirements found.' 0 'No broken requirements found.'
check_case 1 "${known}" 0 'WARNING: allowing known upstream dependency conflict:'
check_case 1 "${known}"$'\n'"${missing}" 1 "${missing}"
check_case 1 "${missing}"$'\n'"${known}" 1 "${missing}"
check_case 1 "${missing}" 1 "${missing}"
check_case 1 "${known/26.2.0/26.2.1}" 1 'mindstudio-kl 26.2.1'
check_case 1 "${known/2.5.4/2.5.5}" 1 'numpy 2.5.5'
check_case 1 "${known/1.26.4/1.25.0}" 1 'numpy<=1.25.0'
check_case 1 '' 1 ''
check_case 2 "${known}" 2 "${known}"
check_case 1 "${known}" 1 'ERROR: pip failed' 'ERROR: pip failed'
