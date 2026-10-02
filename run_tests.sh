#!/bin/bash
# Lunara test runner.
#   ./run_tests.sh unit                 Python logic tests, then Monkey C tests on the device matrix
#   ./run_tests.sh unit fenix7          Monkey C tests on one device, after the Python suite
#   ./run_tests.sh unit --skip-device   Python suite and unit_report.html only
#   ./run_tests.sh ui                   Visual report against baselines
#   ./run_tests.sh ui --full            Every language on every round device
#   ./run_tests.sh ui --update-baselines
#   ./run_tests.sh ui --device fenix7
#   ./run_tests.sh sim fenix7           Compile and open the simulator
#   ./run_tests.sh all                  Python, visual compare, memory, then device unit tests
set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

SDK_DIR="$HOME/Library/Application Support/Garmin/ConnectIQ/Sdks"
SDK_PATH="$(ls -td "$SDK_DIR"/connectiq-sdk-mac-* 2>/dev/null | head -n 1)"
KEY_PATH="$ROOT/developer_key.der"
OUTPUT_PRG="$ROOT/bin/LunaraTest.prg"

DEVICES=("fenix7s" "fenix7" "fr255" "enduro3" "venu2s" "epix2pro42mm" "venu2" "venu3" "fenix9pro51mm")

MODE="${1:-unit}"

if [ -z "${SDK_PATH}" ]; then
    echo "No Connect IQ SDK found in $SDK_DIR"
    exit 1
fi

if [ ! -f "$KEY_PATH" ]; then
    echo "Generating a local developer key..."
    openssl genrsa -out "$ROOT/developer_key.pem" 4096
    openssl pkcs8 -topk8 -inform PEM -outform DER -in "$ROOT/developer_key.pem" -out "$KEY_PATH" -nocrypt
fi

ensure_simulator() {
    if pgrep -f "connectiq" >/dev/null 2>&1; then
        return 0
    fi
    echo "Starting Connect IQ Simulator..."
    "$SDK_PATH/bin/connectiq" >/tmp/lunara-connectiq.log 2>&1 &
    sleep 8
}

run_python_units() {
    echo "========================================================"
    echo "LUNARA PYTHON UNIT TESTS"
    echo "========================================================"
    python3 "$ROOT/run_unit_tests.py"
}

run_device_units() {
    local only="${1:-}"
    local targets=()
    if [ -n "$only" ]; then
        targets=("$only")
    else
        targets=("${DEVICES[@]}")
    fi
    mkdir -p "$ROOT/bin" "$ROOT/test_output"
    local log="$ROOT/test_output/device_unit_log.txt"
    : > "$log"
    local failures=0
    ensure_simulator
    for dev in "${targets[@]}"; do
        echo ""
        echo "--------------------------------------------------------"
        echo "Device unit tests: $dev"
        echo "--------------------------------------------------------"
        if "$SDK_PATH/bin/monkeyc" -f "$ROOT/monkey.jungle" -o "$OUTPUT_PRG" -d "$dev" -y "$KEY_PATH" -t -w; then
            echo "Compile succeeded for $dev"
            local test_out
            test_out=$("$SDK_PATH/bin/monkeydo" "$OUTPUT_PRG" "$dev" -t 2>&1) || true
            echo "$test_out"
            printf '\n===== %s =====\n%s\n' "$dev" "$test_out" >> "$log"
            if echo "$test_out" | grep -q "PASSED ("; then
                echo "Assertions passed for $dev"
            else
                echo "Assertions failed for $dev"
                failures=$((failures + 1))
            fi
        else
            echo "Compile failed for $dev"
            echo "COMPILE FAILED $dev" >> "$log"
            failures=$((failures + 1))
        fi
    done
    echo ""
    echo "Device suites with issues: $failures"
    echo "Log → $log"
    return "$failures"
}

run_visual() {
    shift
    echo "========================================================"
    echo "LUNARA VISUAL REGRESSION"
    echo "========================================================"
    python3 "$ROOT/run_ui_tests.py" "$@"
}

run_sim() {
    local device="${1:-fenix7}"
    mkdir -p "$ROOT/bin"
    echo "Compiling Lunara for $device..."
    "$SDK_PATH/bin/monkeyc" -f "$ROOT/monkey.jungle" -o "$ROOT/bin/Lunara.prg" -d "$device" -y "$KEY_PATH" -w
    ensure_simulator
    echo "Launching $device..."
    "$SDK_PATH/bin/monkeydo" "$ROOT/bin/Lunara.prg" "$device"
}

case "$MODE" in
    --help|-h|help)
        sed -n '2,12p' "$0"
        ;;
    unit)
        run_python_units || exit 1
        if [ "${2:-}" = "--skip-device" ]; then
            exit 0
        fi
        run_device_units "${2:-}"
        ;;
    ui)
        run_visual "$@"
        ;;
    sim)
        run_sim "${2:-fenix7}"
        ;;
    all)
        run_python_units || exit 1
        if [ ! -d "$ROOT/test_output/baselines" ] || [ -z "$(ls -A "$ROOT/test_output/baselines" 2>/dev/null)" ]; then
            python3 "$ROOT/run_ui_tests.py" --update-baselines || exit 1
        fi
        python3 "$ROOT/run_ui_tests.py" || exit 1
        "$ROOT/profile_memory.sh" || exit 1
        run_device_units ""
        ;;
    *)
        echo "Unknown mode '$MODE'. Run ./run_tests.sh help"
        exit 1
        ;;
esac
