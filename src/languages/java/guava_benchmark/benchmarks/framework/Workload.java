package benchmarks.framework;

public interface Workload {
    void setup(BenchmarkContext ctx) throws Exception;
    void runIteration(BenchmarkContext ctx, int iteration) throws Exception;
    void teardown(BenchmarkContext ctx) throws Exception;
    default String name() { return getClass().getSimpleName(); }
}
