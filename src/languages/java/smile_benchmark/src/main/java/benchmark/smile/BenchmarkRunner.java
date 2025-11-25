package benchmark.smile;

import smile.clustering.KMeans;

import java.io.BufferedReader;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.concurrent.*;

public class BenchmarkRunner {

    private static double[][] loadCSVDouble(String path) throws Exception {
        ArrayList<double[]> rows = new ArrayList<>();
        int n = -1;
        try (BufferedReader br = new BufferedReader(new FileReader(path))) {
            String line;
            while ((line = br.readLine()) != null) {
                if (line.isEmpty()) continue;
                String[] parts = line.split(",");
                if (n == -1) n = parts.length;
                double[] r = new double[n];
                for (int i = 0; i < n; i++) r[i] = Double.parseDouble(parts[i]);
                rows.add(r);
            }
        }
        return rows.toArray(new double[0][]);
    }

    private static class Result { final int id; final double seconds; Result(int id,double s){this.id=id;this.seconds=s;} }

    public static void main(String[] args) throws Exception {
        String workload = "kmeans";
        String data = "./data/kmeans.csv";
        int clusters = 100;
        int threads = Math.max(1, Runtime.getRuntime().availableProcessors());
        Integer iters = null;

        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--workload": workload = args[++i]; break;
                case "--data": data = args[++i]; break;
                case "--clusters": clusters = Integer.parseInt(args[++i]); break;
                case "--threads": threads = Integer.parseInt(args[++i]); break;
                case "--iters": iters = Integer.parseInt(args[++i]); break;
            }
        }

        if (iters == null) {
            switch (workload) {
                case "kmeans": iters = 6; break;
                default: iters = 1; break;
            }
        }

        // Preload data once based on workload (only kmeans now)
        double[][] matrixData = null;
        if ("kmeans".equals(workload)) {
            matrixData = loadCSVDouble(data);
        }

        ExecutorService pool = Executors.newFixedThreadPool(threads);
        List<Future<Result>> futures = new ArrayList<>();
        for (int t = 0; t < threads; t++) {
            final int id = t;
            final String wl = workload;
            final int cl = clusters;
            final int iterations = iters;
            final double[][] sharedMatrix = matrixData;
            futures.add(pool.submit(() -> {
                long start = System.nanoTime();
                for (int i = 0; i < iterations; i++) {
                    if ("kmeans".equals(wl)) {
                        KMeans.fit(sharedMatrix, cl);
                    } else {
                        throw new IllegalArgumentException("Unknown workload: " + wl);
                    }
                }
                long end = System.nanoTime();
                return new Result(id, (end - start)/1e9);
            }));
        }
        pool.shutdown();
        pool.awaitTermination(1, TimeUnit.HOURS);
        double max = 0.0;
        for (Future<Result> f : futures) {
            Result r = f.get();
            if (r.seconds > max) max = r.seconds;
        }
        System.out.printf("[RESULT] Total elapsed time: %.4f s%n", max);
        System.exit(0);
    }
}
