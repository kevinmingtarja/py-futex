# Python futex lock

An educational mutex implementation in python using Linux [futex](https://man7.org/linux/man-pages/man2/futex.2.html) with
atomic operations written in C. Requires Linux x86-64. Mostly handwritten, with some assistance from Codex.

Inspired by section 28.15 of https://pages.cs.wisc.edu/~remzi/OSTEP/threads-locks.pdf.

For a brief overview of futex: https://eli.thegreenplace.net/2018/basics-of-futexes.

## Testing

```sh
docker run --rm --platform linux/amd64 \
  -v "$PWD:/work" -w /work py-futex:local \
  bash -c 'clang -O2 -shared -fPIC atomics.c -o atomics.so && python3 example.py'
```

The example uses two threads to increment a shared counter. Expected output: `Counter: 200 (expected 200)`.
