/**
 * TinyKW - A keyword spotting library
 *
 * Copyright (c) 2026 voyelle-io.
 * 
 * Licensed under the Apache License, Version 2.0.
 * See the LICENSE file in the root of this repository for full terms.
 *
 */


#ifndef TKW_PUBLIC_H_
#define TKW_PUBLIC_H_

#ifdef __cplusplus
 extern "C" {
#endif

#include <stddef.h>
#include <stdint.h>
#include <stdalign.h>

#if defined(_WIN32)
  #ifdef TKW_BUILD
    #define TKW_API __declspec(dllexport)
  #else
    #define TKW_API __declspec(dllimport)
  #endif
#elif !defined(__linux__) && !defined(__APPLE__) && (defined(__arm__) || defined(__thumb__))
  #define TKW_API
#else
  #define TKW_API __attribute__((visibility("default")))
#endif

#define TKW_VERSION_MAJOR 1
#define TKW_VERSION_MINOR 1
#define TKW_VERSION_PATCH 1

#define TKW_CTX_SIZE         14000
#define TKW_AUDIO_FRAME_SIZE 480

typedef enum {
    TKW_OK = 0,
    TKW_NOT_INITIALIZED = 1,
    TKW_TOO_MANY_KEYWORDS = 2,
    TKW_INVALID_KEYWORD_BYTES = 3,
    TKW_WRONG_INPUT_SIZE = 4,
    TKW_INVALID_ARGUMENT = 5,
    TKW_INVALID_KEYWORD_ID = 6,
    TKW_INTERNAL_ERROR = 7,
} tkw_status;



/*
 * `tkw_context` holds the memory required for internal state.
 */
typedef struct {
    alignas(16) uint8_t internal_memory[TKW_CTX_SIZE]; 
} tkw_context;

/*
 * Initializes a `tkw_context` provided by caller.
 * Calling tkw_init() multiple times is allowed and resets all internal state,
 * including registered keywords and detection flags.
 * Args:
 *  - ctx: context to initialize.
 *
 * Returns TKW_OK on success.
 */
TKW_API tkw_status tkw_init(tkw_context* ctx);


/*
 * Callback when a keyword is detected.
 *  - keyword_id: ID of the detected keyword, as returned by tkw_add_keyword().
 *  - user_ctx: pointer to void passed to tkw_set_callback().
 * It is important to keep the callback short.
 */
typedef void(*tkw_callback)(uint8_t keyword_id, void* user_ctx);

/*
 * Sets the callback called when a keyword is detected.
 * Args:
 *  - user_cb: callback function of signature `tkw_callback`.
 *  - user_ctx: pointer that will be passed to the callback.
 *  - ctx: TinyKW context
 * 
 * Returns TKW_OK on success.
 */
TKW_API tkw_status tkw_set_callback(tkw_callback user_cb, void* user_ctx, tkw_context* ctx);

/* 
 * Adds a keyword to detect.
 *
 * Args:
 *  - data: 48-byte encoded keyword (can be obtained from https://www.voyelle.io/tinykw)
 *  - detection_threshold: value between 0 and 255, controlling how strict the detection is.
 *      * Higher: fewer false positives, but more missed detections.
 *      * Lower:  fewer missed detections, but more false positives.
 *      It is recommended to start at 128, and then adjust if necessary.
 *  - out_id: receives the ID assigned to the keyword.
 *  - ctx: TinyKW context.
 */
TKW_API tkw_status tkw_add_keyword(const uint8_t data[48], uint8_t detection_threshold, uint8_t* out_id, tkw_context* ctx);

/*
 * Deletes a keyword
 * 
 * Args:
 *  - id: ID of the keyword, as returned by tkw_add_keyword().
 *  - ctx: TinyKW context.
 * 
 * Returns TKW_OK on success.
 */
TKW_API tkw_status tkw_remove_keyword(uint8_t id, tkw_context* ctx);

/*
 * Processes one frame of 16-bit PCM audio sampled at 16 kHz.
 *
 * Args:
 *  - waveform: pointer to audio samples
 *  - size: number of samples in waveform, must equal TKW_AUDIO_FRAME_SIZE
 *  - ctx: TinyKW context
 */
TKW_API tkw_status tkw_process_frame(const int16_t* waveform, size_t size, tkw_context* ctx);

/*
 * Returns a human-readable string for a status code.
 * The returned pointer refers to a static string and must not be freed.
 */
TKW_API const char* tkw_status_string(tkw_status status);


#ifdef __cplusplus
}
#endif

#endif
