import gc
import logging

logger = logging.getLogger("bel_chatbot.memory")


def trim_process_memory() -> None:
    """
    Forces Python garbage collection and invokes glibc malloc_trim on Linux.
    Releases unused heap arenas back to the Linux kernel to protect against
    cgroup memory limit kills in 512MB RAM cloud environments (Render Free).
    """
    gc.collect()
    try:
        import ctypes
        import ctypes.util

        c_lib = ctypes.util.find_library("c")
        if c_lib:
            libc = ctypes.CDLL(c_lib)
            if hasattr(libc, "malloc_trim"):
                libc.malloc_trim(0)
    except Exception as e:
        logger.debug(f"malloc_trim call omitted: {e}")
