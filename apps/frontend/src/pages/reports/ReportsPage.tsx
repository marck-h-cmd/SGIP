import { useState } from 'react';
import { useDailyReport, useWeeklyReport, useCustomReport } from '../../services/hooks';
import { api } from '../../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, AreaChart, Area } from 'recharts';
import { FileText, Download, Calendar, Loader2, TrendingUp, AlertTriangle, Droplets, CheckCircle, FileSpreadsheet, Clock, Settings } from 'lucide-react';
import clsx from 'clsx';

type Tab = 'daily' | 'weekly' | 'custom';
type ExportFormat = 'xlsx' | 'pdf' | 'csv';

export default function ReportsPage() {
  const [tab, setTab] = useState<Tab>('daily');
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [customStart, setCustomStart] = useState(new Date(Date.now() - 7 * 86400000).toISOString().slice(0, 10));
  const [customEnd, setCustomEnd] = useState(new Date().toISOString().slice(0, 10));
  const [generateCustom, setGenerateCustom] = useState(false);
  const [exportingFormat, setExportingFormat] = useState<ExportFormat | null>(null);
  const [exportProgress, setExportProgress] = useState<number | null>(null);

  const { data: daily, isLoading: dailyLoading } = useDailyReport(date);
  const { data: weekly, isLoading: weeklyLoading } = useWeeklyReport();
  const { data: custom, isLoading: customLoading } = useCustomReport(generateCustom ? customStart : '', generateCustom ? customEnd : '');
  
  const isLoading = (tab === 'daily' && dailyLoading) || (tab === 'weekly' && weeklyLoading) || (tab === 'custom' && customLoading);

  // Date validation
  const isDateValid = (dateStr: string) => {
    const date = new Date(dateStr);
    return !isNaN(date.getTime()) && date <= new Date();
  };

  const isCustomRangeValid = () => {
    const start = new Date(customStart);
    const end = new Date(customEnd);
    const diffDays = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
    return start <= end && diffDays <= 90 && isDateValid(customStart) && isDateValid(customEnd);
  };

  const handleExport = async (type: Tab, format: ExportFormat) => {
    try {
      setExportingFormat(format);
      setExportProgress(0);
      
      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setExportProgress(prev => {
          if (prev !== null && prev < 90) {
            return prev + 10;
          }
          return prev;
        });
      }, 200);

      let blob: Blob;
      if (type === 'daily') {
        blob = await api.reports.exportReportV2('daily', format, date);
      } else if (type === 'weekly') {
        blob = await api.reports.exportReportV2('weekly', format);
      } else {
        blob = await api.reports.exportReportV2('custom', format, undefined, customStart, customEnd);
      }
      
      clearInterval(progressInterval);
      setExportProgress(100);
      
      // Download file - blob returned directly from API
      // Note: We can't extract filename from headers since we only get the blob
      let filename = `${type}_report.${format}`;
      
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (e) {
      console.error('Error exporting report:', e);
      alert('Hubo un error al exportar el reporte. Por favor, inténtelo de nuevo.');
    } finally {
      setExportingFormat(null);
      setTimeout(() => setExportProgress(null), 1000);
    }
  };

  const dailyChart = daily?.readings?.length
    ? daily.readings.slice(-24).map((r: any) => ({
        time: new Date(r.timestamp).toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }),
        presion: r.pressure_mca,
        caudal: r.flow_lps,
      }))
    : [];

  const weeklyChart = weekly?.daily_stats?.length
    ? weekly.daily_stats.map((d: any) => ({
        dia: new Date(d.date).toLocaleDateString('es-PE', { weekday: 'short', day: 'numeric' }),
        presion: d.avg_pressure,
        caudal: d.avg_flow,
      }))
    : [];

  const tabs: { key: Tab; label: string; icon: any }[] = [
    { key: 'daily', label: 'Reporte Diario', icon: Calendar },
    { key: 'weekly', label: 'Reporte Semanal', icon: TrendingUp },
    { key: 'custom', label: 'Personalizado', icon: Settings },
  ];

  return (
    <div className="space-y-8 animate-fade-in max-w-6xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Centro de Reportes</h1>
          <p className="text-sm text-gray-500 mt-1">Análisis detallado, históricos y exportación de datos del sector</p>
        </div>
        
        <div className="flex p-1 bg-gray-100 rounded-xl shadow-inner w-full md:w-auto">
          {tabs.map((t) => (
            <button key={t.key} onClick={() => setTab(t.key)}
              className={clsx('flex-1 md:flex-none px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 flex items-center justify-center gap-2',
                tab === t.key 
                  ? 'bg-white text-primary-600 shadow-sm ring-1 ring-black/5' 
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-200/50'
              )}>
              <t.icon className="w-4 h-4" />
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'daily' && (
        <div className="space-y-6">
          <div className="flex items-center gap-3 bg-white p-4 rounded-xl shadow-sm border border-gray-100 w-full md:w-max">
            <Calendar className="w-5 h-5 text-primary-500" />
            <div className="flex flex-col">
              <label className="text-xs text-gray-400 font-medium">Fecha del Reporte</label>
              <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
                max={new Date().toISOString().slice(0, 10)}
                className="text-sm font-medium text-gray-800 bg-transparent border-none p-0 focus:ring-0 cursor-pointer outline-none" />
            </div>
          </div>

          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-24 bg-white/50 rounded-2xl border border-gray-100 border-dashed">
              <Loader2 className="w-10 h-10 animate-spin text-primary-500 mb-4" />
              <p className="text-gray-500 font-medium">Generando reporte diario...</p>
            </div>
          ) : daily ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1 space-y-6">
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 relative overflow-hidden group">
                  <div className="absolute top-0 right-0 p-4 opacity-10 transform translate-x-4 -translate-y-4 group-hover:scale-110 transition-transform">
                    <Droplets className="w-24 h-24 text-primary-500" />
                  </div>
                  <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-6">Métricas Principales</h3>
                  
                  <div className="space-y-6">
                    <div>
                      <p className="text-xs text-gray-500 mb-1 flex items-center gap-1.5"><TrendingUp className="w-3.5 h-3.5 text-blue-500"/> Presión Promedio</p>
                      <p className="text-3xl font-black text-gray-900">{daily.summary?.avg_pressure ?? '--'} <span className="text-lg font-medium text-gray-400">MCA</span></p>
                    </div>
                    
                    <div className="h-px w-full bg-gray-100"></div>
                    
                    <div>
                      <p className="text-xs text-gray-500 mb-1 flex items-center gap-1.5"><Droplets className="w-3.5 h-3.5 text-cyan-500"/> Caudal Promedio</p>
                      <p className="text-3xl font-black text-gray-900">{daily.summary?.avg_flow ?? '--'} <span className="text-lg font-medium text-gray-400">LPS</span></p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white rounded-2xl p-5 shadow-sm border border-orange-100 bg-gradient-to-br from-white to-orange-50/30">
                    <AlertTriangle className="w-6 h-6 text-orange-500 mb-3" />
                    <p className="text-2xl font-bold text-orange-600 mb-1">{daily.anomalies?.total ?? 0}</p>
                    <p className="text-xs text-gray-600 font-medium">Anomalías</p>
                  </div>
                  <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
                    <FileText className="w-6 h-6 text-gray-400 mb-3" />
                    <p className="text-2xl font-bold text-gray-900 mb-1">{daily.incidents?.total ?? 0}</p>
                    <p className="text-xs text-gray-600 font-medium">Incidentes</p>
                  </div>
                </div>
              </div>

              <div className="lg:col-span-2 bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-sm font-bold text-gray-800">Evolución Diaria (Últimas 24h)</h3>
                  <div className="flex gap-4">
                    <span className="flex items-center text-xs text-gray-500"><span className="w-2 h-2 rounded-full bg-[#0d6ebd] mr-2"></span> Presión</span>
                    <span className="flex items-center text-xs text-gray-500"><span className="w-2 h-2 rounded-full bg-[#0ea5e9] mr-2"></span> Caudal</span>
                  </div>
                </div>
                
                {dailyChart.length > 0 ? (
                  <ResponsiveContainer width="100%" height={320}>
                    <AreaChart data={dailyChart} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorPresion" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#0d6ebd" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#0d6ebd" stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="colorCaudal" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                      <XAxis dataKey="time" fontSize={11} tickLine={false} axisLine={false} tickMargin={10} minTickGap={30} />
                      <YAxis fontSize={11} tickLine={false} axisLine={false} tickMargin={10} />
                      <Tooltip 
                        contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}
                        itemStyle={{ fontSize: '12px', fontWeight: 600 }}
                        labelStyle={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}
                      />
                      <Area type="monotone" dataKey="presion" stroke="#0d6ebd" strokeWidth={2} fillOpacity={1} fill="url(#colorPresion)" name="Presión (MCA)" />
                      <Area type="monotone" dataKey="caudal" stroke="#0ea5e9" strokeWidth={2} fillOpacity={1} fill="url(#colorCaudal)" name="Caudal (LPS)" />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[320px] flex flex-col items-center justify-center text-gray-400">
                    <Calendar className="w-12 h-12 mb-3 text-gray-200" />
                    <p className="text-sm">Sin datos para esta fecha</p>
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>
      )}

      {tab === 'weekly' && (
        <div className="space-y-6">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-24 bg-white/50 rounded-2xl border border-gray-100 border-dashed">
              <Loader2 className="w-10 h-10 animate-spin text-primary-500 mb-4" />
              <p className="text-gray-500 font-medium">Generando reporte semanal...</p>
            </div>
          ) : weekly ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1 space-y-4">
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                  <h3 className="text-sm font-bold text-gray-800 mb-5">Resumen de la Semana</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center p-3 bg-gray-50 rounded-xl">
                      <span className="text-sm text-gray-500">Lecturas Totales</span>
                      <span className="text-lg font-bold text-gray-900">{weekly.total_readings ?? 0}</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-orange-50 text-orange-800 rounded-xl">
                      <span className="text-sm">Anomalías Detectadas</span>
                      <span className="text-lg font-bold">{weekly.total_anomalies ?? 0}</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-gray-50 rounded-xl">
                      <span className="text-sm text-gray-500">Nuevos Incidentes</span>
                      <span className="text-lg font-bold text-gray-900">{weekly.total_incidents ?? 0}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl p-6 shadow-lg text-white relative overflow-hidden">
                  <Droplets className="absolute right-[-20px] top-[-20px] w-32 h-32 text-white opacity-10" />
                  <p className="text-blue-100 text-sm font-medium mb-1">Volumen de Pérdida Estimada</p>
                  <p className="text-4xl font-black mb-1">
                    {weekly?.water_loss_estimate != null && weekly.water_loss_estimate !== undefined
                      ? `${Number(weekly.water_loss_estimate).toFixed(2)}`
                      : '0.00'}
                    <span className="ml-1 text-xl font-medium opacity-80">m³</span>
                  </p>
                  <p className="text-xs text-blue-200 mt-4 bg-black/10 inline-block px-2 py-1 rounded">Basado en algoritmos de ML</p>
                </div>
              </div>

              <div className="lg:col-span-2 bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="text-sm font-bold text-gray-800 mb-6">Promedios y Comportamiento Diario</h3>
                {weeklyChart.length > 0 ? (
                  <ResponsiveContainer width="100%" height={320}>
                    <BarChart data={weeklyChart} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                      <XAxis dataKey="dia" fontSize={11} tickLine={false} axisLine={false} tickMargin={10} />
                      <YAxis fontSize={11} tickLine={false} axisLine={false} tickMargin={10} />
                      <Tooltip 
                        cursor={{fill: '#f8fafc'}}
                        contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}
                      />
                      <Bar dataKey="presion" fill="#0d6ebd" radius={[4, 4, 0, 0]} name="Presión (MCA)" maxBarSize={40} />
                      <Bar dataKey="caudal" fill="#0ea5e9" radius={[4, 4, 0, 0]} name="Caudal (LPS)" maxBarSize={40} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[320px] flex flex-col items-center justify-center text-gray-400">
                    <p className="text-sm">Sin datos semanales</p>
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>
      )}

      {tab === 'custom' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
            <div className="flex flex-col md:flex-row items-center gap-8">
              <div className="flex-1 text-center md:text-left">
                <div className="w-12 h-12 bg-primary-50 rounded-xl flex items-center justify-center mb-4 mx-auto md:mx-0">
                  <FileText className="w-6 h-6 text-primary-600" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Reporte Analítico a Medida</h3>
                <p className="text-sm text-gray-500 max-w-md">
                  Define un intervalo temporal para extraer indicadores agregados, resolver auditorías o presentar resultados de gestión hídrica.
                </p>
              </div>
              
              <div className="flex-1 w-full bg-gray-50 p-6 rounded-2xl border border-gray-100">
                <div className="flex flex-col gap-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-gray-600 mb-1.5 uppercase tracking-wide">Fecha Inicial</label>
                      <input type="date" value={customStart} onChange={e => { setCustomStart(e.target.value); setGenerateCustom(false); }} 
                        max={new Date().toISOString().slice(0, 10)}
                        className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 outline-none transition-all" />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-600 mb-1.5 uppercase tracking-wide">Fecha Final</label>
                      <input type="date" value={customEnd} onChange={e => { setCustomEnd(e.target.value); setGenerateCustom(false); }} 
                        max={new Date().toISOString().slice(0, 10)}
                        className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 outline-none transition-all" />
                    </div>
                  </div>
                  
                  {!isCustomRangeValid() && (customStart || customEnd) && (
                    <div className="text-xs text-red-500 bg-red-50 p-2 rounded-lg">
                      {new Date(customStart) > new Date(customEnd) && "La fecha de inicio debe ser anterior a la fecha final."}
                      {(new Date(customEnd).getTime() - new Date(customStart).getTime()) / (1000 * 60 * 60 * 24) > 90 && "El rango no puede exceder 90 días."}
                    </div>
                  )}
                  
                  <button onClick={() => setGenerateCustom(true)} 
                    disabled={!isCustomRangeValid()}
                    className="w-full py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-xl text-sm font-bold shadow-md shadow-primary-500/20 flex items-center justify-center gap-2 transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed">
                    Generar Análisis de Datos
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          {isLoading && (
            <div className="flex flex-col items-center justify-center py-20 bg-white/50 rounded-2xl border border-gray-100 border-dashed">
              <Loader2 className="w-10 h-10 animate-spin text-primary-500 mb-4" />
              <p className="text-gray-500 font-medium">Recopilando datos y calculando métricas...</p>
            </div>
          )}
          
          {generateCustom && custom && !isLoading && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-fade-in">
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-6 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" /> Resultados del Periodo
                </h3>
                <div className="grid grid-cols-2 gap-y-8 gap-x-4">
                  <div>
                    <p className="text-xs text-gray-500 mb-1 font-medium">Total Lecturas</p>
                    <p className="text-2xl font-bold text-gray-900">{custom.statistics?.total_readings?.toLocaleString() ?? 0}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1 font-medium">Anomalías Detectadas</p>
                    <p className="text-2xl font-bold text-orange-600">{custom.statistics?.anomalies_detected?.toLocaleString() ?? 0}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1 font-medium">Presión Promedio (Total)</p>
                    <p className="text-2xl font-bold text-gray-900">{custom.statistics?.avg_pressure ?? 0} <span className="text-sm text-gray-400 font-normal">MCA</span></p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1 font-medium">Caudal Promedio (Total)</p>
                    <p className="text-2xl font-bold text-gray-900">{custom.statistics?.avg_flow ?? 0} <span className="text-sm text-gray-400 font-normal">LPS</span></p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-6 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-500" /> Gestión de Mantenimiento
                </h3>
                <div className="h-full flex flex-col justify-center gap-6 pb-6">
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl border border-gray-100">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full bg-gray-400"></div>
                      <span className="font-medium text-gray-700">Incidentes Creados</span>
                    </div>
                    <span className="text-xl font-bold text-gray-900">{custom.statistics?.incidents_created ?? 0}</span>
                  </div>
                  
                  <div className="flex items-center justify-between p-4 bg-green-50 rounded-xl border border-green-100">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full bg-green-500"></div>
                      <span className="font-medium text-green-800">Incidentes Resueltos</span>
                    </div>
                    <span className="text-xl font-bold text-green-700">{custom.statistics?.incidents_resolved ?? 0}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Export Section */}
      {!isLoading && (
        (tab === 'daily' && daily) || 
        (tab === 'weekly' && weekly) || 
        (tab === 'custom' && custom && generateCustom)
      ) && (
        <div className="fixed bottom-6 right-6 md:static md:flex md:justify-end gap-3 mt-8 bg-white md:bg-transparent p-4 md:p-0 rounded-2xl shadow-xl md:shadow-none border border-gray-100 md:border-none z-50 flex flex-col md:flex-row">
          <p className="text-xs text-gray-400 font-medium md:hidden mb-2 text-center uppercase tracking-wider">Opciones de Exportación</p>
          
          {/* Progress Bar */}
          {exportProgress !== null && (
            <div className="w-full mb-3">
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary-500 transition-all duration-300" 
                  style={{ width: `${exportProgress}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1 text-center">
                {exportProgress < 100 ? 'Exportando...' : '¡Completado!'}
              </p>
            </div>
          )}
          
          <button 
            onClick={() => handleExport(tab, 'xlsx')} 
            disabled={exportingFormat !== null}
            className="w-full md:w-auto px-6 py-2.5 bg-[#107c41] text-white rounded-xl text-sm font-bold shadow-lg shadow-green-900/20 hover:bg-[#0b5e31] flex items-center justify-center gap-2 transition-all disabled:opacity-70 disabled:cursor-not-allowed">
            {exportingFormat === 'xlsx' ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileSpreadsheet className="w-4 h-4" />} 
            {exportingFormat === 'xlsx' ? 'Exportando...' : 'Descargar Excel'}
          </button>
          
          <button 
            onClick={() => handleExport(tab, 'pdf')} 
            disabled={exportingFormat !== null}
            className="w-full md:w-auto px-6 py-2.5 bg-red-600 text-white rounded-xl text-sm font-bold shadow-lg shadow-red-900/20 hover:bg-red-700 flex items-center justify-center gap-2 transition-all disabled:opacity-70 disabled:cursor-not-allowed">
            {exportingFormat === 'pdf' ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />} 
            {exportingFormat === 'pdf' ? 'Exportando...' : 'Descargar PDF'}
          </button>
          
          <button 
            onClick={() => handleExport(tab, 'csv')} 
            disabled={exportingFormat !== null}
            className="w-full md:w-auto px-6 py-2.5 bg-gray-600 text-white rounded-xl text-sm font-bold shadow-lg shadow-gray-900/20 hover:bg-gray-700 flex items-center justify-center gap-2 transition-all disabled:opacity-70 disabled:cursor-not-allowed">
            {exportingFormat === 'csv' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />} 
            {exportingFormat === 'csv' ? 'Exportando...' : 'Descargar CSV'}
          </button>
        </div>
      )}
    </div>
  );
}