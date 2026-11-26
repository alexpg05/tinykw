/*
This demo uses Portaudio (https://portaudio.com/) to read the microphone audio and TinyKW to detect keywords.
*/
#include <string.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>
#include <signal.h>
#include <assert.h>

#include "portaudio.h"
#include "tinykw.h"
#include "keywords_encodings.h"

#define SAMPLE_RATE (16000)
#define NUM_SECONDS (180)
#define NB_KEYWORDS (3)

static tkw_context tinykw_ctx;
static const uint8_t *keywords[] = {kw_hello_world, kw_banana_split, kw_activate};
static const char *names[] = {"hello world", "banana split", "activate"}; // for logging
static uint8_t keyword_ids[NB_KEYWORDS];

static volatile int keepRunning = 1;

/*
TinyKW callback
*/
static void on_detection(uint8_t keyword_id, void* args)
{
    // We just print the keyword's name
    uint8_t index = 0;
    while((index < NB_KEYWORDS) && (keyword_ids[index] != keyword_id)) index++;
    printf("Keyword detected: %s\n", names[index]);
}

void intHandler(int dummy) {
    keepRunning = 0;
}

int microphone_demo()
{
    signal(SIGINT, intHandler);
    tkw_status status;

    /* Initializes TinyKW context */
    status = tkw_init(&tinykw_ctx);
    assert(status == TKW_OK);
    printf("TinyKW engine initialized.\n");
    
    /* Add keywords */
    for (int k = 0; k < NB_KEYWORDS; ++k)
    {
        status = tkw_add_keyword(keywords[k], 128, &(keyword_ids[k]), &tinykw_ctx);
        assert(status == TKW_OK);
    }
    printf("Keywords added.\n");

    /* Set callback */
    status = tkw_set_callback(on_detection, NULL, &tinykw_ctx);
    assert(status == TKW_OK);

    /* Read and process microphone's data using Portaudio */
    PaStream *stream;
    PaError err;
    PaStreamParameters inputParameters;
    err = Pa_Initialize();
    if( err != paNoError ) goto done;

    //inputParameters.device = 1;
    inputParameters.device = Pa_GetDefaultInputDevice();
    if (inputParameters.device == paNoDevice) {
        fprintf(stderr,"Error: No default input device.\n");
        goto done;
    }
    inputParameters.channelCount = 1;
    inputParameters.sampleFormat = paInt16;
    inputParameters.suggestedLatency = Pa_GetDeviceInfo( inputParameters.device )->defaultLowInputLatency;
    inputParameters.hostApiSpecificStreamInfo = NULL;

    err = Pa_OpenStream(
              &stream,
              &inputParameters,
              NULL,
              SAMPLE_RATE,
              TKW_AUDIO_FRAME_SIZE,
              paClipOff,
              NULL,
              NULL );
    if( err != paNoError ) goto done;
    
    err = Pa_StartStream( stream );
    if( err != paNoError ) goto done;
    printf("Wire on. Will run %d seconds.\n", NUM_SECONDS); fflush(stdout);

    int16_t sampleBlock[TKW_AUDIO_FRAME_SIZE];
    for (int k = 0; k < NUM_SECONDS * SAMPLE_RATE / TKW_AUDIO_FRAME_SIZE; ++k)
    {
        err = Pa_ReadStream( stream, sampleBlock, TKW_AUDIO_FRAME_SIZE );
        if( err ) goto xrun;
        status = tkw_process_frame(sampleBlock, TKW_AUDIO_FRAME_SIZE, &tinykw_ctx); // process one frame
        assert(status == TKW_OK);

        if (keepRunning == 0)
            break;
    }
    printf("Wire off.\n"); fflush(stdout);

    // stop stream
    err = Pa_StopStream( stream );
    if( err != paNoError ) goto done;

    Pa_Terminate();
    return 0;

    xrun:
        printf("err = %d\n", err); fflush(stdout);
        if( stream ) {
            Pa_AbortStream( stream );
            Pa_CloseStream( stream );
        }
        Pa_Terminate();
        if( err & paInputOverflow )
            fprintf( stderr, "Input Overflow.\n" );
        if( err & paOutputUnderflow )
            fprintf( stderr, "Output Underflow.\n" );
        return -2;

    done:
        Pa_Terminate();
        if( err != paNoError )
        {
            fprintf( stderr, "An error occurred while using the portaudio stream\n" );
            fprintf( stderr, "Error number: %d\n", err );
            fprintf( stderr, "Error message: %s\n", Pa_GetErrorText( err ) );
            err = 1;          /* Always return 0 or 1, but no other return codes. */
        }
        return err;
}

int main(int argc, char *argv[])
{
    printf("MICROPHONE EXAMPLE\n");
    microphone_demo();
}
