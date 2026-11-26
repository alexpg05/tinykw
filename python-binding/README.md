# Python binding for TinyKW

## Installation

```
pip install tinykw
```

## Usage

```python
from tinykw import TkwEngine

engine = TkwEngine(language="es")

kw_id = engine.add_keyword(data=kw_bytes, detection_threshold=0.5)
engine.set_callback(lambda keyword_id: print(f"keyword {keyword_id} detected"))
# ... 
engine.process_frame(samples) # calls the callback when a keyword is detected
```

See [examples/python](https://github.com/voyelle-io/tinykw/tree/main/examples/python) for full usage.

## License

TinyKW is licensed under the Apache License 2.0.
Please see [LICENSE](https://github.com/voyelle-io/tinykw/tree/main/LICENSE) for details.
