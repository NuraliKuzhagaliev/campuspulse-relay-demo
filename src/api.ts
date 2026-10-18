let csrf = "";
const reads = new Map<string, Promise<unknown>>();
export function setCsrf(value: string) {
  csrf = value;
  reads.clear();
}
export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  if (method === "GET") {
    const pending = reads.get(path);
    if (pending) return pending as Promise<T>;
    const promise = request<T>(path, method, body).finally(() =>
      reads.delete(path),
    );
    reads.set(path, promise);
    return promise;
  }
  return request<T>(path, method, body);
}
async function request<T>(
  path: string,
  method: string,
  body?: unknown,
): Promise<T> {
  if (window.relay)
    return (await window.relay.request("/api" + path, method, body)) as T;
  const form = body instanceof FormData;
  const response = await fetch("/api" + path, {
    method,
    credentials: "same-origin",
    signal: AbortSignal.timeout(110000),
    headers: {
      ...(!form && body ? { "Content-Type": "application/json" } : {}),
      ...(method !== "GET" ? { "X-Relay-CSRF": csrf } : {}),
    },
    body: body ? (form ? (body as FormData) : JSON.stringify(body)) : undefined,
  });
  const value = await response.json().catch(() => {
    throw new Error(
      "UPSTREAM_UNAVAILABLE: The gateway returned an unreadable response. Retry after reconnecting.",
    );
  });
  if (!response.ok)
    throw Object.assign(
      new Error(
        `${value.error?.code || "REQUEST_FAILED"}: ${value.error?.message || "The request could not be completed."}`,
      ),
      { status: response.status },
    );
  return value as T;
}
