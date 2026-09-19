#!/bin/bash
# Shared container entrypoint. SSH supports disabled, key-only, and password modes.
# Reads SSH_MODE (default: disabled), USERNAME (default: luciole), and the optional
# ROOT_PASSWORD_FILE path used only by password mode.
#
# The image's USER directive keeps PID 1 non-root. Passwordless sudo is used
# only for SSH runtime setup explicitly selected by the image manifest.
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
        sudo -n /usr/sbin/sshd \
            -o PasswordAuthentication=no \
            -o KbdInteractiveAuthentication=no \
            -o PermitRootLogin=no
        ;;
    password)
        # A mounted password file avoids exposing credentials in image layers or arguments.
        if [ -n "${ROOT_PASSWORD_FILE:-}" ]; then
            if ! sudo -n test -s "${ROOT_PASSWORD_FILE}"; then
                echo "[entrypoint] ROOT_PASSWORD_FILE must reference a non-empty file" >&2
                exit 64
            fi
            sudo -n /bin/bash -c '
                password=$(cat "$1")
                printf "root:%s\n" "${password}" | chpasswd
            ' _ "${ROOT_PASSWORD_FILE}"
        fi
        sudo -n mkdir -p /run/sshd
        sudo -n ssh-keygen -A >/dev/null
        sudo -n /usr/sbin/sshd \
            -o PasswordAuthentication=yes \
            -o KbdInteractiveAuthentication=no \
            -o PermitEmptyPasswords=no \
            -o PermitRootLogin=yes
        ;;
    *)
        echo "[entrypoint] unsupported SSH_MODE '${SSH_MODE_VAL}'" >&2
        exit 64
        ;;
esac

# Preserve the user command as PID 1 so signals propagate directly.
exec "$@"
