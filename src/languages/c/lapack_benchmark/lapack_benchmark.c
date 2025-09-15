#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <pthread.h>
#include <lapacke.h>

double wall_time() {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

enum { MODE_SOLVE, MODE_EIGEN, MODE_SVD };

typedef struct {
    int thread_id;
    int n;
    int mode;
    int iters;
} thread_arg_t;

double run_task(int mode, int n) {
    char fname[256];
    double t0 = 0.0, t1 = 0.0;

    if (mode == MODE_SOLVE) {
        snprintf(fname, sizeof(fname), "data/solve_A_%d.bin", n);
        FILE* fa = fopen(fname, "rb");
        if (!fa) { fprintf(stderr, "Error: cannot open %s\n", fname); exit(1); }
        double* A = malloc(n * n * sizeof(double));
        size_t ret = fread(A, sizeof(double), n*n, fa);
        if(ret != n*n) { fprintf(stderr, "Error: read %zu elements, expected %d\n", ret, n*n); exit(1); }
        fclose(fa);

        snprintf(fname, sizeof(fname), "data/solve_b_%d.bin", n);
        FILE* fb = fopen(fname, "rb");
        if (!fb) { fprintf(stderr, "Error: cannot open %s\n", fname); exit(1); }
        double* b = malloc(n * sizeof(double));
        ret = fread(b, sizeof(double), n, fb);
        fclose(fb);

        int* ipiv = malloc(n * sizeof(int));

        t0 = wall_time();
        LAPACKE_dgesv(LAPACK_ROW_MAJOR, n, 1, A, n, ipiv, b, 1);
        t1 = wall_time();

        free(A); free(b); free(ipiv);
    }
    else if (mode == MODE_EIGEN) {
        snprintf(fname, sizeof(fname), "data/eigen_A_%d.bin", n);
        FILE* fa = fopen(fname, "rb");
        if (!fa) { fprintf(stderr, "Error: cannot open %s\n", fname); exit(1); }
        double* A = malloc(n * n * sizeof(double));
        size_t ret = fread(A, sizeof(double), n*n, fa);
        if(ret != n*n) { fprintf(stderr, "Error: read %zu elements, expected %d\n", ret, n*n); exit(1); }
        fclose(fa);

        double* w = malloc(n * sizeof(double));

        t0 = wall_time();
        LAPACKE_dsyev(LAPACK_ROW_MAJOR, 'V', 'U', n, A, n, w);
        t1 = wall_time();

        free(A); free(w);
    }
    else if (mode == MODE_SVD) {
        snprintf(fname, sizeof(fname), "data/svd_A_%d.bin", n);
        FILE* fa = fopen(fname, "rb");
        if (!fa) { fprintf(stderr, "Error: cannot open %s\n", fname); exit(1); }
        double* A = malloc(n * n * sizeof(double));
        size_t ret = fread(A, sizeof(double), n*n, fa);
        if(ret != n*n) { fprintf(stderr, "Error: read %zu elements, expected %d\n", ret, n*n); exit(1); }
        fclose(fa);

        double* S = malloc(n * sizeof(double));
        double* U = malloc(n * n * sizeof(double));
        double* VT = malloc(n * n * sizeof(double));
        int k = (n > 1) ? (n - 1) : 1;
        double* superb = malloc(k * sizeof(double));

        t0 = wall_time();
        LAPACKE_dgesvd(LAPACK_ROW_MAJOR, 'A', 'A', n, n, A, n, S, U, n, VT, n, superb);
        t1 = wall_time();

        free(A); free(S); free(U); free(VT); free(superb);
    }
    return t1 - t0;
}

void* thread_func(void* arg) {
    thread_arg_t* targ = (thread_arg_t*)arg;
    for (int i = 0; i < targ->iters; i++) {
        run_task(targ->mode, targ->n);
    }
    return NULL;
}

int main(int argc, char* argv[]) {
    int n = 2000;
    char mode_str[16] = "solve";
    int iters = 3;
    int warmup = 1;
    int threads = 1;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--size") == 0 && i + 1 < argc) n = atoi(argv[++i]);
        else if (strcmp(argv[i], "--mode") == 0 && i + 1 < argc) strncpy(mode_str, argv[++i], 15);
        else if (strcmp(argv[i], "--iters") == 0 && i + 1 < argc) iters = atoi(argv[++i]);
        else if (strcmp(argv[i], "--warmup") == 0 && i + 1 < argc) warmup = atoi(argv[++i]);
        else if (strcmp(argv[i], "--threads") == 0 && i + 1 < argc) threads = atoi(argv[++i]);
        else if (strcmp(argv[i], "--help") == 0) {
            printf("Usage: %s [--size N] [--mode MODE] [--iters ITERS] [--warmup WARMUP] [--threads THREADS]\n", argv[0]);
            printf("Modes: solve, eigen, svd\n");
            return 0;
        }
    }

    int mode;
    if (strcmp(mode_str, "solve") == 0) mode = MODE_SOLVE;
    else if (strcmp(mode_str, "eigen") == 0) mode = MODE_EIGEN;
    else if (strcmp(mode_str, "svd") == 0) mode = MODE_SVD;
    else {
        fprintf(stderr, "Unknown mode: %s\n", mode_str);
        return 1;
    }

    // === Warmup ===
    for (int i = 0; i < warmup; i++) run_task(mode, n);

    // === Benchmark ===
    pthread_t* tids = malloc(sizeof(pthread_t) * threads);
    thread_arg_t* targs = malloc(sizeof(thread_arg_t) * threads);

    double start = wall_time();
    for (int i = 0; i < threads; i++) {
        targs[i].thread_id = i;
        targs[i].n = n;
        targs[i].mode = mode;
        targs[i].iters = iters;
        pthread_create(&tids[i], NULL, thread_func, &targs[i]);
    }

    for (int i = 0; i < threads; i++) {
        pthread_join(tids[i], NULL);
    }
    double end = wall_time();

    printf("[INFO] Mode=%s, N=%d, iters=%d, warmup=%d, threads=%d\n",
           mode_str, n, iters, warmup, threads);
    printf("[RESULT] WallTime: %.6f sec\n", end-start);

    free(tids);
    free(targs);
    return 0;
}
