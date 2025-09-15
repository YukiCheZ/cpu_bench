package org.example;

import smile.clustering.KMeans;

import java.util.Random;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class KMeansBenchmark {

    public static void main(String[] args) throws InterruptedException {
        // 命令行参数解析
        int nSamples  = args.length > 0 ? Integer.parseInt(args[0]) : 100_000; // 每副本样本数
        int nFeatures = args.length > 1 ? Integer.parseInt(args[1]) : 50;      // 特征维度
        int nClusters = args.length > 2 ? Integer.parseInt(args[2]) : 10;      // 聚类数
        int nCopies   = args.length > 3 ? Integer.parseInt(args[3]) : 1;       // 副本数 = 并行线程数

        System.out.printf("Running KMeans benchmark: samples=%d, features=%d, clusters=%d, copies=%d%n",
                nSamples, nFeatures, nClusters, nCopies);

        ExecutorService executor = Executors.newFixedThreadPool(nCopies);

        for (int copy = 0; copy < nCopies; copy++) {
            final int copyId = copy;
            executor.submit(() -> {
                // 单线程生成数据
                double[][] data = new double[nSamples][nFeatures];
                Random rand = new Random(42 + copyId);
                for (int i = 0; i < nSamples; i++) {
                    for (int j = 0; j < nFeatures; j++) {
                        data[i][j] = rand.nextDouble();
                    }
                }

                // 单线程运行 KMeans
                long start = System.nanoTime();
                KMeans.fit(data, nClusters);
                long end = System.nanoTime();

                System.out.printf("Copy %d finished. Runtime: %.3f seconds%n",
                        copyId, (end - start) / 1e9);
            });
        }

        executor.shutdown();
        executor.awaitTermination(1, TimeUnit.HOURS);

        System.out.println("All copies finished.");
    }
}
