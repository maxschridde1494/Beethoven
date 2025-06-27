import time
import functools

from app.utils.logger import get_logger

logger = get_logger(__name__)

def benchmark(name: str):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                dt = (time.perf_counter() - t0) * 1000
                logger.info(f"{name} took {dt:.1f} ms")
        return wrapper
    return deco