package benchmarks.utils;

import java.util.*;
import java.util.concurrent.ThreadLocalRandom;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

public class DataGenerator {
    private final int seed;

    public DataGenerator(int seed) {
        this.seed = seed;
    }

    // Generate a list of random integers
    public List<Integer> generateIntList(int size, int bound) {
        ThreadLocalRandom rng = ThreadLocalRandom.current();
        return rng.ints(size, 0, bound)
                  .boxed()
                  .collect(Collectors.toList());
    }

    // Generate a list of sequential keys [0..size-1]
    public List<Integer> generateSequentialKeys(int size) {
        return IntStream.range(0, size).boxed().collect(Collectors.toList());
    }
}
