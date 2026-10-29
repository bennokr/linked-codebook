const sorted = (_key: string, value: unknown): unknown =>
  value !== null && typeof value === 'object' && !Array.isArray(value)
    ? Object.fromEntries(Object.entries(value).sort(([a], [b]) => (a < b ? -1 : 1)))
    : value;

/** JSON with sorted keys and two-space indentation, so that every implementation prints the same text. */
export function canonical(value: unknown): string {
  return `${JSON.stringify(value, sorted, 2)}\n`;
}
