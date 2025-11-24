package benchmarks.framework;

import benchmarks.utils.DataGenerator;
import java.util.concurrent.ThreadLocalRandom;

public class BenchmarkContext {
    public final int dataSize;
    public final int iterations;
    public final int threads;
    public final DataGenerator generator;

    public BenchmarkContext(int dataSize, int iterations, int threads, DataGenerator generator) {
        this.dataSize = dataSize;
        this.iterations = iterations;
        this.threads = threads;
        this.generator = generator;
    }

    public ThreadLocalRandom rng() { return ThreadLocalRandom.current(); }
}
