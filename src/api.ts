let csrf = "";
export function setCsrf(value: string) {
  csrf = value;
}
export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  if (window.relay)
    return (await window.relay.request("/api" + path, method, body)) as T;
  const form = body instanceof FormData;
  const response = await fetch("/api" + path, {
    method,
    credentials: "same-origin",
    headers: {
      ...(!form && body ? { "Content-Type": "application/json" } : {}),
      ...(method !== "GET" ? { "X-Relay-CSRF": csrf } : {}),
    },
    body: body ? (form ? (body as FormData) : JSON.stringify(body)) : undefined,
  });
  const value = await response.json();
  if (!response.ok)
    throw Object.assign(
      new Error(
        `${value.error?.code || "REQUEST_FAILED"}: ${value.error?.message || "The request could not be completed."}`,
      ),
      { status: response.status },
    );
  return value as T;
}
