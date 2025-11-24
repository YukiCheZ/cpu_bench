package benchmarks.workloads;

import benchmarks.framework.BenchmarkContext;
import benchmarks.framework.Workload;
import com.google.common.hash.BloomFilter;
import com.google.common.hash.Funnels;
import com.google.common.hash.Hashing;

import java.util.concurrent.ThreadLocalRandom;

/**
 * BloomFilter workload: simulates ID stream inserts and queries with false positives;
 * includes chained hashing operations to generate CPU load.
 */
public class BloomFilterWorkload implements Workload {
    private BloomFilter<Integer> filter;
    private int bound;

    @Override
    public void setup(BenchmarkContext ctx) {
        bound = ctx.dataSize * 10; // Expand query space
        int expectedInsertions = ctx.dataSize;
        filter = BloomFilter.create(Funnels.integerFunnel(), expectedInsertions, 0.01);
        // Warm-up: insert half of expected entries
        ThreadLocalRandom rng = ctx.rng();
        for (int i = 0; i < expectedInsertions / 2; i++) filter.put(rng.nextInt(bound));
    }

    @Override
    public void runIteration(BenchmarkContext ctx, int iteration) {
        ThreadLocalRandom rng = ctx.rng();
        long sink = 0;
        for (int i = 0; i < ctx.dataSize; i++) {
            int v = rng.nextInt(bound);
            boolean present = filter.mightContain(v);
            if (!present) filter.put(v); // Dynamic growth
            // Additional hash chain to increase CPU cost
            int h = Hashing.sha256().hashInt(v).asInt();
            h = Hashing.murmur3_128().hashInt(h).asInt();
            sink += present ? h : ~h;
        }
        if (sink == 7L) System.out.println("avoid opt");
    }

    @Override
    public void teardown(BenchmarkContext ctx) {
        filter = null;
    }
}
