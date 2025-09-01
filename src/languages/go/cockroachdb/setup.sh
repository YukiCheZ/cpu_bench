set -e

COCKROACH_VERSION="v23.1.30"

INSTALL_DIR="./bin"

if [ -n "$COCKROACH_BIN" ]; then
    if [ ! -x "$COCKROACH_BIN" ]; then
        echo "Error: COCKROACH_BIN is set but not executable: $COCKROACH_BIN"
        return 1 2>/dev/null || exit 1
    fi
    echo "Using user-provided CockroachDB binary: $COCKROACH_BIN"
    return 0 2>/dev/null || exit 0
fi

ARCH=$(uname -m)
case "$ARCH" in
    x86_64) COCKROACH_URL="https://binaries.cockroachdb.com/cockroach-${COCKROACH_VERSION}.linux-amd64.tgz" ;;
    aarch64) COCKROACH_URL="https://binaries.cockroachdb.com/cockroach-${COCKROACH_VERSION}.linux-arm64.tgz" ;;
    *)
        echo "Unsupported architecture: $ARCH"
        return 1 2>/dev/null || exit 1
        ;;
esac

mkdir -p "$INSTALL_DIR"

if [ -x "$INSTALL_DIR/cockroach" ]; then
    echo "CockroachDB binary already exists at $INSTALL_DIR/cockroach"
    echo "You can run your benchmark now."
    export COCKROACH_BIN="$INSTALL_DIR/cockroach"
    return 0 2>/dev/null || true
fi

echo "Downloading CockroachDB ${COCKROACH_VERSION} for $ARCH..."
curl -L "$COCKROACH_URL" -o "cockroach.tgz"

echo "Extracting..."
tar -xzf cockroach.tgz --strip-components=1 -C "$INSTALL_DIR"
rm cockroach.tgz

export COCKROACH_BIN="$INSTALL_DIR/cockroach"
echo "CockroachDB installed at $COCKROACH_BIN"
echo "COCKROACH_BIN has been set for this shell session."
