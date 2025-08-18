package benchmarks.workloads;

import com.google.common.collect.*;
import com.google.common.hash.Hashing;

import java.util.*;
import java.util.concurrent.ThreadLocalRandom;
import java.util.stream.*;

public class GuavaWorkloads {

    // Mode 1: Collection operations + sorting + hashing
    public static void runCollectionTask(List<Integer> data, int iterations) {
        for (int iter = 0; iter < iterations; iter++) {
            // Filter even numbers
            List<Integer> filtered = Lists.newArrayList(
                    Iterables.filter(data, x -> x % 2 == 0)
            );

            // Hash and map to strings
            List<String> mapped = Lists.transform(filtered, x -> Hashing.sha256()
                    .hashInt(x).toString());

            // Sort
            Ordering<String> ordering = Ordering.natural();
            List<String> sorted = ordering.sortedCopy(mapped);

            // Count frequencies
            Map<String, Integer> freq = new HashMap<>();
            for (String s : mapped) {
                freq.merge(s, 1, Integer::sum);
            }

            // Top 10
            List<Map.Entry<String, Integer>> top10 = freq.entrySet()
                    .stream()
                    .sorted((e1, e2) -> e2.getValue() - e1.getValue())
                    .limit(10)
                    .collect(Collectors.toList());
        }
    }

    // Mode 2: Immutable collections + BiMap inversion
    public static void runImmutableTask(List<Integer> bigList, int iterations) {
        ImmutableList<Integer> immutableList = ImmutableList.copyOf(bigList);

        ImmutableBiMap<Integer, String> biMap = ImmutableBiMap.copyOf(
                Maps.toMap(immutableList, String::valueOf)
        );

        for (int iter = 0; iter < iterations; iter++) {
            ImmutableBiMap<String, Integer> inverse = biMap.inverse();

            // Random lookups
            for (int i = 0; i < 1000; i++) {
                int idx = ThreadLocalRandom.current().nextInt(bigList.size());
                inverse.get(String.valueOf(bigList.get(idx)));
            }
        }
    }

    // Mode 3: Cache-like workload
    public static void runOptimizedFakeCacheTask(List<Integer> keys, int iterations) {
        Map<Integer, String> map = new HashMap<>();

        // Initialize cache
        for (Integer key : keys) {
            map.put(key, Hashing.sha256().hashInt(key).toString());
        }

        long dummy = 0;

        for (int iter = 0; iter < iterations; iter++) {
            for (int i = 0; i < keys.size(); i++) {
                int key = ThreadLocalRandom.current().nextInt(keys.size() * 2); // 50% miss
                String val = map.getOrDefault(key, Hashing.sha256().hashInt(key).toString());
                dummy += Hashing.sha256().hashUnencodedChars(val).asInt();
            }
        }

        // Prevent JVM optimization
        if (dummy == 42) System.out.println(dummy);
    }
}
