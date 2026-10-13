// Promise cache for per-genome shards: concurrent callers share one fetch, failures are retried.
export function createShardCache(load) {
  const cache = new Map();
  return (key) => {
    if (!cache.has(key)) {
      cache.set(
        key,
        load(key).catch((error) => {
          cache.delete(key);
          throw error;
        })
      );
    }
    return cache.get(key);
  };
}
