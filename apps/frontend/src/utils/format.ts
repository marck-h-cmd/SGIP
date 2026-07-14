export const format = {
  datetime: (iso: string | undefined | null): string => {
    if (!iso) return '--';
    // Ensure the string is treated as UTC (append 'Z' if no timezone info)
    const utcStr = iso.endsWith('Z') || iso.includes('+') ? iso : iso + 'Z';
    const d = new Date(utcStr);
    return d.toLocaleString('es-PE', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  },
  date: (iso: string | undefined | null): string => {
    if (!iso) return '--';
    const utcStr = iso.endsWith('Z') || iso.includes('+') ? iso : iso + 'Z';
    const d = new Date(utcStr);
    return d.toLocaleDateString('es-PE', {
      day: '2-digit', month: '2-digit', year: 'numeric',
    });
  },
  number: (n: number | undefined | null, decimals = 2): string => {
    if (n === null || n === undefined) return '--';
    return n.toLocaleString('es-PE', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  },
};
