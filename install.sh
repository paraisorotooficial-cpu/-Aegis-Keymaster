#!/usr/bin/env bash
# Aegis Keymaster — user installer (~/.local). No root required.
# Usage:
#   ./install.sh              install (or update) for the current user
#   ./install.sh --uninstall  remove the user installation
set -euo pipefail

PREFIX="${HOME}/.local"
APP_NAME="aegis-keymaster"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

install() {
    echo "==> Installing ${APP_NAME} to ${PREFIX}"
    python3 -m pip install --user --no-deps "${REPO_DIR}"
    python3 -m pip install --user -r "${REPO_DIR}/requirements.txt"
    python3 -m pip install --user --no-deps "${REPO_DIR}" >/dev/null 2>&1 || true

    # Application icons (hicolor theme)
    for size_dir in "${REPO_DIR}"/assets/icons/*/; do
        size="$(basename "${size_dir}")"
        target="${PREFIX}/share/icons/hicolor/${size}x${size}/apps"
        mkdir -p "${target}"
        cp "${size_dir}/${APP_NAME}.png" "${target}/"
    done

    # Desktop entry
    mkdir -p "${PREFIX}/share/applications"
    sed "s|^Icon=.*|Icon=${APP_NAME}|" "${REPO_DIR}/packaging/${APP_NAME}.desktop" \
        > "${PREFIX}/share/applications/${APP_NAME}.desktop"

    # Fonts and other assets stay inside the package; nothing else to copy.
    command -v update-desktop-database >/dev/null 2>&1 && \
        update-desktop-database "${PREFIX}/share/applications" || true

    echo "==> Done. Start it with: ${PREFIX}/bin/${APP_NAME}"
    echo "    (make sure ${PREFIX}/bin is in your PATH)"
}

uninstall() {
    echo "==> Removing ${APP_NAME} from ${PREFIX}"
    python3 -m pip uninstall -y "${APP_NAME}" || true
    rm -f "${PREFIX}/share/applications/${APP_NAME}.desktop"
    for size_dir in "${REPO_DIR}"/assets/icons/*/; do
        size="$(basename "${size_dir}")"
        rm -f "${PREFIX}/share/icons/hicolor/${size}x${size}/apps/${APP_NAME}.png"
    done
    command -v update-desktop-database >/dev/null 2>&1 && \
        update-desktop-database "${PREFIX}/share/applications" || true
    echo "==> User data in ~/.local/share/aegis-keymaster was kept."
    echo "    Remove it manually if you no longer need your progress."
}

case "${1:-}" in
    --uninstall) uninstall ;;
    "") install ;;
    *) echo "Unknown option: $1"; echo "Usage: $0 [--uninstall]"; exit 2 ;;
esac
