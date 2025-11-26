// lapack_benchmark_gen_totalwall.c
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <pthread.h>
#include <errno.h>
#include <lapacke.h>
#include <stdint.h>
#include <sys/stat.h>
#include <math.h>

double wall_time(void) {
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

    /* per-thread working buffers (allocated once) */
    double *A;    /* n * n */
    double *b;    /* n (for solve) */
    double *w;    /* n (for eigen) */
    double *S;    /* min(m,n) (for svd) */
    double *U;    /* n*n (for svd) */
    double *VT;   /* n*n (for svd) */
    double *superb; /* min(m,n)-1 or NULL */
    lapack_int *ipiv; /* n (for solve) */

    /* stats */
    double *times; /* per-iteration times (iters) */
} thread_arg_t;

/* original data (shared, read-only) */
static double *origA = NULL;
static double *origb = NULL;

static int aligned_alloc_ptr(void **ptr, size_t alignment, size_t size) {
    if (posix_memalign(ptr, alignment, size) != 0) {
        *ptr = malloc(size);
        return (*ptr) ? 0 : -1;
    }
    return 0;
}

/* random double in [-1,1] using srand()/rand() (seeded earlier) */
static double rand_double_signed(void) {
    return (double)rand() / RAND_MAX * 2.0 - 1.0;
}

/* generate matrices in memory according to mode */
static int generate_data(int mode, int n, unsigned int seed) {
    srand(seed);

    /* allocate origA and origb */
    size_t nn = (size_t)n * n;
    if (aligned_alloc_ptr((void**)&origA, 64, nn * sizeof(double)) != 0) return -1;
    if (mode == MODE_SOLVE) {
        if (aligned_alloc_ptr((void**)&origb, 64, (size_t)n * sizeof(double)) != 0) return -1;
    } else {
        origb = NULL;
    }

    if (mode == MODE_SOLVE) {
        /* generate general matrix but make it diagonally dominant to avoid singularity */
        for (int i = 0; i < n; ++i) {
            double rowsum = 0.0;
            for (int j = 0; j < n; ++j) {
                double v = rand_double_signed();
                origA[i*n + j] = v;
                rowsum += fabs(v);
            }
            origA[i*n + i] += rowsum + 1.0; /* make diagonal dominant */
        }
        for (int i = 0; i < n; ++i) origb[i] = rand_double_signed();
    } else if (mode == MODE_EIGEN) {
        /* symmetric matrix: fill upper triangle and mirror */
        for (int i = 0; i < n; ++i) {
            for (int j = i; j < n; ++j) {
                double v = rand_double_signed();
                origA[i*n + j] = v;
                origA[j*n + i] = v;
            }
        }
    } else { /* SVD */
        for (size_t k = 0; k < nn; ++k) {
            origA[k] = rand_double_signed();
        }
    }
    return 0;
}

/* run LAPACK on thread-local buffers, record time */
static double run_task_with_buffers(thread_arg_t *t) {
    int n = t->n;
    double t0, t1;
    int info = 0;

    if (t->mode == MODE_SOLVE) {
        t0 = wall_time();
        info = LAPACKE_dgesv(LAPACK_ROW_MAJOR, n, 1, t->A, n, t->ipiv, t->b, 1);
        t1 = wall_time();
        if (info != 0) fprintf(stderr, "[ERROR] Thread %d: dgesv returned %d\n", t->thread_id, info);
    } else if (t->mode == MODE_EIGEN) {
        t0 = wall_time();
        info = LAPACKE_dsyev(LAPACK_ROW_MAJOR, 'V', 'U', n, t->A, n, t->w);
        t1 = wall_time();
        if (info != 0) fprintf(stderr, "[ERROR] Thread %d: dsyev returned %d\n", t->thread_id, info);
    } else {
        int m = n, lda = n;
        t0 = wall_time();
        info = LAPACKE_dgesvd(LAPACK_ROW_MAJOR, 'A', 'A', m, n, t->A, lda,
                              t->S, t->U, n, t->VT, n, t->superb ? t->superb : NULL);
        t1 = wall_time();
        if (info != 0) fprintf(stderr, "[ERROR] Thread %d: dgesvd returned %d\n", t->thread_id, info);
    }
    return t1 - t0;
}

static void *thread_func(void *arg) {
    thread_arg_t *t = (thread_arg_t*)arg;
    for (int it = 0; it < t->iters; ++it) {
        /* restore from originals before each iter */
        memcpy(t->A, origA, (size_t)t->n * t->n * sizeof(double));
        if (t->mode == MODE_SOLVE && origb) memcpy(t->b, origb, (size_t)t->n * sizeof(double));

        double dt = run_task_with_buffers(t);
        t->times[it] = dt;
    }
    return NULL;
}

/* allocate and prepare per-thread buffers (copy initial data) */
static int prepare_thread_buffers(thread_arg_t *t, int n, int mode, int iters) {
    t->n = n;
    t->mode = mode;
    t->iters = iters;

    if (aligned_alloc_ptr((void**)&t->A, 64, (size_t)n * n * sizeof(double)) != 0) return -1;

    if (mode == MODE_SOLVE) {
        if (aligned_alloc_ptr((void**)&t->b, 64, (size_t)n * sizeof(double)) != 0) return -1;
        if (aligned_alloc_ptr((void**)&t->ipiv, 64, (size_t)n * sizeof(lapack_int)) != 0) return -1;
    } else if (mode == MODE_EIGEN) {
        if (aligned_alloc_ptr((void**)&t->w, 64, (size_t)n * sizeof(double)) != 0) return -1;
    } else {
        int k = n;
        if (aligned_alloc_ptr((void**)&t->S, 64, (size_t)k * sizeof(double)) != 0) return -1;
        if (aligned_alloc_ptr((void**)&t->U, 64, (size_t)n * n * sizeof(double)) != 0) return -1;
        if (aligned_alloc_ptr((void**)&t->VT, 64, (size_t)n * n * sizeof(double)) != 0) return -1;
        int superb_len = (n > 1) ? (n - 1) : 0;
        if (superb_len > 0) {
            if (aligned_alloc_ptr((void**)&t->superb, 64, (size_t)superb_len * sizeof(double)) != 0) return -1;
        } else {
            t->superb = NULL;
        }
    }

    t->times = malloc((size_t)iters * sizeof(double));
    if (!t->times) return -1;

    /* initial copy so buffers have data before first iter */
    memcpy(t->A, origA, (size_t)n * n * sizeof(double));
    if (mode == MODE_SOLVE && origb) memcpy(t->b, origb, (size_t)n * sizeof(double));

    return 0;
}

static void compute_stats(double *arr, int len, double *avg, double *mn, double *mx) {
    if (len <= 0) { *avg = *mn = *mx = 0.0; return; }
    double s = 0.0;
    *mn = arr[0]; *mx = arr[0];
    for (int i = 0; i < len; ++i) {
        s += arr[i];
        if (arr[i] < *mn) *mn = arr[i];
        if (arr[i] > *mx) *mx = arr[i];
    }
    *avg = s / len;
}

int main(int argc, char* argv[]) {
    int n = 2048;
    char mode_str[16] = "solve";
    int iters = 3;
    int warmup = 1;
    int num_threads = 1;
    unsigned int seed = 42;
    int iters_specified = 0;  

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--size") == 0 && i + 1 < argc) n = atoi(argv[++i]);
        else if (strcmp(argv[i], "--mode") == 0 && i + 1 < argc) strncpy(mode_str, argv[++i], 15);
        else if (strcmp(argv[i], "--iters") == 0 && i + 1 < argc) {
            iters = atoi(argv[++i]);
            iters_specified = 1;  
        }
        else if (strcmp(argv[i], "--warmup") == 0 && i + 1 < argc) warmup = atoi(argv[++i]);
        else if (strcmp(argv[i], "--threads") == 0 && i + 1 < argc) num_threads = atoi(argv[++i]);
        else if (strcmp(argv[i], "--seed") == 0 && i + 1 < argc) seed = (unsigned int)atoi(argv[++i]);
        else if (strcmp(argv[i], "--help") == 0) {
            printf("Usage: %s [--size N] [--mode MODE] [--iters ITERS] [--warmup WARMUP] [--threads THREADS] [--seed S]\n", argv[0]);
            printf("Modes: solve, eigen, svd\n");
            return 0;
        }
    }

    if (!iters_specified) {
        if (strcmp(mode_str, "solve") == 0)
            iters = 1500;
        else if (strcmp(mode_str, "eigen") == 0)
            iters = 6;
        else if (strcmp(mode_str, "svd") == 0)
            iters = 3;
        else
            iters = 1;  
    }

    int mode;
    if (strcmp(mode_str, "solve") == 0) mode = MODE_SOLVE;
    else if (strcmp(mode_str, "eigen") == 0) mode = MODE_EIGEN;
    else if (strcmp(mode_str, "svd") == 0) mode = MODE_SVD;
    else {
        fprintf(stderr, "[ERROR] Unknown mode: %s\n", mode_str);
        return 1;
    }

    /* set OpenBLAS threading default */
    setenv("OPENBLAS_NUM_THREADS", "1", 1);
    printf("[INFO] Forced OPENBLAS_NUM_THREADS=1 to avoid nested parallelism\n");


    /* generate data in memory */
    if (generate_data(mode, n, seed) != 0) {
        fprintf(stderr, "[ERROR] Failed to generate input data\n");
        return 1;
    }

    /* allocate thread structures */
    pthread_t *tids = malloc((size_t)num_threads * sizeof(pthread_t));
    thread_arg_t *targs = calloc((size_t)num_threads, sizeof(thread_arg_t));
    if (!tids || !targs) { fprintf(stderr, "OOM\n"); return 1; }

    for (int t = 0; t < num_threads; ++t) {
        targs[t].thread_id = t;
        if (prepare_thread_buffers(&targs[t], n, mode, iters) != 0) {
            fprintf(stderr, "[ERROR] Failed to allocate buffers for thread %d\n", t);
            return 1;
        }
    }

    /* spawn threads and measure total walltime from start to finish */
    printf("[INFO] Starting benchmark:\n");
    double t_start = wall_time();
    for (int t = 0; t < num_threads; ++t) {
        if (pthread_create(&tids[t], NULL, thread_func, &targs[t]) != 0) {
            perror("pthread_create");
            return 1;
        }
    }

    for (int t = 0; t < num_threads; ++t) pthread_join(tids[t], NULL);
    double t_end = wall_time();
    double total_walltime = t_end - t_start;

    /* Output only total walltime and basic info */
    printf("[INFO] Mode=%s, N=%d, threads=%d, iters=%d, warmup=%d, seed=%u\n",
           mode_str, n, num_threads, iters, warmup, seed);
    printf("[RESULT] Total elapsed time: %.4f s\n", total_walltime);

    /* cleanup */
    for (int t = 0; t < num_threads; ++t) {
        free(targs[t].A);
        free(targs[t].b);
        free(targs[t].w);
        free(targs[t].S);
        free(targs[t].U);
        free(targs[t].VT);
        free(targs[t].superb);
        free(targs[t].ipiv);
        free(targs[t].times);
    }
    free(targs);
    free(tids);
    free(origA);
    free(origb);

    return 0;
}
