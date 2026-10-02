#!/bin/bash
# Compile Lunara. Pass a device id, for example: ./build.sh fenix7
set -euo pipefail

DEVICE="${1:-fenix7}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
SDK_DIR="$HOME/Library/Application Support/Garmin/ConnectIQ/Sdks"
SDK_PATH="$(ls -td "$SDK_DIR"/connectiq-sdk-mac-* 2>/dev/null | head -n 1)"

if [ -z "${SDK_PATH}" ]; then
    echo "No Connect IQ SDK found in $SDK_DIR"
    exit 1
fi

if [ ! -f "$ROOT/developer_key.der" ]; then
    echo "Generating a local developer key..."
    openssl genrsa -out "$ROOT/developer_key.pem" 4096
    openssl pkcs8 -topk8 -inform PEM -outform DER -in "$ROOT/developer_key.pem" -out "$ROOT/developer_key.der" -nocrypt
fi

mkdir -p "$ROOT/bin"
echo "Using $SDK_PATH"
echo "Building Lunara for $DEVICE..."
"$SDK_PATH/bin/monkeyc" \
    -d "$DEVICE" \
    -f "$ROOT/monkey.jungle" \
    -o "$ROOT/bin/Lunara.prg" \
    -y "$ROOT/developer_key.der" \
    -w
echo "Built $ROOT/bin/Lunara.prg"
