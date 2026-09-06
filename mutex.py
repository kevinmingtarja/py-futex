import ctypes
from pathlib import Path

# syscall number for x86_64, varies by architecture
SYS_futex = 202

# Futex operations
FUTEX_WAIT = 0
FUTEX_WAKE = 1

# TODO: pass in _PRIVATE variant if futex is only used
# between threads of the same process.
# This allows the kernel to make some additional
# performance optimizations.
FUTEX_PRIVATE_FLAG = 0x0080
FUTEX_WAIT_PRIVATE = FUTEX_WAIT | FUTEX_PRIVATE_FLAG
FUTEX_WAKE_PRIVATE = FUTEX_WAKE | FUTEX_PRIVATE_FLAG


EAGAIN = 11

libc = ctypes.CDLL(None, use_errno=True)

def futex_wait(uaddr, val):
    """
    This operation tests that the value at the futex word pointed to
    by the address uaddr still contains the expected value val, and if
    so, then sleeps waiting for a FUTEX_WAKE(2const) operation on the
    futex word.

    https://man7.org/linux/man-pages/man2/FUTEX_WAIT.2const.html
    """
    # long syscall(SYS_futex, uint32_t *uaddr, FUTEX_WAIT, uint32_t val,
    #              const struct timespec *_Nullable timeout);
    res = libc.syscall(SYS_futex, ctypes.byref(uaddr), FUTEX_WAIT, val, None, None, 0)
    if res == -1:
        err = ctypes.get_errno()
        if err != EAGAIN:
            raise OSError(err, "futex wait failed")
        # If the futex value does not match val, then the call
        # fails immediately with EAGAIN, in which case
        # we shouldn't error, we simply don't sleep at all.
        # This is to prevent lost wake-ups:
        #        A                 B
        # t0                    read v = 1 (locked)
        # t1  v = 0 (unlock)
        # t2  FUTEX_WAKE
        # t3                   FUTEX_WAIT(v, 1) -> EAGAIN
    return res


def futex_wake(uaddr):
    """
    This operation wakes a single waiter that is waiting (e.g., inside FUTEX_WAIT(2const))
    on the futex word at the address uaddr.

    https://man7.org/linux/man-pages/man2/FUTEX_WAKE.2const.html
    """
    # long syscall(SYS_futex, uint32_t *uaddr, FUTEX_WAKE, uint32_t val);
    # we hardcode val = 1 to just wake up a single waiter
    res = libc.syscall(SYS_futex, ctypes.byref(uaddr), FUTEX_WAKE, 1)
    if res == -1:
        err = ctypes.get_errno()
        raise OSError(err, "futex wake failed")
    return res

atomics = ctypes.CDLL(str(Path(__file__).resolve().with_name("atomics.so")))
WordPtr = ctypes.POINTER(ctypes.c_uint32)

atomics.atomic_test_and_set_lock.argtypes = [WordPtr]
atomics.atomic_test_and_set_lock.restype = ctypes.c_uint32

atomics.atomic_clear_lock.argtypes = [WordPtr]
atomics.atomic_clear_lock.restype = ctypes.c_uint32

atomics.atomic_increment.argtypes = [WordPtr]
atomics.atomic_increment.restype = None  # C void

atomics.atomic_decrement.argtypes = [WordPtr]
atomics.atomic_decrement.restype = None

atomics.atomic_load_word.argtypes = [WordPtr]
atomics.atomic_load_word.restype = ctypes.c_uint32

class Mutex:
    def __init__(self):
        # Use a single uint32 to track both whether the lock is held or not (the high bit)
        # and the number of waiters on the lock (all other bits).
        self._mutex = ctypes.c_uint32(0)
        self._word = ctypes.byref(self._mutex)

    def lock(self):
        # fast path, we got the mutex
        if atomics.atomic_test_and_set_lock(self._word) == 0:
            return
        
        atomics.atomic_increment(self._word)
        while True:
            if atomics.atomic_test_and_set_lock(self._word) == 0:
                atomics.atomic_decrement(self._word)
                return

            v = atomics.atomic_load_word(self._word)
            if v & (1 << 31) == 0:
                # unlocked (high bit is unset)
                continue
            futex_wait(self._mutex, v)

    
    def release(self):
        if atomics.atomic_clear_lock(self._word) == 0:
            # if result is 0, it means there are not other
            # waiting threads
            return
        futex_wake(self._mutex)

