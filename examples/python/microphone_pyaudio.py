# This demo uses PyAudio (https://people.csail.mit.edu/hubert/pyaudio/) to read the microphone audio and TinyKW to detect keywords.
import random
import pyaudio
from tinykw import TkwEngine
import numpy as np
import termcolor
random.seed(1)

def main():
    # Encoding of keywords can be retrieved from https://voyelle.io/tinykw.
    kw_hello_world = [
        0x11, 0xb4, 0x15, 0xc0, 0x54, 0xb6, 0xcc, 0x22,
        0xc5, 0xb6, 0xd6, 0x2e, 0x7a, 0xe3, 0xb9, 0x75,
        0xf6, 0xb6, 0xbc, 0x70, 0xf7, 0x29, 0x3b, 0x14,
        0x67, 0x9a, 0x81, 0x07, 0x93, 0x51, 0xa2, 0x90,
        0x40, 0x74, 0xc9, 0x06, 0xb6, 0x41, 0x6a, 0xf5,
        0x2a, 0xe2, 0x7c, 0x39, 0xfa, 0x9e, 0x5a, 0x92
    ]
    kw_banana_split = [
        0x58, 0xef, 0x25, 0x32, 0x4b, 0x18, 0x95, 0x67,
        0x20, 0x52, 0x85, 0x4b, 0x34, 0x02, 0x7b, 0x9e,
        0x6b, 0x61, 0x8a, 0x17, 0xf9, 0x6f, 0x8c, 0xfd,
        0x8a, 0x7f, 0x2b, 0x1f, 0x49, 0x5b, 0x46, 0x81,
        0xed, 0x3e, 0xdf, 0xc1, 0x5a, 0x98, 0x40, 0x9c,
        0xd0, 0x59, 0xed, 0xdd, 0x6e, 0x3a, 0xa2, 0x56
    ]
    kw_activate = [
        0xb2, 0xfd, 0xa7, 0x25, 0x47, 0xaf, 0x4a, 0xda,
        0x87, 0x6a, 0x99, 0x51, 0x71, 0x1a, 0x9a, 0xdb,
        0x80, 0xa5, 0x9a, 0x53, 0x92, 0x92, 0x49, 0xbc,
        0x50, 0xbf, 0x48, 0x8e, 0xf5, 0xff, 0x1a, 0xb9,
        0x46, 0xce, 0x9f, 0xd1, 0xb7, 0xb2, 0x40, 0xa3,
        0x98, 0xc0, 0x3c, 0x63, 0xde, 0x09, 0x7c, 0x8c
    ]

    keywords = [kw_hello_world, kw_banana_split, kw_activate]
    keywords_names = ["hello world", "banana split", "activate"] # for logging
    colors = random.sample(list(termcolor.COLORS.keys()), len(keywords)) # for logging
    nb_keywords = len(keywords)

    # 1. Initialization of the engine.
    engine = TkwEngine(language="en")

    # 2. Add the keywords to the engine. 
    # add_keyword() returns a unique id associated with the keyword
    keyword_ids = []
    for k in range(nb_keywords):
        kw_id = engine.add_keyword(data=keywords[k], detection_threshold=0.5)
        keyword_ids.append(kw_id)

    # 3. Set the function called when a keyword is detected.
    def on_detection(kw_id: int):
        k = keyword_ids.index(kw_id)
        print(termcolor.colored(f"{keywords_names[k]}", colors[k], attrs=["bold"]), "detected")
    engine.set_callback(on_detection)

    # 4. Read and process microphone's data using Pyaudio.
    p = pyaudio.PyAudio()
    try:
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=engine.frame_size)
        print('Recording...')
        while True:
            data = stream.read(engine.frame_size)
            samples = np.frombuffer(data, dtype=np.int16)
            engine.process_frame(samples) # process one audio frame, on_detection() is called if a keyword is detected
                
    except KeyboardInterrupt:
        print("Stopped by user")
    except Exception as e:
        print("Exception:", e)
    finally:
        print('Done')
        stream.close()
        p.terminate()


if __name__ == "__main__":
    main()
