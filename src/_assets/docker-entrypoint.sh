#!/bin/bash
# Shared container entrypoint. SSH is disabled unless SSH_MODE=key-only.
# Reads SSH_MODE (default: disabled) and USERNAME (default: luciole).
#
# The image's USER directive keeps PID 1 non-root. Passwordless sudo is used
# only for the runtime directories, host keys, and daemon required by the
# explicitly enabled key-only SSH mode.
set -euo pipefail

SSH_MODE_VAL="${SSH_MODE:-disabled}"
USERNAME_VAL="${USERNAME:-luciole}"

# Start sshd only after validating the explicit mode and mounted public key.
case "${SSH_MODE_VAL}" in
    disabled) ;;
    key-only)
        USER_HOME="$(getent passwd "${USERNAME_VAL}" | cut -d: -f6)"
        AUTHORIZED_KEYS="${USER_HOME}/.ssh/authorized_keys"
        if [ ! -s "${AUTHORIZED_KEYS}" ]; then
            echo "[entrypoint] SSH_MODE=key-only requires a non-empty ${AUTHORIZED_KEYS}" >&2
            exit 64
        fi
        sudo -n mkdir -p /run/sshd
        sudo -n ssh-keygen -A >/dev/null
        sudo -n /usr/sbin/sshd
        ;;
    *)
        echo "[entrypoint] unsupported SSH_MODE '${SSH_MODE_VAL}'" >&2
        exit 64
        ;;
esac

# Preserve the user command as PID 1 so signals propagate directly.
exec "$@"
