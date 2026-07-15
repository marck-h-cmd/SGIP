import { useState, useMemo } from 'react';
import { useIncidents, useUpdateIncidentStatus } from '../../services/hooks';
import StatusBadge, { PriorityBadge } from '../../components/StatusBadge';
import { format } from '../../utils/format';
import { Search, Clock, CheckCircle, XCircle, Loader2, MessageSquare, AlertTriangle, Eye, Edit, ArrowRight } from 'lucide-react';
import clsx from 'clsx';

const statusFilters = ['TODOS', 'NEW', 'CLASSIFIED', 'ASSIGNED', 'IN_PROGRESS', 'ESCALATED', 'RESOLVED', 'CLOSED'];
const priorityFilters = ['TODOS', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

const translateStatus = (s: string) => {
  const map: Record<string, string> = {
    TODOS: 'Todos', NEW: 'Nuevo', CLASSIFIED: 'Clasificado', ASSIGNED: 'Asignado',
    IN_PROGRESS: 'En Progreso', ESCALATED: 'Escalado', RESOLVED: 'Resuelto', CLOSED: 'Cerrado'
  };
  return map[s] || s;
};

const translatePriority = (p: string) => {
  const map: Record<string, string> = { TODOS: 'Todos', CRITICAL: 'Critico', HIGH: 'Alta', MEDIUM: 'Media', LOW: 'Baja' };
  return map[p] || p;
};

const getValidTransitions = (currentStatus: string) => {
  const transitions: Record<string, string[]> = {
    NEW: ['CLASSIFIED', 'CANCELLED'],
    CLASSIFIED: ['ASSIGNED', 'CANCELLED'],
    ASSIGNED: ['IN_PROGRESS', 'CANCELLED'],
    IN_PROGRESS: ['RESOLVED', 'ESCALATED', 'CANCELLED'],
    ESCALATED: ['IN_PROGRESS', 'RESOLVED', 'CANCELLED'],
    RESOLVED: ['CLOSED', 'IN_PROGRESS'],
    CLOSED: [],
    CANCELLED: []
  };
  return transitions[currentStatus] || [];
};

const getTransitionLabel = (from: string, to: string) => {
  const labels: Record<string, Record<string, string>> = {
    NEW: { CLASSIFIED: 'Clasificar', CANCELLED: 'Cancelar' },
    CLASSIFIED: { ASSIGNED: 'Asignar', CANCELLED: 'Cancelar' },
    ASSIGNED: { IN_PROGRESS: 'Iniciar', CANCELLED: 'Cancelar' },
    IN_PROGRESS: { RESOLVED: 'Resolver', ESCALATED: 'Escalar', CANCELLED: 'Cancelar' },
    ESCALATED: { IN_PROGRESS: 'Reanudar', RESOLVED: 'Resolver', CANCELLED: 'Cancelar' },
    RESOLVED: { CLOSED: 'Cerrar', IN_PROGRESS: 'Reabrir' }
  };
  return labels[from]?.[to] || to;
};

const getTransitionIcon = (to: string) => {
  switch (to) {
    case 'RESOLVED': return <CheckCircle className="w-4 h-4" />;
    case 'ESCALATED': return <AlertTriangle className="w-4 h-4" />;
    case 'CLOSED': return <XCircle className="w-4 h-4" />;
    default: return <ArrowRight className="w-4 h-4" />;
  }
};

interface IncidentDetailProps {
  incident: any;
  onClose: () => void;
  onStatusChange: (id: number, status: string) => void;
}

function IncidentDetailModal({ incident, onClose, onStatusChange }: IncidentDetailProps) {
  const [activeTab, setActiveTab] = useState<'details' | 'audit'>('details');
  const validTransitions = getValidTransitions(incident.status);

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <div>
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm text-gray-500">{incident.code}</span>
              <StatusBadge status={incident.status} />
              <PriorityBadge priority={incident.priority} />
            </div>
            <h2 className="text-lg font-bold text-gray-900 mt-1">{incident.title}</h2>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg">
            <XCircle className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        <div className="flex border-b border-gray-100">
          <button onClick={() => setActiveTab('details')}
            className={clsx('px-6 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'details' ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700')}>
            <Eye className="w-4 h-4 inline mr-2" />Detalles
          </button>
          <button onClick={() => setActiveTab('audit')}
            className={clsx('px-6 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'audit' ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700')}>
            <Clock className="w-4 h-4 inline mr-2" />Historial
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {activeTab === 'details' ? (
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Descripcion</h3>
                <p className="text-gray-600 text-sm">{incident.description || 'Sin descripcion'}</p>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div><p className="text-xs text-gray-500 mb-1">DMA</p><p className="font-medium text-gray-900">{incident.dma_name || incident.dma_id}</p></div>
                <div><p className="text-xs text-gray-500 mb-1">Asignado a</p><p className="font-medium text-gray-900">{incident.assigned_to || 'Sin asignar'}</p></div>
                <div><p className="text-xs text-gray-500 mb-1">SLA Due</p>
                  <p className={clsx('font-medium', incident.sla_due_at && new Date(incident.sla_due_at) < new Date() ? 'text-red-600' : 'text-gray-900')}>
                    {incident.sla_due_at ? format.datetime(incident.sla_due_at) : 'Sin definir'}
                  </p></div>
                <div><p className="text-xs text-gray-500 mb-1">Creado</p><p className="font-medium text-gray-900">{format.datetime(incident.created_at)}</p></div>
              </div>
              {incident.anomaly_id && (
                <div className="bg-blue-50 p-4 rounded-xl"><p className="text-sm text-blue-800"><span className="font-semibold">Anomaly ID:</span> {incident.anomaly_id}</p></div>
              )}
              {validTransitions.length > 0 && (
                <div className="border-t border-gray-100 pt-4">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">Acciones ITIL</h3>
                  <div className="flex flex-wrap gap-2">
                    {validTransitions.map((nextStatus) => (
                      <button key={nextStatus}
                        onClick={() => { if (confirm(`Cambiar estado a ${getTransitionLabel(incident.status, nextStatus)}?`)) { onStatusChange(incident.id, nextStatus); onClose(); } }}
                        className={clsx('px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors',
                          nextStatus === 'RESOLVED' && 'bg-green-100 text-green-700 hover:bg-green-200',
                          nextStatus === 'ESCALATED' && 'bg-orange-100 text-orange-700 hover:bg-orange-200',
                          nextStatus === 'CLOSED' && 'bg-gray-100 text-gray-700 hover:bg-gray-200',
                          nextStatus === 'IN_PROGRESS' && 'bg-blue-100 text-blue-700 hover:bg-blue-200',
                          nextStatus === 'CANCELLED' && 'bg-red-100 text-red-700 hover:bg-red-200')}>
                        {getTransitionIcon(nextStatus)}{getTransitionLabel(incident.status, nextStatus)}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {incident.audit_log && incident.audit_log.length > 0 ? (
                <div className="relative">
                  <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>
                  {incident.audit_log.map((log: any, idx: number) => (
                    <div key={idx} className="relative flex gap-4 mb-6">
                      <div className={clsx('w-8 h-8 rounded-full flex items-center justify-center z-10',
                        log.action === 'STATUS_CHANGE' ? 'bg-blue-100' : log.action === 'COMMENT' ? 'bg-green-100' : 'bg-gray-100')}>
                        {log.action === 'STATUS_CHANGE' ? <ArrowRight className="w-4 h-4 text-blue-600" /> :
                         log.action === 'COMMENT' ? <MessageSquare className="w-4 h-4 text-green-600" /> :
                         <Edit className="w-4 h-4 text-gray-600" />}
                      </div>
                      <div className="flex-1 bg-gray-50 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-gray-900">
                            {log.action === 'STATUS_CHANGE' ? `Estado: ${log.old_value} -> ${log.new_value}` :
                             log.action === 'COMMENT' ? 'Comentario' : log.action}
                          </span>
                          <span className="text-xs text-gray-500">{format.datetime(log.timestamp)}</span>
                        </div>
                        {log.user && <p className="text-xs text-gray-500 mb-1">Por: {log.user}</p>}
                        {log.comment && <p className="text-sm text-gray-600 mt-2">{log.comment}</p>}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-400">
                  <Clock className="w-12 h-12 mx-auto mb-3 text-gray-200" />
                  <p className="text-sm">Sin historial de cambios registrado</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function IncidentsPage() {
  const [statusFilter, setStatusFilter] = useState('TODOS');
  const [priorityFilter, setPriorityFilter] = useState('TODOS');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIncident, setSelectedIncident] = useState<any>(null);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const { data: incidents, isLoading } = useIncidents();
  const updateStatus = useUpdateIncidentStatus();

  const list = Array.isArray(incidents) ? incidents : [];
  const filtered = useMemo(() => {
    return list.filter((inc) => {
      if (statusFilter !== 'TODOS' && inc.status !== statusFilter) return false;
      if (priorityFilter !== 'TODOS' && inc.priority !== priorityFilter) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        if (!inc.code.toLowerCase().includes(q) && !inc.title.toLowerCase().includes(q) && !(inc.dma_name || '').toLowerCase().includes(q)) return false;
      }
      return true;
    });
  }, [list, statusFilter, priorityFilter, searchQuery]);

  const paginatedData = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filtered.slice(start, start + pageSize);
  }, [filtered, page, pageSize]);

  const totalPages = Math.ceil(filtered.length / pageSize);
  const activeCount = list.filter((i) => !['RESOLVED', 'CLOSED', 'CANCELLED'].includes(i.status)).length;
  const slaAtRisk = list.filter((i) => i.sla_due_at && new Date(i.sla_due_at) < new Date() && !['RESOLVED', 'CLOSED', 'CANCELLED'].includes(i.status)).length;
  const escalatedCount = list.filter((i) => i.status === 'ESCALATED').length;

  if (isLoading) return (
    <div className="flex items-center justify-center py-20">
      <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="kpi-card"><p className="text-xs text-gray-500">Total</p><p className="text-2xl font-bold text-gray-900">{list.length}</p></div>
        <div className="kpi-card"><p className="text-xs text-gray-500">Activos</p><p className="text-2xl font-bold text-orange-600">{activeCount}</p></div>
        <div className="kpi-card"><p className="text-xs text-gray-500">Escalados</p><p className={clsx('text-2xl font-bold', escalatedCount > 0 ? 'text-orange-600' : 'text-gray-900')}>{escalatedCount}</p></div>
        <div className="kpi-card"><p className="text-xs text-gray-500">SLA Vencido</p><p className={clsx('text-2xl font-bold', slaAtRisk > 0 ? 'text-red-600' : 'text-green-600')}>{slaAtRisk}</p></div>
        <div className="kpi-card"><p className="text-xs text-gray-500">Resueltos</p><p className="text-2xl font-bold text-green-600">{list.filter((i) => i.status === 'RESOLVED' || i.status === 'CLOSED').length}</p></div>
      </div>

      <div className="kpi-card">
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input type="text" placeholder="Buscar por codigo, titulo o DMA..." value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
              className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
          </div>
          <div className="flex gap-2">
            {priorityFilters.map((p) => (
              <button key={p} onClick={() => { setPriorityFilter(p); setPage(1); }}
                className={clsx('px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                  priorityFilter === p ? 'bg-primary-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200')}>
                {translatePriority(p)}</button>
            ))}
          </div>
        </div>
        <div className="flex gap-2 mb-4 flex-wrap">
          {statusFilters.map((s) => (
            <button key={s} onClick={() => { setStatusFilter(s); setPage(1); }}
              className={clsx('px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                statusFilter === s ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200')}>
              {translateStatus(s)}</button>
          ))}
        </div>

        {paginatedData.length === 0 ? (
          <p className="text-sm text-gray-400 py-8 text-center">No se encontraron incidentes</p>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-3 text-gray-500 font-medium">Codigo</th>
                    <th className="text-left py-3 px-3 text-gray-500 font-medium">Titulo</th>
                    <th className="text-left py-3 px-3 text-gray-500 font-medium">DMA</th>
                    <th className="text-left py-3 px-3 text-gray-500 font-medium">Prioridad</th>
                    <th className="text-left py-3 px-3 text-gray-500 font-medium">Estado</th>
                    <th className="text-left py-3 px-3 text-gray-500 font-medium">Asignado</th>
                    <th className="text-left py-3 px-3 text-gray-500 font-medium">SLA</th>
                    <th className="text-left py-3 px-3 text-gray-500 font-medium">Creado</th>
                    <th className="text-left py-3 px-3 text-gray-500 font-medium">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedData.map((inc) => {
                    const slaDate = inc.sla_due_at ? new Date(inc.sla_due_at) : null;
                    const slaExpired = slaDate && slaDate < new Date() && !['RESOLVED', 'CLOSED', 'CANCELLED'].includes(inc.status);
                    const validTransitions = getValidTransitions(inc.status);
                    return (
                      <tr key={inc.id} className="border-b border-gray-50 hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedIncident(inc)}>
                        <td className="py-3 px-3 font-mono text-xs text-gray-700">{inc.code}</td>
                        <td className="py-3 px-3 font-medium text-gray-800">{inc.title}</td>
                        <td className="py-3 px-3 text-gray-600">{inc.dma_name || inc.dma_id}</td>
                        <td className="py-3 px-3"><PriorityBadge priority={inc.priority} /></td>
                        <td className="py-3 px-3"><StatusBadge status={inc.status} /></td>
                        <td className="py-3 px-3 text-gray-600">{inc.assigned_to || '--'}</td>
                        <td className="py-3 px-3">
                          <span className={clsx('flex items-center gap-1 text-xs', slaExpired ? 'text-red-600 font-medium' : 'text-gray-500')}>
                            <Clock className="w-3 h-3" />{slaDate ? format.datetime(inc.sla_due_at) : '--'}{slaExpired && ' !'}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-xs text-gray-500">{format.datetime(inc.created_at)}</td>
                        <td className="py-3 px-3" onClick={(e) => e.stopPropagation()}>
                          <div className="flex gap-1">
                            {validTransitions.slice(0, 3).map((nextStatus) => (
                              <button key={nextStatus}
                                onClick={() => { if (confirm(`Cambiar a ${getTransitionLabel(inc.status, nextStatus)}?`)) updateStatus.mutate({ id: inc.id, status: nextStatus }); }}
                                className={clsx('p-1.5 rounded hover:bg-gray-100',
                                  nextStatus === 'RESOLVED' ? 'text-green-600' : nextStatus === 'ESCALATED' ? 'text-orange-600' : 'text-gray-500')}
                                title={getTransitionLabel(inc.status, nextStatus)}>
                                {getTransitionIcon(nextStatus)}
                              </button>
                            ))}
                            <button onClick={() => setSelectedIncident(inc)}
                              className="p-1.5 rounded hover:bg-gray-100 text-gray-400 hover:text-primary-600" title="Ver detalles">
                              <Eye className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
                <p className="text-xs text-gray-500">Mostrando {(page - 1) * pageSize + 1} a {Math.min(page * pageSize, filtered.length)} de {filtered.length}</p>
                <div className="flex gap-2">
                  <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                    className="px-3 py-1.5 text-xs font-medium bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50">Anterior</button>
                  <span className="px-3 py-1.5 text-xs font-medium text-gray-600">Pagina {page} de {totalPages}</span>
                  <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                    className="px-3 py-1.5 text-xs font-medium bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50">Siguiente</button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {selectedIncident && (
        <IncidentDetailModal incident={selectedIncident} onClose={() => setSelectedIncident(null)}
          onStatusChange={(id, status) => updateStatus.mutate({ id, status })} />
      )}
    </div>
  );
}