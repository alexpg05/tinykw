import ctypes
import platform
from pathlib import Path
from typing import Callable

_libs: dict[str, ctypes.CDLL] = {}

# typedef void(*tkw_callback)(uint8_t keyword_id, void* user_ctx);
_TKW_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_uint8, ctypes.c_void_p)

def _load_library(language: str) -> ctypes.CDLL:
    global _libs
    if language in _libs:
        return _libs[language]

    system = platform.system()
    machine = platform.machine()
    arch = {
        "x86_64": "x86_64",
        "AMD64": "x86_64",   
        "arm64": "arm64",
        "ARM64": "arm64",
        "aarch64": "arm64",
    }.get(machine)

    if arch is None:
        raise OSError(f"Unsupported architecture: {machine}")

    lib_dir = Path(__file__).parent / "libs" / language
    if system == "Darwin":
        lib_path = lib_dir / "libtinykw.dylib"
    elif system == "Linux":
        lib_path = lib_dir / "libtinykw.so"
    elif system == "Windows":
        lib_path = lib_dir / "libtinykw.dll"
    else:
        raise OSError(f"Unsupported platform: {system}")

    if not lib_path.exists():
        suported_languages = [x.name for x in (Path(__file__).parent / "libs").iterdir() if x.is_dir()]
        raise OSError(f"Language '{language}' is not supported. Supported languages are {suported_languages}")
    
    lib = ctypes.CDLL(str(lib_path))

    lib.tkw_create.argtypes = []
    lib.tkw_create.restype  = ctypes.c_void_p

    lib.tkw_destroy.argtypes = [ctypes.c_void_p]
    lib.tkw_destroy.restype  = None

    lib.tkw_set_callback.argtypes = [_TKW_CALLBACK,
                                     ctypes.c_void_p,
                                     ctypes.c_void_p]
    lib.tkw_set_callback.restype  = ctypes.c_int32

    lib.tkw_add_keyword.argtypes = [ctypes.POINTER(ctypes.c_uint8), 
                                    ctypes.c_uint8, 
                                    ctypes.POINTER(ctypes.c_uint8),
                                    ctypes.c_void_p]
    lib.tkw_add_keyword.restype  = ctypes.c_int32

    lib.tkw_remove_keyword.argtypes = [ctypes.c_uint8,
                                       ctypes.c_void_p]
    lib.tkw_remove_keyword.restype  = ctypes.c_int32

    lib.tkw_process_frame.argtypes = [ctypes.POINTER(ctypes.c_int16),
                                        ctypes.c_size_t,
                                        ctypes.c_void_p]
    lib.tkw_process_frame.restype  = ctypes.c_int32

    lib.tkw_status_string.argtypes = [ctypes.c_int32]
    lib.tkw_status_string.restype = ctypes.c_char_p

    _libs[language] = lib
    return _libs[language]


AUDIO_FRAME_SIZE = 480

class tkwError(RuntimeError):
    pass

class TkwEngine:
    def __init__(self, language):
        self._lib = _load_library(language)
        self._ctx = self._lib.tkw_create()
        if not self._ctx:
            raise MemoryError("tkw_create failed")
        self.frame_size = AUDIO_FRAME_SIZE

    def set_callback(self, callback: Callable[[int], None] | None) -> None:
        """
        Sets the function called when a keyword is detected.

        Args:
            callback: function taking the ID of the detected keyword (as returned by add_keyword()),
                or None to remove the callback. It is called from within process_frame().
                It is important to keep the callback short.

        Example:
            engine.set_callback(lambda keyword_id: print(f"keyword {keyword_id} detected"))
        """
        self._c_callback = _TKW_CALLBACK(lambda keyword_id, user_ctx: callback(keyword_id)) if callback else _TKW_CALLBACK()
        status = self._lib.tkw_set_callback(self._c_callback, None, self._ctx)
        self._check_status(status)
    
    def add_keyword(self, data: list[int] | bytes, detection_threshold: float = 0.5) -> int:
        """
        Adds a keyword to the engine.

        Args:
            data: 48 bytes keyword encoding (can be obtained from https://voyelle.io/tinykw).
            detection_threshold: value between 0 and 1. 
                Controls how strict the engine is when deciding whether a detection is valid.
                A high value makes the engine more conservative: only high-scoring detections are accepted (fewer false positives, but more missed detections).
                A low value makes the engine more permissive: more detections are accepted (fewer misses, but more false positives).
                This parameter may need tuning depending on the keyword, use case and environment. A good starting point is to set it mid-range at 0.5, and 
                then eventually adjust it based on your tolerance for false positives vs missed detections.
        
        Returns:
            id: the assigned keyword ID

        Example:
            data = [0x3f, 0x12, 0x00, ...]  # 48 bytes
            id = engine.add_keyword(data, 0.75)
        """
        if isinstance(data, bytes):
            data = list(data)
        if len(data) != 48:
            raise ValueError(f"data must be exactly 48 bytes, got {len(data)}")
        if not (0.0 <= detection_threshold <= 1.0):
            raise ValueError("detection_threshold must be in [0.0, 1.0]")
        detection_threshold = max(0, min(255, round(detection_threshold * 256)))
        c_data = (ctypes.c_uint8 * 48)(*data)
        out_id = ctypes.c_uint8()
        status = self._lib.tkw_add_keyword(c_data, 
                                    ctypes.c_uint8(detection_threshold), 
                                    ctypes.byref(out_id), 
                                    self._ctx)
        self._check_status(status)
        return out_id.value

    def remove_keyword(self, keyword_id: int) -> None:
        """
        Removes a keyword from the engine.

        Args:
            keyword_id: keyword ID, as returned by add_keyword().
        """
        status = self._lib.tkw_remove_keyword(ctypes.c_uint8(keyword_id), self._ctx)
        self._check_status(status)
    
    def process_frame(self, waveform) -> None:
        """
        Processes one frame of 16-bit PCM audio sampled at 16 kHz.
        The callback set with set_callback() is called for each detected keyword.

        Args:
            waveform: int16 numpy array or list of length self.frame_size.
        """
        if len(waveform) != self.frame_size:
            raise ValueError(
                f"waveform must have length {self.frame_size}, got {len(waveform)}"
            )
        if hasattr(waveform, "ctypes"):
            ptr = waveform.ctypes.data_as(ctypes.POINTER(ctypes.c_int16))
        else:
            arr = (ctypes.c_int16 * len(waveform))(*waveform)
            ptr = arr
        status = self._lib.tkw_process_frame(ptr, len(waveform), self._ctx)
        self._check_status(status)

    def _check_status(self, status: int):
        if status != 0:
            msg = self._lib.tkw_status_string(status)
            msg = msg.decode() if msg else f"Error code {status}"
            raise tkwError(msg)
        
    def close(self):
        ctx = getattr(self, '_ctx', None)
        if ctx:
            self._lib.tkw_destroy(self._ctx)

    def __del__(self):
        self.close()
