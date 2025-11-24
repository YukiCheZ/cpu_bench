package benchmarks.workloads;

import benchmarks.framework.BenchmarkContext;
import benchmarks.framework.Workload;
import com.google.common.hash.Hashing;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ThreadLocalRandom;

/**
 * Custom concurrent cache simulation (replaces LoadingCache to avoid extra dependency):
 * - 20% hot keys, 80% cold keys
 * - Grows gradually and triggers size-based random eviction
 */
public class LoadingCacheWorkload implements Workload {
    private Map<Integer, String> cache;
    private int hotKeyRange;
    private int coldKeyRange;
    private int maxSize;

    @Override
    public void setup(BenchmarkContext ctx) {
        hotKeyRange = Math.max(10, ctx.dataSize / 100);
        coldKeyRange = ctx.dataSize * 10;
        maxSize = hotKeyRange * 30;
        cache = new ConcurrentHashMap<>(hotKeyRange * 4);
        ThreadLocalRandom rng = ctx.rng();
        for (int i = 0; i < hotKeyRange; i++) {
            cache.put(i, computeValue(i));
        }
    }

    @Override
    public void runIteration(BenchmarkContext ctx, int iteration) {
        ThreadLocalRandom rng = ctx.rng();
        long sink = 0;
        for (int i = 0; i < ctx.dataSize; i++) {
            int key = rng.nextDouble() < 0.2 ? rng.nextInt(hotKeyRange) : hotKeyRange + rng.nextInt(coldKeyRange);
            String val = cache.get(key);
            if (val == null) {
                val = computeValue(key);
                cache.put(key, val);
                // Simple eviction: randomly remove a few entries when exceeding max size
                if (cache.size() > maxSize) {
                    int removeCount = Math.min(50, cache.size()/20);
                    int removed = 0;
                    for (Integer k : cache.keySet()) {
                        if (rng.nextDouble() < 0.3) {
                            cache.remove(k);
                            removed++;
                            if (removed >= removeCount) break;
                        }
                    }
                }
            }
            sink += val.hashCode();
        }
        if (sink == 123) System.out.println("avoid optimize");
    }

    private String computeValue(int key) {
        long acc = key;
        for (int i = 0; i < 50; i++) acc = Hashing.murmur3_128().hashLong(acc ^ (i * 31L + key)).asLong();
        return Long.toHexString(acc) + ':' + Integer.toHexString(key);
    }

    @Override
    public void teardown(BenchmarkContext ctx) {
        cache.clear();
        cache = null;
    }
}
