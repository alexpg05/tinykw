![Workflow Status](https://github.com/voyelle-io/tinykw/actions/workflows/github-actions.yml/badge.svg)

# TinyKW

TinyKW ("Tiny Keyword") is a lightweight, configurable, keyword spotting engine. 

It can be used for Wake word detection and Voice commands, on cortex-M MCUs, ESP32, Raspberry Pi and desktops.

## Installation

Precompiled binaries and headers are available under [libs/](libs/).

A Python binding that closely follows the C API is also available at [python-binding](python-binding/).

## Usage

Before use, keywords must be encoded using the [web encoder](https://voyelle.io/tinykw). The encoder outputs a binary representation ready to paste directly into the C or Python code.

```C
#include "tinykw.h"

void on_detection(uint8_t kw_id, void* user_ctx)
{
    // called when a keyword is detected
}

tkw_context ctx;
tkw_status status = tkw_init(&ctx);

uint8_t kw_id;
status = tkw_add_keyword(keyword_bytes, detection_threshold, &kw_id, &ctx);
status = tkw_set_callback(on_detection, NULL, &ctx);
// ...
status = tkw_process_frame(samples, size, &ctx); // calls on_detection() when a keyword is detected
```

See [examples/C](examples/C/) and [examples/Python](examples/python/) for full examples.

## Projects using TinyKW

* [wyoming-tinykw](https://github.com/Yamawine408/wyoming-tinykw): Wake word detection for Home Assistant Wyoming Protocol.
* [stm32f411-voice-interaction](https://github.com/voyelle-io/stm32f411-voice-interaction): Voice interaction on NUCLEO-STM32F411 board.

## License

TinyKW is licensed under the Apache License 2.0.
Please see [LICENSE](LICENSE) for details.