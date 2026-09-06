#include <stdint.h>

uint32_t test_and_set_lock(uint32_t *word) {
  uint32_t old = __atomic_fetch_or(word, UINT32_C(1) << 31, __ATOMIC_ACQUIRE);
  return old >> 31;
}

uint32_t clear_lock(uint32_t *word) {
  return __atomic_and_fetch(word, 0x7fffffff, __ATOMIC_RELEASE);
}

void increment(uint32_t *word) {
  __atomic_fetch_add(word, 1, __ATOMIC_RELAXED);
}

void decrement(uint32_t *word) {
  __atomic_fetch_sub(word, 1, __ATOMIC_RELAXED);
}

uint32_t load_word(uint32_t *word) {
  return __atomic_load_n(word, __ATOMIC_RELAXED);
}
