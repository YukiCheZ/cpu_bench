#!/usr/bin/env bash
set -e

CASSANDRA_VERSION="4.0.18"
CASSANDRA_DIR="./bin/apache-cassandra-$CASSANDRA_VERSION"
TAR_FILE="apache-cassandra-$CASSANDRA_VERSION-bin.tar.gz"

PRIMARY_URL="https://downloads.apache.org/cassandra/$CASSANDRA_VERSION/$TAR_FILE"
ARCHIVE_URL="https://archive.apache.org/dist/cassandra/$CASSANDRA_VERSION/$TAR_FILE"

mkdir -p ./bin

if [ -d "$CASSANDRA_DIR" ]; then
    echo "[INFO] Cassandra $CASSANDRA_VERSION already exists at $CASSANDRA_DIR, skipping download."
else
    echo "[INFO] Trying to download Cassandra $CASSANDRA_VERSION from primary URL..."
    if curl --output /dev/null --silent --head --fail "$PRIMARY_URL"; then
        DOWNLOAD_URL="$PRIMARY_URL"
    else
        echo "[WARN] Primary URL not found, switching to archive mirror..."
        DOWNLOAD_URL="$ARCHIVE_URL"
    fi

    echo "[INFO] Downloading from $DOWNLOAD_URL"
    curl -L -o "./bin/$TAR_FILE" "$DOWNLOAD_URL"

    echo "[INFO] Extracting Cassandra..."
    tar -xzf "./bin/$TAR_FILE" -C ./bin

    echo "[INFO] Cleaning up..."
    rm "./bin/$TAR_FILE"

    echo "[INFO] Cassandra setup completed at $CASSANDRA_DIR."
fi
