# Makefile for LAPACK CPU Benchmark

# Default settings
CC ?= gcc
OPT ?= -O3
CFLAGS = -Wall $(OPT)
LDFLAGS = -llapacke -llapack -lblas -lm

SRC = lapack_benchmark.c
BIN_DIR = bin
TARGET = $(BIN_DIR)/lapack_benchmark
STAMP = $(BIN_DIR)/build_stamp

.PHONY: all clean run

all: $(TARGET)

# Create bin directory if needed
$(BIN_DIR):
	mkdir -p $(BIN_DIR)

# Generate target, rebuild if SRC or CC/OPT changed
$(TARGET): $(SRC) $(STAMP) | $(BIN_DIR)
	@echo "Building $(TARGET) with $(CC) $(OPT)..."
	$(CC) $(CFLAGS) -o $@ $(SRC) $(LDFLAGS)
	@echo "CC=$(CC)" > $(STAMP)
	@echo "OPT=$(OPT)" >> $(STAMP)

# Stamp file depends on nothing, but triggers rebuild if CC/OPT changed
$(STAMP):
	@mkdir -p $(BIN_DIR)
	@echo "CC=$(CC)" > $@
	@echo "OPT=$(OPT)" >> $@

clean:
	rm -rf $(BIN_DIR)
