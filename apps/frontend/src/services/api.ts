const API_BASE = '/api';

let authToken: string | null = null;

function getHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
  return headers;
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { ...getHeaders(), ...init?.headers } as Record<string, string>,
    ...init,
  });
  if (res.status === 401) {
    localStorage.removeItem('sgip_token');
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.detail || err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  auth: {
    setToken: (t: string | null) => { authToken = t; },
    login: (username: string, password: string) =>
      fetchJson<{ access_token: string; token_type: string; username: string }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      }),
    me: () => fetchJson<{ username: string; role: string }>('/auth/me'),
    verify: () => fetchJson<{ valid: boolean }>('/auth/verify'),
  },
  dmas: {
    list: () => fetchJson<DMA[]>('/dmas/'),
    get: (id: string) => fetchJson<DMA>(`/dmas/${id}`),
    getSensors: (id: string) => fetchJson<Record<string, unknown>>(`/dmas/${id}/sensors`),
    getMetrics: (id: string) => fetchJson<DmaMetrics>(`/dmas/${id}/kpis`),
    getSummary: (id: string) => fetchJson<Record<string, unknown>>(`/dmas/${id}/summary`),
  },
  telemetry: {
    latest: () => fetchJson<TelemetryReading[]>('/telemetry/latest'),
    history: (dmaId: string, hours = 24) => {
      const end = new Date();
      const start = new Date(end.getTime() - hours * 3600 * 1000);
      return fetchJson<any>(`/telemetry/history/${dmaId}?start_date=${start.toISOString()}&end_date=${end.toISOString()}`);
    },
    trends: (dmaId: string) => fetchJson<TelemetryReading[]>(`/telemetry/trends/${dmaId}`),
    mocheLatest: () => fetchJson<TelemetryReading>('/telemetry/moche/latest'),
    mocheTrends: () => fetchJson<TelemetryReading[]>('/telemetry/moche/trends'),
  },
  anomalies: {
    recent: (dmaId?: string) =>
      fetchJson<Record<string, unknown>>(dmaId ? `/anomalies/dma/${dmaId}` : '/anomalies/recent'),
    mocheRecent: () => fetchJson<Record<string, unknown>>('/anomalies/moche/recent'),
    mocheStats: () => fetchJson<Record<string, unknown>>('/anomalies/moche/stats'),
    simulate: () => fetchJson<Record<string, unknown>>('/anomalies/simulate', { method: 'POST' }),
  },
  incidents: {
    list: (dmaId?: string) => {
      const params = dmaId ? `?dma_id=${dmaId}` : '';
      return fetchJson<IncidentTicket[]>(`/incidents/${params}`);
    },
    get: (id: number) => fetchJson<IncidentTicket>(`/incidents/${id}`),
    updateStatus: (id: number, status: string) =>
      fetchJson<IncidentTicket>(`/incidents/${id}/status?status=${status}`, { method: 'PATCH' }),
    slaMetrics: (dmaId?: string) => {
      const endpoint = dmaId ? `/incidents/moche/sla-metrics` : `/incidents/sla/metrics`;
      return fetchJson<Record<string, unknown>>(endpoint);
    },
    checkSlaBreaches: () =>
      fetchJson<Record<string, unknown>>('/incidents/check-sla-breaches', { method: 'POST' }),
    addComment: (id: number, comment: string, user: string = 'operator') =>
      fetchJson<IncidentTicket>(`/incidents/${id}/comment`, {
        method: 'POST',
        body: JSON.stringify({ comment, user, is_internal: false })
      }),
    escalate: (id: number, reason: string = 'Manual escalation') =>
      fetchJson<IncidentTicket>(`/incidents/${id}/escalate?reason=${encodeURIComponent(reason)}`, { method: 'POST' }),
    getAuditLog: (id: number) =>
      fetchJson<Record<string, unknown>[]>(`/incidents/${id}/audit-log`),
  },
  kpis: {
    executive: () => fetchJson<KpiExecutive>('/kpis/executive'),
    mocheExecutive: () => fetchJson<KpiExecutive>('/kpis/moche/executive'),
    dmaMetrics: (dmaId: string) => fetchJson<DmaMetrics>(`/kpis/dma/${dmaId}`),
    waterLoss: () => fetchJson<Record<string, unknown>>('/kpis/water-loss'),
  },
  alerts: {
    list: () => fetchJson<Alert[]>('/alerts/'),
    acknowledge: (id: number) =>
      fetchJson<Alert>(`/alerts/${id}/acknowledge?user=operator`, { method: 'POST' }),
  },
  reports: {
    daily: (date?: string) => fetchJson<Record<string, unknown>>(`/reports/daily${date ? `?date=${date}` : ''}`),
    weekly: () => fetchJson<Record<string, unknown>>('/reports/weekly'),
    mocheDaily: (date?: string) => fetchJson<Record<string, unknown>>(`/reports/moche/daily${date ? `?date=${date}` : ''}`),
    mocheWeekly: () => fetchJson<Record<string, unknown>>('/reports/moche/weekly'),
    mocheCustom: (start: string, end: string) => fetchJson<Record<string, unknown>>(`/reports/moche/custom?start_date=${start}T00:00:00&end_date=${end}T23:59:59`),
    exportReport: (type: 'daily' | 'weekly' | 'custom', format: 'xlsx' | 'pdf', date?: string, start?: string, end?: string) => {
      let query = `?format=${format}`;
      if (type === 'daily' && date) query += `&date=${date}`;
      if (type === 'custom' && start && end) query += `&start_date=${start}T00:00:00&end_date=${end}T23:59:59`;
      return fetchJson<{ content: string; filename: string; format: string }>(`/reports/export/${type}${query}`);
    },
    // New V2 modular endpoints
    getReportV2: (reportType: string, params?: Record<string, string>) => {
      const queryParams = new URLSearchParams(params).toString();
      return fetchJson<Record<string, unknown>>(`/reports/v2/${reportType}${queryParams ? `?${queryParams}` : ''}`);
    },
    exportReportV2: (reportType: string, format: 'xlsx' | 'pdf' | 'csv', date?: string, startDate?: string, endDate?: string) => {
      const params: Record<string, string> = { format };
      if (date) params.date = date;
      if (startDate && endDate) {
        params.start_date = `${startDate}T00:00:00`;
        params.end_date = `${endDate}T23:59:59`;
      }
      const queryParams = new URLSearchParams(params).toString();
      // Return blob for file download
      return fetch(`${API_BASE}/reports/v2/export/${reportType}?${queryParams}`, {
        headers: getHeaders(),
      }).then(res => {
        if (!res.ok) {
          return res.json().catch(() => ({ error: res.statusText })).then(err => { throw new Error(err.detail || err.error || `HTTP ${res.status}`); });
        }
        return res.blob();
      });
    },
    getMocheReportV2: (reportType: string, params?: Record<string, string>) => {
      const queryParams = new URLSearchParams(params).toString();
      return fetchJson<Record<string, unknown>>(`/reports/v2/moche/${reportType}${queryParams ? `?${queryParams}` : ''}`);
    },
  },
};

import type { DMA, Sensor, TelemetryReading, DmaMetrics } from '../types';
import type { IncidentTicket, Alert, KpiExecutive } from '../types';
