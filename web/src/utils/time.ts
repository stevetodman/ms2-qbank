export function formatSeconds(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return '—';
  }
  const total = Math.max(0, Math.floor(value));
  const minutes = Math.floor(total / 60)
    .toString()
    .padStart(2, '0');
  const seconds = (total % 60).toString().padStart(2, '0');
  return `${minutes}:${seconds}`;
}
