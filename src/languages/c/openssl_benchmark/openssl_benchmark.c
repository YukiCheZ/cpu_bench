#include <openssl/evp.h>
#include <openssl/sha.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <time.h>

#define DEFAULT_THREADS 1
#define DATA_FILE "./data/data.bin"
#define DEFAULT_ITERS 200
#define DEFAULT_WARMUP 1

unsigned char g_key[32], g_iv[16];
unsigned char *g_data = NULL;
size_t g_data_size = 0;

typedef struct {
    int thread_id;
    int iters;
} thread_arg_t;

void* thread_func(void* arg) {
    thread_arg_t *targ = (thread_arg_t*)arg;
    int outlen, tmplen;

    unsigned char *plaintext = malloc(g_data_size);
    unsigned char *ciphertext = malloc(g_data_size + 16);
    unsigned char *decrypted = malloc(g_data_size + 16);
    if (!plaintext || !ciphertext || !decrypted) {
        fprintf(stderr, "Thread %d: memory allocation failed\n", targ->thread_id);
        return NULL;
    }

    memcpy(plaintext, g_data, g_data_size);

    EVP_CIPHER_CTX *ctx_enc = EVP_CIPHER_CTX_new();
    EVP_CIPHER_CTX *ctx_dec = EVP_CIPHER_CTX_new();
    EVP_EncryptInit_ex(ctx_enc, EVP_aes_256_cbc(), NULL, g_key, g_iv);
    EVP_DecryptInit_ex(ctx_dec, EVP_aes_256_cbc(), NULL, g_key, g_iv);

    for(int i = 0; i < targ->iters; i++) {
        EVP_EncryptInit_ex(ctx_enc, NULL, NULL, NULL, NULL);
        EVP_EncryptUpdate(ctx_enc, ciphertext, &outlen, plaintext, g_data_size);
        EVP_EncryptFinal_ex(ctx_enc, ciphertext + outlen, &tmplen);
        int cipher_len = outlen + tmplen;

        unsigned char hash256[SHA256_DIGEST_LENGTH];
        SHA256(ciphertext, cipher_len, hash256);

        EVP_DecryptInit_ex(ctx_dec, NULL, NULL, NULL, NULL);
        EVP_DecryptUpdate(ctx_dec, decrypted, &outlen, ciphertext, cipher_len);
        EVP_DecryptFinal_ex(ctx_dec, decrypted + outlen, &tmplen);
        int dec_len = outlen + tmplen;

        unsigned char hash512[SHA512_DIGEST_LENGTH];
        SHA512(decrypted, dec_len, hash512);

        unsigned char checksum = 0;
        for(size_t k = 0; k < dec_len; k++)
            checksum ^= decrypted[k];
    }

    EVP_CIPHER_CTX_free(ctx_enc);
    EVP_CIPHER_CTX_free(ctx_dec);
    free(plaintext);
    free(ciphertext);
    free(decrypted);
    return NULL;
}

int main(int argc, char *argv[]) {
    int num_threads = DEFAULT_THREADS;
    int iters = DEFAULT_ITERS;
    int warmup = DEFAULT_WARMUP;
    char data_file[256] = DATA_FILE;

    for(int i = 1; i < argc; i++){
        if(strcmp(argv[i], "--threads") == 0 && i+1 < argc){
            num_threads = atoi(argv[++i]);
        } else if(strcmp(argv[i], "--input") == 0 && i+1 < argc){
            strncpy(data_file, argv[++i], sizeof(data_file)-1);
        } else if(strcmp(argv[i], "--iters") == 0 && i+1 < argc){
            iters = atoi(argv[++i]);
        } else if(strcmp(argv[i], "--warmup") == 0 && i+1 < argc){
            warmup = atoi(argv[++i]);
        } else if(strcmp(argv[i], "--help") == 0){
            printf("Usage: %s [--file data.bin] [--threads N] [--iters N] [--warmup N]\n", argv[0]);
            return 0;
        }
    }

    FILE *fp = fopen(data_file, "rb");
    if(!fp){
        perror("Failed to open data file");
        return 1;
    }
    fseek(fp, 0, SEEK_END);
    g_data_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    g_data = malloc(g_data_size);
    if(!g_data){
        fprintf(stderr, "Memory allocation for data failed\n");
        fclose(fp);
        return 1;
    }
    size_t nread = fread(g_data, 1, g_data_size, fp);
    if (nread != g_data_size) {
        fprintf(stderr, "Failed to read data file: expected %zu bytes, got %zu bytes\n", g_data_size, nread);
        fclose(fp);
        free(g_data);
        return 1;
    }
    fclose(fp);

    for(int i=0; i<32; i++) g_key[i] = (unsigned char)(rand() & 0xFF);
    for(int i=0; i<16; i++) g_iv[i] = (unsigned char)(rand() & 0xFF);

    pthread_t *threads = malloc(sizeof(pthread_t) * num_threads);
    thread_arg_t *targs = malloc(sizeof(thread_arg_t) * num_threads);

    // Warmup
    for(int i=0; i<num_threads; i++){
        targs[i].thread_id = i;
        targs[i].iters = warmup;
        pthread_create(&threads[i], NULL, thread_func, &targs[i]);
    }
    for(int i=0; i<num_threads; i++){
        pthread_join(threads[i], NULL);
    }

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    for(int i=0; i<num_threads; i++){
        targs[i].thread_id = i;
        targs[i].iters = iters;
        pthread_create(&threads[i], NULL, thread_func, &targs[i]);
    }
    for(int i=0; i<num_threads; i++){
        pthread_join(threads[i], NULL);
    }

    clock_gettime(CLOCK_MONOTONIC, &end);
    double seconds = (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec)/1e9;

    printf("[RESULT] CPU macrobenchmark finished in %.2f seconds (data=%zu bytes, threads=%d, iters=%d, warmup=%d)\n",
           seconds, g_data_size, num_threads, iters, warmup);

    free(threads);
    free(targs);
    free(g_data);
    return 0;
}
