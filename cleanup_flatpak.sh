#!/usr/bin/env bash
# Remove AudioDeck Flatpak artefacts only.
#
# Never touches dist/, dist-installer/ or any Windows or macOS output: the
# three build paths stay independent.
#
# Author: Oliver Ernster

set -euo pipefail

APP_ID="uk.codecrafter.AudioDeck"
BUNDLE="audiodeck.flatpak"

if flatpak list --user 2>/dev/null | grep -q "${APP_ID}"; then
    flatpak uninstall --user -y "${APP_ID}"
else
    echo "  Not installed, skipping."
fi

rm -f "${BUNDLE}" "${APP_ID}.yml"
rm -rf .flatpak-build .flatpak-repo .flatpak-builder .flatpak-wheels packaging

echo "Flatpak artefacts removed."
