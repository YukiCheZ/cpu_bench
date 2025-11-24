package benchmarks;

import benchmarks.framework.BenchmarkContext;
import benchmarks.framework.Workload;
import benchmarks.utils.DataGenerator;
import benchmarks.workloads.*;

import java.util.*;
import java.util.concurrent.*;

/**
 * Unified Guava CPU benchmark runner.
 * Parameters:
 *   --workload event|graph|bloom|cache|immutable
 *   --dataSize N
 *   --iterations M  (iterations per thread)
 *   --threads T
 *   --warmupIterations W | --noWarmup
 */
public class BenchmarkRunner {
    private static final Map<String, Integer> DEFAULT_DATASIZE = new HashMap<>();
    private static final Map<String, Integer> DEFAULT_ITERATIONS = new HashMap<>();

    static {
        DEFAULT_DATASIZE.put("event", 200000);
        DEFAULT_DATASIZE.put("graph", 400000);
        DEFAULT_DATASIZE.put("bloom", 400000);
        DEFAULT_DATASIZE.put("cache", 100000);
        DEFAULT_DATASIZE.put("immutable", 400000);

        DEFAULT_ITERATIONS.put("event", 100000);
        DEFAULT_ITERATIONS.put("graph", 15000);
        DEFAULT_ITERATIONS.put("bloom", 2000);
        DEFAULT_ITERATIONS.put("cache", 1000);
        DEFAULT_ITERATIONS.put("immutable", 32000);
    }
    public static void main(String[] args) throws Exception {
        Map<String, String> argMap = parseArgs(args);
        if (argMap.containsKey("help") || argMap.isEmpty()) {
            usage();
            return;
        }
        String workloadName = argMap.getOrDefault("workload", "event").toLowerCase();
        int threads = Integer.parseInt(argMap.getOrDefault("threads", "1"));

        int dataSize = argMap.containsKey("dataSize")
                ? Integer.parseInt(argMap.get("dataSize"))
                : DEFAULT_DATASIZE.getOrDefault(workloadName, 200000);
        int iterations = argMap.containsKey("iterations")
                ? Integer.parseInt(argMap.get("iterations"))
                : DEFAULT_ITERATIONS.getOrDefault(workloadName, 100);

        // Warmup iteration logic: --warmupIterations overrides; default = min(5, max(1, iterations/500)); --noWarmup disables
        int warmupIterations;
        if (argMap.containsKey("noWarmup")) {
            warmupIterations = 0;
        } else if (argMap.containsKey("warmupIterations")) {
            warmupIterations = Integer.parseInt(argMap.get("warmupIterations"));
        } else {
            warmupIterations = Math.min(5, Math.max(1, iterations / 500));
        }

        Workload prototype = createWorkload(workloadName);
        if (prototype == null) {
            System.err.println("Unknown workload: " + workloadName);
            usage();
            return;
        }

        System.out.printf("[INFO] Workload=%s dataSize=%d iterations/thread=%d threads=%d%n", workloadName, dataSize, iterations, threads);

        BenchmarkContext baseCtx = new BenchmarkContext(dataSize, iterations, threads, new DataGenerator(42));

        // Create an isolated workload instance per thread to avoid shared mutable state
        List<Workload> workloads = new ArrayList<>(threads);
        for (int i = 0; i < threads; i++) {
            Workload w = createWorkload(workloadName);
            w.setup(baseCtx); 
            workloads.add(w);
        }

        ExecutorService pool = Executors.newFixedThreadPool(threads);
        List<Callable<Long>> calls = new ArrayList<>();
        for (int t = 0; t < threads; t++) {
            Workload w = workloads.get(t);
            calls.add(() -> runThread(w, baseCtx));
        }

        // Warmup (only first workload instance, reduced iteration count)
        if (warmupIterations > 0) {
            System.out.printf("[INFO] Warmup: %d iterations%n", warmupIterations);
            runThreadPartial(workloads.get(0), baseCtx, warmupIterations);
            System.out.println("[INFO] Warmup complete.");
        }

        System.out.println("[INFO] Starting benchmark...");
        long start = System.nanoTime();
        List<Future<Long>> futures = pool.invokeAll(calls);
        long totalOps = 0;
        for (Future<Long> f : futures) totalOps += f.get();
        long end = System.nanoTime();
        pool.shutdown();

        double sec = (end - start) / 1_000_000_000.0;
        System.out.printf("[RESULT] Total elapsed time: %.4f s%n", sec);

        for (Workload w : workloads) {
            try { w.teardown(baseCtx); } catch (Exception ignored) {}
        }
    }

    private static long runThread(Workload workload, BenchmarkContext ctx) throws Exception {
        return runThreadPartial(workload, ctx, ctx.iterations);
    }

    private static long runThreadPartial(Workload workload, BenchmarkContext ctx, int iterationCount) throws Exception {
        long ops = 0;
        for (int i = 0; i < iterationCount; i++) {
            workload.runIteration(ctx, i);
            ops++;
        }
        return ops;
    }

    private static Workload createWorkload(String name) {
        return switch (name.toLowerCase()) {
            case "event" -> new EventAggregationWorkload();
            case "graph" -> new GraphTraversalWorkload();
            case "bloom" -> new BloomFilterWorkload();
            case "cache" -> new LoadingCacheWorkload();
            case "immutable" -> new ImmutableSnapshotWorkload();
            default -> null;
        };
    }

    private static Map<String, String> parseArgs(String[] args) {
        Map<String, String> map = new HashMap<>();
        for (int i = 0; i < args.length; i++) {
            String a = args[i];
            if (a.equals("-h") || a.equals("--help")) { map.put("help", "1"); }
            else if (a.startsWith("--")) {
                String key = a.substring(2);
                if (i + 1 < args.length && !args[i+1].startsWith("--")) {
                    map.put(key, args[++i]);
                } else {
                    map.put(key, "true");
                }
            }
        }
        return map;
    }

    private static void usage() {
        System.out.println("Usage: java BenchmarkRunner --workload <event|graph|bloom|cache|immutable> --dataSize <N> --iterations <M> --threads <T> [--warmupIterations <W>|--noWarmup]");
        System.out.println("Defaults (dataSize / iterations) if omitted:");
        System.out.printf("  event: %d / %d%n", DEFAULT_DATASIZE.get("event"), DEFAULT_ITERATIONS.get("event"));
        System.out.printf("  graph: %d / %d%n", DEFAULT_DATASIZE.get("graph"), DEFAULT_ITERATIONS.get("graph"));
        System.out.printf("  bloom: %d / %d%n", DEFAULT_DATASIZE.get("bloom"), DEFAULT_ITERATIONS.get("bloom"));
        System.out.printf("  cache: %d / %d%n", DEFAULT_DATASIZE.get("cache"), DEFAULT_ITERATIONS.get("cache"));
        System.out.printf("  immutable: %d / %d%n", DEFAULT_DATASIZE.get("immutable"), DEFAULT_ITERATIONS.get("immutable"));
        System.out.println("Warmup: default = min(5, max(1, iterations/500)); override with --warmupIterations or disable via --noWarmup");
    }
}
