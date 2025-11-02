export function resolveEnv(key: string, fallback: string): string {
  const fromWindow =
    typeof window !== 'undefined' && (window as typeof window & { __APP_CONFIG__?: Record<string, unknown> }).__APP_CONFIG__;
  if (fromWindow && typeof fromWindow[key] === 'string') {
    return fromWindow[key] as string;
  }

  try {
    const meta = (Function('return import.meta')() as ImportMeta | undefined)?.env as
      | Record<string, unknown>
      | undefined;
    const value = meta?.[key];
    if (typeof value === 'string') {
      return value;
    }
  } catch {
    // Swallow errors when running in non-Vite environments (tests, SSR).
  }

  if (typeof process !== 'undefined' && typeof process.env?.[key] === 'string') {
    return process.env[key] as string;
  }

  return fallback;
}

export function getBaseUrl(): string {
  return resolveEnv('VITE_API_BASE_URL', 'http://localhost:8000');
}
