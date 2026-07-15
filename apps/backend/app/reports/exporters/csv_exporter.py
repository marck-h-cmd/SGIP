"""CSV Exporter - Professional layout in Spanish"""
from app.reports.base import BaseExporter, ReportData
import csv
import io


# Spanish labels
SUMMARY_LABELS = {
    "total_readings": "Lecturas Totales",
    "avg_pressure": "Presion Promedio",
    "avg_flow": "Caudal Promedio",
    "nrw_percentage": "Perdidas No Renumeradas",
    "water_loss_m3": "Perdidas de Agua",
    "water_loss_estimate": "Perdidas de Agua",
    "anomalies_total": "Anomalias Totales",
    "anomalies_critical": "Anomalias Criticas",
    "anomalies_detected": "Anomalias Detectadas",
    "incidents_total": "Incidencias Totales",
    "incidents_open": "Incidencias Abiertas",
    "incidents_created": "Incidencias Creadas",
    "incidents_resolved": "Incidencias Resueltas",
    "total_anomalies": "Total Anomalias",
    "total_incidents": "Total Incidencias",
}

SUMMARY_UNITS = {
    "avg_pressure": "mca",
    "avg_flow": "LPS",
    "nrw_percentage": "%",
    "water_loss_m3": "m3/dia",
    "water_loss_estimate": "m3/dia",
}


class CSVExporter(BaseExporter):
    """Export reports to CSV format with clean sections"""

    def get_format(self) -> str:
        return "csv"

    def export(self, report_data: ReportData) -> bytes:
        output = io.StringIO()
        writer = csv.writer(output, delimiter=";")

        # Header
        self._write_header(writer, report_data)

        # Summary
        self._write_summary(writer, report_data)

        # Details based on report type
        if report_data.report_type == "daily":
            self._write_daily_details(writer, report_data)
        elif report_data.report_type == "weekly":
            self._write_weekly_details(writer, report_data)
        elif report_data.report_type == "custom":
            self._write_custom_details(writer, report_data)

        # Metadata
        self._write_metadata(writer, report_data)

        output.seek(0)
        return output.getvalue().encode("utf-8-sig")  # BOM for Excel compatibility

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------
    def _write_header(self, writer, rd: ReportData):
        titles = {
            "daily": "REPORTE DIARIO DE OPERACIONES",
            "weekly": "REPORTE SEMANAL DE OPERACIONES",
            "custom": "REPORTE PERSONALIZADO",
            "sla": "REPORTE DE CUMPLIMIENTO SLA",
        }
        writer.writerow([titles.get(rd.report_type, f"REPORTE {rd.report_type.upper()}")])
        writer.writerow([])
        writer.writerow(["Sector:", f"{rd.dma_name} ({rd.dma_id})"])
        writer.writerow(["Periodo:", f"{rd.period_start.strftime('%d/%m/%Y')} al {rd.period_end.strftime('%d/%m/%Y')}"])
        writer.writerow(["Generado:", rd.generated_at.strftime("%d/%m/%Y %H:%M")])
        writer.writerow([])

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    def _write_summary(self, writer, rd: ReportData):
        writer.writerow(["=== RESUMEN EJECUTIVO ==="])
        writer.writerow([])
        writer.writerow(["Metrica", "Valor", "Unidad"])

        summary = rd.summary or {}
        for key, value in summary.items():
            label = SUMMARY_LABELS.get(key, key.replace("_", " ").title())
            unit = SUMMARY_UNITS.get(key, "")
            writer.writerow([label, value, unit])

        writer.writerow([])

    # ------------------------------------------------------------------
    # Daily details
    # ------------------------------------------------------------------
    def _write_daily_details(self, writer, rd: ReportData):
        details = rd.details or {}

        # Anomalies breakdown
        ab = details.get("anomalies_breakdown", {})
        if ab:
            writer.writerow(["=== DESGLOSE DE ANOMALIAS ==="])
            writer.writerow([])
            writer.writerow(["Total", ab.get("total", 0)])
            writer.writerow(["Criticas", ab.get("critical", 0)])
            writer.writerow(["Alta Severidad", ab.get("high", 0)])
            writer.writerow(["Severidad Media", ab.get("medium", 0)])
            writer.writerow(["Baja Severidad", ab.get("low", 0)])
            writer.writerow([])

        # Incidents breakdown
        ib = details.get("incidents_breakdown", {})
        if ib:
            writer.writerow(["=== DESGLOSE DE INCIDENCIAS ==="])
            writer.writerow([])
            writer.writerow(["Total", ib.get("total", 0)])
            writer.writerow(["Abiertas", ib.get("open", 0)])
            writer.writerow(["Resueltas", ib.get("resolved", 0)])
            writer.writerow(["Criticas Abiertas", ib.get("critical_open", 0)])
            writer.writerow([])

        # Pressure and flow stats
        ps = details.get("pressure_stats", {})
        fs = details.get("flow_stats", {})
        if ps or fs:
            writer.writerow(["=== ESTADISTICAS DE PRESION Y CAUDAL ==="])
            writer.writerow([])
            if ps:
                writer.writerow(["Presion Minima (mca)", ps.get("min", 0)])
                writer.writerow(["Presion Maxima (mca)", ps.get("max", 0)])
            if fs:
                writer.writerow(["Caudal Minimo (LPS)", fs.get("min", 0)])
                writer.writerow(["Caudal Maximo (LPS)", fs.get("max", 0)])
            writer.writerow([])

        # Readings sample
        readings = details.get("readings", [])
        if readings:
            writer.writerow([f"=== LECTURAS ({len(readings)} registros) ==="])
            writer.writerow([])
            writer.writerow(["Hora", "Presion (mca)", "Caudal (LPS)", "Anomalia"])
            for r in readings[:50]:  # Limit to 50 for CSV
                ts = r.get("timestamp", "")
                if "T" in ts:
                    ts = ts.split("T")[1][:5]
                writer.writerow([
                    ts,
                    r.get("pressure_mca", 0),
                    r.get("flow_lps", 0),
                    "Si" if r.get("is_anomaly") else "No",
                ])
            if len(readings) > 50:
                writer.writerow([f"... y {len(readings) - 50} lecturas mas"])
            writer.writerow([])

    # ------------------------------------------------------------------
    # Weekly details
    # ------------------------------------------------------------------
    def _write_weekly_details(self, writer, rd: ReportData):
        details = rd.details or {}

        daily_stats = details.get("daily_stats", [])
        if daily_stats:
            writer.writerow(["=== ESTADISTICAS DIARIAS ==="])
            writer.writerow([])
            writer.writerow(["Fecha", "Presion Prom (mca)", "Caudal Prom (LPS)", "Lecturas", "Anomalias", "Perdidas (m3)"])
            for s in daily_stats:
                writer.writerow([
                    s.get("date", ""),
                    s.get("avg_pressure", 0),
                    s.get("avg_flow", 0),
                    s.get("readings_count", 0),
                    s.get("anomalies_count", 0),
                    round(s.get("water_loss", 0), 2),
                ])
            writer.writerow([])

        # Trends
        at = details.get("anomaly_trend", {})
        it = details.get("incident_trend", {})
        if at or it:
            writer.writerow(["=== TENDENCIAS ==="])
            writer.writerow([])
            trend_labels = {"RISING": "En Aumento", "FALLING": "En Disminucion", "STABLE": "Estable"}
            if at:
                writer.writerow(["Tendencia Anomalias", trend_labels.get(at.get("trend", ""), at.get("trend", ""))])
                writer.writerow(["Cambio Anomalias (%)", f"{at.get('change_percentage', 0):+.1f}"])
            if it:
                writer.writerow(["Tendencia Incidencias", trend_labels.get(it.get("trend", ""), it.get("trend", ""))])
                writer.writerow(["Cambio Incidencias (%)", f"{it.get('change_percentage', 0):+.1f}"])
            writer.writerow([])

    # ------------------------------------------------------------------
    # Custom details
    # ------------------------------------------------------------------
    def _write_custom_details(self, writer, rd: ReportData):
        details = rd.details or {}

        anomalies = details.get("anomalies_list", [])
        if anomalies:
            writer.writerow([f"=== ANOMALIAS DETECTADAS ({len(anomalies)}) ==="])
            writer.writerow([])
            writer.writerow(["ID", "Fecha", "Severidad", "Estado"])
            for a in anomalies:
                writer.writerow([
                    a.get("id", ""),
                    a.get("date", ""),
                    a.get("severity", ""),
                    a.get("status", ""),
                ])
            writer.writerow([])

        incidents = details.get("incidents_list", [])
        if incidents:
            writer.writerow([f"=== INCIDENCIAS ({len(incidents)}) ==="])
            writer.writerow([])
            writer.writerow(["Codigo", "Titulo", "Prioridad", "Estado", "Fecha"])
            for inc in incidents:
                writer.writerow([
                    inc.get("code", ""),
                    inc.get("title", ""),
                    inc.get("priority", ""),
                    inc.get("status", ""),
                    inc.get("date", ""),
                ])
            writer.writerow([])

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------
    def _write_metadata(self, writer, rd: ReportData):
        writer.writerow(["=== METADATA ==="])
        writer.writerow(["Version Reporte", rd.metadata.get("report_version", "N/A")])
        writer.writerow(["Generado Por", rd.metadata.get("generated_by", "SGIP-CAP System")])
        if rd.metadata.get("target_dma"):
            writer.writerow(["DMA Objetivo", rd.metadata.get("target_dma")])
        if rd.metadata.get("period_days"):
            writer.writerow(["Dias del Periodo", rd.metadata.get("period_days")])
