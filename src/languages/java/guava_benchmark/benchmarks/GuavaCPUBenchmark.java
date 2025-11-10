package benchmarks;

import benchmarks.workloads.GuavaWorkloads;
import benchmarks.utils.DataGenerator;

import java.util.*;
import java.util.concurrent.*;

public class GuavaCPUBenchmark {

    public static void main(String[] args) throws Exception {
        if (args.length < 3) {
            System.out.println("Usage: java GuavaCPUBenchmark <mode: collection|immutable|cache> <dataSize> <copies> [iterations]");
            return;
        }

        String mode = args[0].toLowerCase();
        int dataSize = Integer.parseInt(args[1]);
        int copies = Integer.parseInt(args[2]);
        int iterations = args.length >= 4 ? Integer.parseInt(args[3]) : 10;

        ExecutorService pool = Executors.newFixedThreadPool(copies);
        DataGenerator generator = new DataGenerator(42);

        // Prepare data for all modes
        List<Integer> dataset = generator.generateIntList(dataSize, Integer.MAX_VALUE);
        List<Integer> keys = generator.generateSequentialKeys(dataSize);

        Runnable task = () -> {
            switch (mode) {
                case "collection":
                    GuavaWorkloads.runCollectionTask(dataset, iterations);
                    break;
                case "immutable":
                    GuavaWorkloads.runImmutableTask(dataset, iterations);
                    break;
                case "cache":
                    GuavaWorkloads.runOptimizedFakeCacheTask(keys, iterations);
                    break;
                default:
                    throw new IllegalArgumentException("Unknown mode: " + mode);
            }
        };

        System.out.println("Running Guava CPU Benchmark in mode: " + mode);
        // Warm-up
        task.run();

        // Parallel execution
        long start = System.nanoTime();
        List<Future<?>> futures = new ArrayList<>();
        for (int i = 0; i < copies; i++) {
            futures.add(pool.submit(task));
        }

        for (Future<?> f : futures) f.get();
        pool.shutdown();

        long end = System.nanoTime();
        double totalTimeSec = (end - start) / 1_000_000_000.0;
        System.out.println("[RESULT] Total elapsed time: " + totalTimeSec + " s");
    }
}
