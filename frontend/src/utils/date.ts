export function format(isoString: string): string {
  try {
    const d = new Date(isoString);
    return d.toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
  } catch {
    return isoString;
  }
}

export function formatDate(isoString: string): string {
  try {
    return new Date(isoString).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  } catch {
    return isoString;
  }
}
