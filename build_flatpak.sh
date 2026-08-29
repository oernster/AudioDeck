#!/usr/bin/env bash
# Build the AudioDeck Flatpak bundle (Linux).
#
# Offline-wheels variant: PySide6 wheels are downloaded on the host first,
# then installed inside the sandbox with --no-index, so the build itself
# needs no network. The runtime sandbox gets the PulseAudio socket (device
# control via pactl) and network (the GitHub update check only).
#
# Author: Oliver Ernster

set -euo pipefail

APP_ID="uk.codecrafter.AudioDeck"
APP_NAME="AudioDeck"
APP_CMD="audiodeck"
APP_SUMMARY="Audio device switcher with Stream Deck integration"
APP_VERSION="$(tr -d '[:space:]' < VERSION)"
# AppStream requires a date on every release. The day VERSION last changed is
# the day this version came into being; an uncommitted bump dates as today.
APP_RELEASE_DATE="$(git log -1 --format=%cs -- VERSION 2>/dev/null)"
APP_RELEASE_DATE="${APP_RELEASE_DATE:-$(date +%F)}"
RUNTIME="org.freedesktop.Platform"
SDK="org.freedesktop.Sdk"
RUNTIME_VERSION="25.08"
PYTHON_DIR="python3.13"
BUNDLE="${APP_CMD}.flatpak"
BUILD_DIR=".flatpak-build"
REPO_DIR=".flatpak-repo"
WHEELS_DIR=".flatpak-wheels"
MANIFEST="${APP_ID}.yml"
PACKAGING_DIR="packaging"
ICON_SIZES="16 24 32 48 64 96 128 256 512"

section() {
    printf '\n%s== %s ==%s\n' "$(tput setaf 6 2>/dev/null || true)" "$1" "$(tput sgr0 2>/dev/null || true)"
}

install_if_missing() {
    local tool="$1"
    command -v "${tool}" >/dev/null 2>&1 && return 0
    section "Installing ${tool}"
    if command -v apt-get >/dev/null 2>&1; then sudo apt-get install -y "${tool}"
    elif command -v dnf >/dev/null 2>&1; then sudo dnf install -y "${tool}"
    elif command -v pacman >/dev/null 2>&1; then sudo pacman -S --noconfirm "${tool}"
    elif command -v zypper >/dev/null 2>&1; then sudo zypper install -y "${tool}"
    else echo "Install ${tool} manually and re-run." >&2; exit 1
    fi
}

section "Tooling"
install_if_missing flatpak
install_if_missing flatpak-builder
flatpak remote-add --if-not-exists --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --user --noninteractive flathub "${RUNTIME}//${RUNTIME_VERSION}" "${SDK}//${RUNTIME_VERSION}"

section "Downloading wheels on the host"
rm -rf "${WHEELS_DIR}"
python3 -m pip download --only-binary :all: --python-version 3.13 --implementation cp \
    --platform manylinux_2_34_x86_64 -d "${WHEELS_DIR}" -r requirements-flatpak.txt

section "Writing packaging files"
rm -rf "${PACKAGING_DIR}"
mkdir -p "${PACKAGING_DIR}"

cat > "${PACKAGING_DIR}/${APP_CMD}-launcher" <<'LAUNCHER'
#!/bin/sh
export PYTHONPATH="/app/lib/PYTHON_DIR_TOKEN/site-packages:/app/share/APP_CMD_TOKEN${PYTHONPATH:+:$PYTHONPATH}"
export QT_PLUGIN_PATH="/app/lib/PYTHON_DIR_TOKEN/site-packages/PySide6/Qt/plugins"
export QT_QPA_PLATFORM_PLUGIN_PATH="/app/lib/PYTHON_DIR_TOKEN/site-packages/PySide6/Qt/plugins/platforms"
if [ -n "$WAYLAND_DISPLAY" ] && [ -z "$FORCE_X11" ]; then export QT_QPA_PLATFORM=wayland
elif [ -n "$DISPLAY" ]; then export QT_QPA_PLATFORM=xcb
else export QT_QPA_PLATFORM=xcb; fi
exec python3 /app/share/APP_CMD_TOKEN/src/main.py "$@"
LAUNCHER
sed -i "s/PYTHON_DIR_TOKEN/${PYTHON_DIR}/g; s/APP_CMD_TOKEN/${APP_CMD}/g" "${PACKAGING_DIR}/${APP_CMD}-launcher"

cat > "${PACKAGING_DIR}/${APP_ID}.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=${APP_NAME}
Comment=${APP_SUMMARY}
Exec=${APP_CMD}
Icon=${APP_ID}
Categories=AudioVideo;Audio;Settings;
Terminal=false
DESKTOP

cat > "${PACKAGING_DIR}/${APP_ID}.metainfo.xml" <<METAINFO
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>${APP_ID}</id>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>LGPL-3.0-or-later</project_license>
  <name>${APP_NAME}</name>
  <summary>${APP_SUMMARY}</summary>
  <description>
    <p>Switch default audio input and output devices with one click or one
    Stream Deck button, using saved device profiles.</p>
  </description>
  <launchable type="desktop-id">${APP_ID}.desktop</launchable>
  <releases>
    <release version="${APP_VERSION}" date="${APP_RELEASE_DATE}"/>
  </releases>
</component>
METAINFO

section "Writing manifest"
cat > "${MANIFEST}" <<MANIFEST_EOF
app-id: ${APP_ID}
runtime: ${RUNTIME}
runtime-version: "${RUNTIME_VERSION}"
sdk: ${SDK}
command: ${APP_CMD}
build-options:
  strip: true
  no-debuginfo: true
finish-args:
  - --share=ipc
  - --socket=fallback-x11
  - --socket=wayland
  - --device=dri
  - --socket=pulseaudio
  # PipeWire strips the metadata permission from every sandboxed client, so
  # from inside the sandbox devices can be listed but never switched, whatever
  # sockets are granted. Talking to the Flatpak service lets the one metadata
  # write that changes the default device run in the host session instead.
  - --talk-name=org.freedesktop.Flatpak
  - --share=network
modules:
  - name: python-deps
    buildsystem: simple
    build-commands:
      - python3 -m ensurepip --upgrade
      - pip3 install --no-cache-dir --no-index --find-links wheels --prefix=/app -r requirements-flatpak.txt
    sources:
      - type: dir
        path: ${WHEELS_DIR}
        dest: wheels
      - type: file
        path: requirements-flatpak.txt
  - name: ${APP_CMD}
    buildsystem: simple
    build-commands:
      - install -d /app/share/${APP_CMD}
      - install -d /app/share/${APP_CMD}/assets
      - cp -r assets/icons /app/share/${APP_CMD}/assets/
      - cp -r src VERSION LICENSE LICENSE-GPL-3.0.txt LICENSE-LGPL-3.0.txt DOCUMENTATION.md /app/share/${APP_CMD}/
      - install -Dm755 ${PACKAGING_DIR}/${APP_CMD}-launcher /app/bin/${APP_CMD}
      - install -Dm644 ${PACKAGING_DIR}/${APP_ID}.desktop /app/share/applications/${APP_ID}.desktop
      - install -Dm644 ${PACKAGING_DIR}/${APP_ID}.metainfo.xml /app/share/metainfo/${APP_ID}.metainfo.xml
$(for size in ${ICON_SIZES}; do
    printf '      - install -Dm644 assets/icons/audiodeck_icon_%s.png /app/share/icons/hicolor/%sx%s/apps/%s.png\n' "${size}" "${size}" "${size}" "${APP_ID}"
done)
    sources:
      - type: dir
        path: .
MANIFEST_EOF

section "Building"
flatpak-builder --user --install-deps-from=flathub --force-clean \
    --repo="${REPO_DIR}" "${BUILD_DIR}" "${MANIFEST}"

section "Bundling"
flatpak build-bundle --runtime-repo=https://flathub.org/repo/flathub.flatpakrepo \
    "${REPO_DIR}" "${BUNDLE}" "${APP_ID}"

section "Installing"
flatpak install --user --reinstall --noninteractive "./${BUNDLE}"

section "Done"
echo "Installed ${APP_ID} and wrote ${BUNDLE} (attach this to the release)."
echo "Run with: flatpak run ${APP_ID}"
