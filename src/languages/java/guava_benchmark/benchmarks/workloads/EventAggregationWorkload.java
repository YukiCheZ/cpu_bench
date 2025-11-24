package benchmarks.workloads;

import benchmarks.framework.BenchmarkContext;
import benchmarks.framework.Workload;
import benchmarks.utils.DataGenerator;
import com.google.common.collect.*;
import com.google.common.hash.Hashing;

import java.util.*;

/**
 * Simulates event stream categorization and aggregation:
 * - Uses a Multimap to maintain a sliding window of recent events
 * - Uses a Multiset to track user frequency
 * - Computes per-batch top-K hot users and category hash contribution
 */
public class EventAggregationWorkload implements Workload {
    private DataGenerator.Event[] events;
    private Multimap<String, DataGenerator.Event> window;
    private Multiset<Integer> userFreq;
    private int windowSize;
    private int topK = 20;

    @Override
    public void setup(BenchmarkContext ctx) {
        windowSize = Math.min(10_000, ctx.dataSize);
        events = ctx.generator.generateEvents(ctx.dataSize, 200);
        // Use LinkedHashMultimap to preserve insertion order (simulate window eviction)
        window = LinkedHashMultimap.create(windowSize, 8);
        userFreq = HashMultiset.create(windowSize);
    }

    @Override
    public void runIteration(BenchmarkContext ctx, int iteration) {
        int batch = Math.min(windowSize, events.length);
        // Sliding window: clear and rebuild aggregation for current batch
        window.clear();
        userFreq.clear();
        for (int i = 0; i < batch; i++) {
            DataGenerator.Event e = events[(iteration * batch + i) % events.length];
            window.put(e.category, e);
            userFreq.add(e.userId);
        }
        // Compute category hash + frequency stats to emphasize CPU work
        long cpuSink = 0;
        for (String cat : window.keySet()) {
            int h = Hashing.murmur3_32().hashUnencodedChars(cat).asInt();
            cpuSink += h * window.get(cat).size();
        }
        // top-K users
        List<Integer> topUsers = new ArrayList<>(topK);
        // Repeated linear scans amplify hashing and comparisons intentionally
        for (int k = 0; k < topK; k++) {
            int bestUser = -1;
            int bestFreq = -1;
            for (Multiset.Entry<Integer> entry : userFreq.entrySet()) {
                int f = entry.getCount();
                if (f > bestFreq) { bestFreq = f; bestUser = entry.getElement(); }
            }
            if (bestUser == -1) break;
            topUsers.add(bestUser);
            userFreq.remove(bestUser, bestFreq); 
        }
        // Prevent JVM optimizing away the loop sink
        if (cpuSink == 123456789L) System.out.println(topUsers.size());
    }

    @Override
    public void teardown(BenchmarkContext ctx) {
        events = null;
        window.clear();
        userFreq.clear();
    }
}
