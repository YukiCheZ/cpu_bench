package benchmarks.workloads;

import benchmarks.framework.BenchmarkContext;
import benchmarks.framework.Workload;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.hash.Hashing;

import java.util.*;

/**
 * Immutable snapshot workload:
 * - Builds several immutable views (snapshots) from a base int array each iteration
 * - Performs set intersection/difference and hashing reductions
 */
public class ImmutableSnapshotWorkload implements Workload {
    private int[] base;

    @Override
    public void setup(BenchmarkContext ctx) {
        base = ctx.generator.generateIntArray(ctx.dataSize, Integer.MAX_VALUE);
    }

    @Override
    public void runIteration(BenchmarkContext ctx, int iteration) {
        int slice = Math.max(1, base.length / 8);
        ImmutableList<Integer> snapA = buildSlice(0, slice);
        ImmutableList<Integer> snapB = buildSlice(slice/2, slice + slice/2);
        ImmutableSet<Integer> setA = ImmutableSet.copyOf(snapA);
        ImmutableSet<Integer> setB = ImmutableSet.copyOf(snapB);
        // Intersection and set difference hashing
        int intersect = 0;
        long sink = 0;
        for (Integer v : setA) if (setB.contains(v)) intersect++;
        for (Integer v : setA) if (!setB.contains(v)) sink += Hashing.murmur3_32().hashInt(v).asInt();
        for (Integer v : setB) if (!setA.contains(v)) sink ^= Hashing.murmur3_128().hashLong(v).asLong();
        // Build an additional incremental snapshot
        ImmutableList<Integer> snapC = buildSlice(slice, Math.min(base.length, slice * 2));
        ImmutableSet<Integer> setC = ImmutableSet.copyOf(snapC);
        for (Integer v : setC) sink += (v & 0xFF);
        if (sink == 0xdeadbeefL + intersect) System.out.println("avoid optimize");
    }

    private ImmutableList<Integer> buildSlice(int start, int endExclusive) {
        endExclusive = Math.min(base.length, endExclusive);
        ImmutableList.Builder<Integer> b = ImmutableList.builder();
        for (int i = start; i < endExclusive; i++) b.add(base[i]);
        return b.build();
    }

    @Override
    public void teardown(BenchmarkContext ctx) {
        base = null;
    }
}
