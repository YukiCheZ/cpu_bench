#!/bin/bash
# setup.sh - Download and extract Kafka if not already installed

set -e  # Exit immediately if a command exits with a non-zero status

KAFKA_VERSION="3.8.0"
SCALA_VERSION="2.13"
KAFKA_DIR="./bin/kafka_${SCALA_VERSION}-${KAFKA_VERSION}"
KAFKA_TGZ="kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz"

PRIMARY_URL="https://downloads.apache.org/kafka/${KAFKA_VERSION}/${KAFKA_TGZ}"
ARCHIVE_URL="https://archive.apache.org/dist/kafka/${KAFKA_VERSION}/${KAFKA_TGZ}"

# Create bin directory if it doesn't exist
mkdir -p ./bin

# Check if Kafka already exists
if [ -d "$KAFKA_DIR" ]; then
    echo "[INFO] Kafka already exists at $KAFKA_DIR, skipping download."
    exit 0
fi

# Determine available download URL
echo "[INFO] Checking primary Kafka URL..."
if curl --output /dev/null --silent --head --fail "$PRIMARY_URL"; then
    DOWNLOAD_URL="$PRIMARY_URL"
else
    echo "[WARN] Primary URL not available, switching to archive mirror..."
    DOWNLOAD_URL="$ARCHIVE_URL"
fi

echo "[INFO] Downloading Kafka ${KAFKA_VERSION} from: $DOWNLOAD_URL"
curl -L -o "$KAFKA_TGZ" "$DOWNLOAD_URL"

echo "[INFO] Extracting Kafka..."
tar -xzf "$KAFKA_TGZ" -C ./bin

echo "[INFO] Cleaning up..."
rm -f "$KAFKA_TGZ"

echo "[INFO] Kafka setup completed successfully at $KAFKA_DIR"
