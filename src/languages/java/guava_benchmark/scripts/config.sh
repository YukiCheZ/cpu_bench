# Default config for benchmark

# 工作负载模式: collection | immutable | cache
DEFAULT_MODE="collection"

# 不同模式下的数据规模
COLLECTION_DATASIZE=2000000
IMMUTABLE_DATASIZE=5000000
CACHE_DATASIZE=1000000

# 副本数 (即并行线程数)
DEFAULT_COPIES=1

# 每个副本迭代次数
DEFAULT_ITERATIONS=10