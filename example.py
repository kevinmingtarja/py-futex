from concurrent.futures import ThreadPoolExecutor
import time

from mutex import Mutex


def main():
    mutex = Mutex()
    counter = 0
    iterations = 100

    def increment():
        nonlocal counter
        for _ in range(iterations):
            with mutex:
                value = counter
                # Yield while holding the lock so the other thread can contend.
                time.sleep(0.001)
                counter = value + 1

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(increment) for _ in range(2)]
        for future in futures:
            future.result()

    expected = 2 * iterations
    print(f"Counter: {counter} (expected {expected})")
    assert counter == expected


if __name__ == "__main__":
    main()
