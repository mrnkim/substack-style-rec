/**
 * Tiny client-side request cache: TTL eviction + inflight de-duplication.
 *
 * Recommendation endpoints can take tens of seconds (each scene-segment query
 * round-trips to the Twelve Labs Embed API). Caching read results and sharing
 * one promise across concurrent identical requests keeps navigation snappy.
 *
 * Cache keys must encode every parameter that affects the result (including
 * subscriptions / watch history) so that state changes naturally produce a new
 * key and a fresh fetch instead of serving a stale feed.
 */

type Entry<T> = { value: T; expires: number };

const cache = new Map<string, Entry<unknown>>();
const inflight = new Map<string, Promise<unknown>>();

export async function withCache<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttlMs = 300_000, // 5 min
): Promise<T> {
  const now = Date.now();

  const hit = cache.get(key);
  if (hit && hit.expires > now) return hit.value as T;

  const pending = inflight.get(key);
  if (pending) return pending as Promise<T>;

  const promise = fetcher()
    .then((value) => {
      cache.set(key, { value, expires: Date.now() + ttlMs });
      return value;
    })
    .finally(() => {
      inflight.delete(key);
    });

  inflight.set(key, promise);
  return promise;
}
