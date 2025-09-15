#!/usr/bin/env bash
set -e

CASSANDRA_VERSION="4.0.18"
CASSANDRA_DIR="./bin/apache-cassandra-$CASSANDRA_VERSION"
TAR_FILE="apache-cassandra-$CASSANDRA_VERSION-bin.tar.gz"
DOWNLOAD_URL="https://downloads.apache.org/cassandra/$CASSANDRA_VERSION/$TAR_FILE"

# Create bin directory if it doesn't exist
mkdir -p ./bin

if [ -d "$CASSANDRA_DIR" ]; then
    echo "[INFO] Cassandra $CASSANDRA_VERSION already exists at $CASSANDRA_DIR, skipping download."
else
    echo "[INFO] Downloading Cassandra $CASSANDRA_VERSION..."
    curl -L -o "./bin/$TAR_FILE" "$DOWNLOAD_URL"

    echo "[INFO] Extracting Cassandra..."
    tar -xzf "./bin/$TAR_FILE" -C ./bin

    echo "[INFO] Cleaning up..."
    rm "./bin/$TAR_FILE"

    echo "[INFO] Cassandra setup completed at $CASSANDRA_DIR."
fi
