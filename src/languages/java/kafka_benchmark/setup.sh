#!/bin/bash
# setup.sh - Download and extract Kafka if not already installed

KAFKA_VERSION="3.8.0"
SCALA_VERSION="2.13"
KAFKA_DIR="./bin/kafka_${SCALA_VERSION}-${KAFKA_VERSION}"
KAFKA_TGZ="kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz"
KAFKA_URL="https://downloads.apache.org/kafka/${KAFKA_VERSION}/${KAFKA_TGZ}"

# Create bin directory if not exists
mkdir -p ./bin

# Check if Kafka already exists
if [ -d "$KAFKA_DIR" ]; then
    echo "[INFO] Kafka already exists at $KAFKA_DIR"
    exit 0
fi

echo "[INFO] Downloading Kafka ${KAFKA_VERSION}..."
curl -O "$KAFKA_URL"
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to download Kafka from $KAFKA_URL"
    exit 1
fi

echo "[INFO] Extracting Kafka..."
tar -xzf "$KAFKA_TGZ" -C ./bin
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to extract $KAFKA_TGZ"
    exit 1
fi

echo "[INFO] Cleaning up..."
rm -f "$KAFKA_TGZ"

echo "[INFO] Kafka setup completed at $KAFKA_DIR"
