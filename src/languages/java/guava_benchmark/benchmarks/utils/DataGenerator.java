package benchmarks.utils;

import com.google.common.hash.Hashing;
import java.util.*;
import java.util.concurrent.ThreadLocalRandom;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

/**
 * DataGenerator provides various data generation utilities for the benchmarks.
 * It tries to reuse primitive arrays to reduce temporary object allocations.
 */
public class DataGenerator {
    private final int seed;

    public DataGenerator(int seed) {
        this.seed = seed;
    }

    // Random integer list (one-shot generation, can be used for immutable snapshots)
    public List<Integer> generateIntList(int size, int bound) {
        ThreadLocalRandom rng = ThreadLocalRandom.current();
        return rng.ints(size, 0, bound)
                  .boxed()
                  .collect(Collectors.toList());
    }

    // Sequential keys [0..size-1]
    public List<Integer> generateSequentialKeys(int size) {
        return IntStream.range(0, size).boxed().collect(Collectors.toList());
    }

    // Generate a primitive int array to avoid boxing overhead in hot loops
    public int[] generateIntArray(int size, int bound) {
        ThreadLocalRandom rng = ThreadLocalRandom.current();
        int[] arr = new int[size];
        for (int i = 0; i < size; i++) arr[i] = rng.nextInt(bound);
        return arr;
    }

    // Event record structure
    public static final class Event {
        public final int userId;
        public final int value;
        public final long timestamp;
        public final String category;
        public Event(int userId, int value, long timestamp, String category) {
            this.userId = userId;
            this.value = value;
            this.timestamp = timestamp;
            this.category = category;
        }
        public int hash() {
            return Hashing.murmur3_128().hashInt(userId * 31 + value).asInt();
        }
    }

    // Generate an event array (limit category count to create aggregation hotspots)
    public Event[] generateEvents(int size, int categoryCount) {
        ThreadLocalRandom rng = ThreadLocalRandom.current();
        Event[] events = new Event[size];
        for (int i = 0; i < size; i++) {
            int user = rng.nextInt(size / 10 + 1); // 有重复，模拟活跃用户
            int val = rng.nextInt(1000);
            long ts = System.currentTimeMillis() - rng.nextInt(1_000_000);
            String cat = "C" + rng.nextInt(categoryCount);
            events[i] = new Event(user, val, ts, cat);
        }
        return events;
    }

    // Directed graph edges: returns adjacency map (from -> set of to) to avoid duplicating large object graphs
    public Map<Integer, Set<Integer>> generateDirectedEdges(int nodes, int avgOutDegree) {
        ThreadLocalRandom rng = ThreadLocalRandom.current();
        Map<Integer, Set<Integer>> adj = new HashMap<>(nodes);
        for (int i = 0; i < nodes; i++) {
            int out = Math.max(1, (int) Math.round(rng.nextGaussian() * avgOutDegree/3.0 + avgOutDegree));
            Set<Integer> targets = new HashSet<>();
            for (int k = 0; k < out; k++) {
                int t = rng.nextInt(nodes);
                if (t != i) targets.add(t);
            }
            adj.put(i, targets);
        }
        return adj;
    }
}
