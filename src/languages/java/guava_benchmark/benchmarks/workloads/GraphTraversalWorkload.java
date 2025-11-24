package benchmarks.workloads;

import benchmarks.framework.BenchmarkContext;
import benchmarks.framework.Workload;
import benchmarks.utils.DataGenerator;
import com.google.common.graph.*;
import com.google.common.collect.ImmutableList;

import java.util.*;

/**
 * Builds a directed graph and performs multiple traversals:
 * - Uses Guava GraphBuilder to construct a mutable graph
 * - Executes BFS from multiple start nodes, a topological sort, and simple cycle detection
 */
public class GraphTraversalWorkload implements Workload {
    private MutableGraph<Integer> graph;
    private int nodeCount;
    private List<Integer> startNodes;

    @Override
    public void setup(BenchmarkContext ctx) {
        nodeCount = Math.max(1000, ctx.dataSize / 50); // Control size to avoid memory explosion
        Map<Integer, Set<Integer>> edges = ctx.generator.generateDirectedEdges(nodeCount, 6);
        graph = GraphBuilder.directed().allowsSelfLoops(false).expectedNodeCount(nodeCount).build();
        for (int i = 0; i < nodeCount; i++) graph.addNode(i);
        for (Map.Entry<Integer, Set<Integer>> e : edges.entrySet()) {
            int from = e.getKey();
            for (int to : e.getValue()) graph.putEdge(from, to);
        }
        startNodes = ImmutableList.of(0, nodeCount/3, (2*nodeCount)/3);
    }

    @Override
    public void runIteration(BenchmarkContext ctx, int iteration) {
        long sink = 0;
        // Multi-source BFS
        for (int s : startNodes) {
            sink += bfsCount(s);
        }
        // Simple topological sort (Kahn's algorithm)
        sink += topoCount();
        // Cycle detection (DFS with visitation states)
        sink += cycleCheck();
        if (sink == 42L) System.out.println("avoid optimize");
    }

    private int bfsCount(int start) {
        Set<Integer> visited = new HashSet<>();
        ArrayDeque<Integer> dq = new ArrayDeque<>();
        dq.add(start);
        visited.add(start);
        int edgesTraversed = 0;
        while (!dq.isEmpty()) {
            int v = dq.poll();
            for (Integer nxt : graph.successors(v)) {
                edgesTraversed++;
                if (visited.add(nxt)) dq.add(nxt);
            }
        }
        return edgesTraversed + visited.size();
    }

    private int topoCount() {
        Map<Integer, Integer> indeg = new HashMap<>();
        for (Integer n : graph.nodes()) indeg.put(n, 0);
        for (Integer n : graph.nodes()) {
            for (Integer m : graph.successors(n)) indeg.put(m, indeg.get(m) + 1);
        }
        ArrayDeque<Integer> q = new ArrayDeque<>();
        for (Map.Entry<Integer, Integer> e : indeg.entrySet()) if (e.getValue() == 0) q.add(e.getKey());
        int count = 0;
        while (!q.isEmpty()) {
            int v = q.poll();
            count++;
            for (Integer nxt : graph.successors(v)) {
                int val = indeg.get(nxt) - 1;
                indeg.put(nxt, val);
                if (val == 0) q.add(nxt);
            }
        }
        return count;
    }

    private int cycleCheck() {
        // state codes: 0=unvisited, 1=visiting, 2=done
        int cycles = 0;
        int[] state = new int[nodeCount];
        for (int i = 0; i < nodeCount; i++) {
            if (state[i] == 0 && dfs(i, state)) cycles++;
        }
        return cycles;
    }

    private boolean dfs(int v, int[] state) {
        state[v] = 1;
        for (Integer nxt : graph.successors(v)) {
            if (state[nxt] == 1) return true; // Found cycle
            if (state[nxt] == 0 && dfs(nxt, state)) return true;
        }
        state[v] = 2;
        return false;
    }

    @Override
    public void teardown(BenchmarkContext ctx) {
        graph = null;
        startNodes = null;
    }
}
