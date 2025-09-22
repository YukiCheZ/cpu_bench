package benchmark.smile;

import smile.clustering.KMeans;

import java.io.BufferedReader;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class KMeansBenchmark {

    public static double[][] loadCSV(String path) throws Exception {
        ArrayList<double[]> rows = new ArrayList<>();
        int nFeatures = -1;
        try (BufferedReader br = new BufferedReader(new FileReader(path))) {
            String line;
            while ((line = br.readLine()) != null) {
                String[] parts = line.split(",");
                if (nFeatures == -1) {
                    nFeatures = parts.length; 
                } else if (parts.length != nFeatures) {
                    throw new IllegalArgumentException("Inconsistent number of features in CSV");
                }
                double[] row = new double[parts.length];
                for (int i = 0; i < parts.length; i++) {
                    row[i] = Double.parseDouble(parts[i]);
                }
                rows.add(row);
            }
        }
        System.out.printf("[INFO] Loaded %d samples, %d features%n", rows.size(), nFeatures);
        return rows.toArray(new double[0][]);
    }

    public static void main(String[] args) throws Exception {
        String dataPath = args.length > 0 ? args[0] : "./data/kmeans.csv";
        int nClusters = args.length > 1 ? Integer.parseInt(args[1]) : 1000;
        int nCopies   = args.length > 2 ? Integer.parseInt(args[2]) : 1;

        double[][] data = loadCSV(dataPath);
        int nSamples = data.length;
        int nFeatures = data[0].length;

        System.out.printf("[INFO] Running KMeans benchmark: samples=%d, features=%d, clusters=%d, copies=%d%n",
                nSamples, nFeatures, nClusters, nCopies);

        ExecutorService executor = Executors.newFixedThreadPool(nCopies);

        for (int copy = 0; copy < nCopies; copy++) {
            final int copyId = copy;
            executor.submit(() -> {
                try {
                    long start = System.nanoTime();
                    KMeans.fit(data, nClusters);
                    long end = System.nanoTime();
                    System.out.printf("[RESULT] Copy %d finished. Runtime: %.3f seconds%n",
                            copyId, (end - start) / 1e9);
                } catch (Exception e) {
                    e.printStackTrace();
                }
            });
        }

        executor.shutdown();
        executor.awaitTermination(1, TimeUnit.HOURS);

        System.out.println("[INFO] All copies finished.");
    }
}
