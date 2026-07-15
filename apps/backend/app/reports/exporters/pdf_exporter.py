"""PDF Exporter using fpdf2 - Professional layout in Spanish"""
from app.reports.base import BaseExporter, ReportData
from fpdf import FPDF


# Spanish labels for summary keys
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
    "water_loss_m3": "m\u00b3/dia",
    "water_loss_estimate": "m\u00b3/dia",
}

ANOMALY_SEVERITY_LABELS = {
    "CRITICA": "Critica",
    "critical": "Critica",
    "HIGH": "Alta",
    "high": "Alta",
    "MEDIUM": "Media",
    "medium": "Media",
    "LOW": "Baja",
    "low": "Baja",
}

INCIDENT_STATUS_LABELS = {
    "OPEN": "Abierto",
    "IN_PROGRESS": "En Progreso",
    "RESOLVED": "Resuelto",
    "CLOSED": "Cerrado",
}


class PDFExporter(BaseExporter):
    """Export reports to PDF format using fpdf2 with professional layout"""

    def get_format(self) -> str:
        return "pdf"

    def export(self, report_data: ReportData) -> bytes:
        pdf = PDFReport()
        pdf.set_auto_page_break(auto=True, margin=25)
        pdf.add_page()

        # --- Title ---
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 12, self._report_title(report_data), ln=True, align="C")
        pdf.ln(2)

        # --- Metadata block ---
        self._draw_metadata(pdf, report_data)
        pdf.ln(6)

        # --- Summary ---
        self._draw_summary(pdf, report_data)
        pdf.ln(4)

        # --- Details (varies by report type) ---
        self._draw_details(pdf, report_data)

        return bytes(pdf.output())

    # ------------------------------------------------------------------
    # Title
    # ------------------------------------------------------------------
    def _report_title(self, rd: ReportData) -> str:
        titles = {
            "daily": "Reporte Diario de Operaciones",
            "weekly": "Reporte Semanal de Operaciones",
            "custom": "Reporte Personalizado",
            "sla": "Reporte de Cumplimiento SLA",
        }
        return titles.get(rd.report_type, f"Reporte {rd.report_type.title()}")

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------
    def _draw_metadata(self, pdf: FPDF, rd: ReportData):
        pdf.set_font("Helvetica", "", 10)
        pdf.set_fill_color(240, 240, 240)
        labels = [
            ("Sector", f"{rd.dma_name} ({rd.dma_id})"),
            ("Periodo", f"{rd.period_start.strftime('%d/%m/%Y')} al {rd.period_end.strftime('%d/%m/%Y')}"),
            ("Generado", rd.generated_at.strftime("%d/%m/%Y %H:%M")),
        ]
        for label, value in labels:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(30, 7, label + ":", border=0)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 7, value, ln=True, border=0)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    def _draw_summary(self, pdf: FPDF, rd: ReportData):
        self._section_header(pdf, "Resumen Ejecutivo")
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 10)
        pdf.set_fill_color(245, 248, 252)

        summary = rd.summary or {}
        row_alt = False
        for key, value in summary.items():
            label = SUMMARY_LABELS.get(key, key.replace("_", " ").title())
            unit = SUMMARY_UNITS.get(key, "")
            formatted = self._format_value(value, unit)

            pdf.set_fill_color(245, 248, 252) if row_alt else pdf.set_fill_color(255, 255, 255)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(80, 7, f"  {label}", border="B", fill=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 7, formatted, border="B", ln=True, fill=True)
            row_alt = not row_alt

        pdf.ln(4)

    # ------------------------------------------------------------------
    # Details dispatcher
    # ------------------------------------------------------------------
    def _draw_details(self, pdf: FPDF, rd: ReportData):
        details = rd.details or {}

        if rd.report_type == "daily":
            self._draw_daily_details(pdf, details)
        elif rd.report_type == "weekly":
            self._draw_weekly_details(pdf, details)
        elif rd.report_type == "custom":
            self._draw_custom_details(pdf, details)
        elif rd.report_type == "sla":
            self._draw_sla_details(pdf, details)

    # ------------------------------------------------------------------
    # Daily details
    # ------------------------------------------------------------------
    def _draw_daily_details(self, pdf: FPDF, details: dict):
        # --- Anomalies breakdown ---
        ab = details.get("anomalies_breakdown", {})
        if ab:
            self._section_header(pdf, "Desglose de Anomalias")
            pdf.ln(2)
            pdf.set_font("Helvetica", "", 10)
            rows = [
                ("Total", ab.get("total", 0)),
                ("Criticas", ab.get("critical", 0)),
                ("Alta Severidad", ab.get("high", 0)),
                ("Severidad Media", ab.get("medium", 0)),
                ("Baja Severidad", ab.get("low", 0)),
            ]
            self._kv_table(pdf, rows)
            pdf.ln(4)

        # --- Incidents breakdown ---
        ib = details.get("incidents_breakdown", {})
        if ib:
            self._section_header(pdf, "Desglose de Incidencias")
            pdf.ln(2)
            rows = [
                ("Total", ib.get("total", 0)),
                ("Abiertas", ib.get("open", 0)),
                ("Resueltas", ib.get("resolved", 0)),
                ("Criticas Abiertas", ib.get("critical_open", 0)),
            ]
            self._kv_table(pdf, rows)
            pdf.ln(4)

        # --- Pressure & Flow stats ---
        ps = details.get("pressure_stats", {})
        fs = details.get("flow_stats", {})
        if ps or fs:
            self._section_header(pdf, "Estadisticas de Presion y Caudal")
            pdf.ln(2)
            rows = []
            if ps:
                rows.append(("Presion Minima", f"{ps.get('min', 0):.1f} mca"))
                rows.append(("Presion Maxima", f"{ps.get('max', 0):.1f} mca"))
            if fs:
                rows.append(("Caudal Minimo", f"{fs.get('min', 0):.1f} LPS"))
                rows.append(("Caudal Maximo", f"{fs.get('max', 0):.1f} LPS"))
            self._kv_table(pdf, rows)
            pdf.ln(4)

        # --- Readings summary ---
        readings = details.get("readings", [])
        if readings:
            self._section_header(pdf, f"Resumen de Lecturas ({len(readings)} registros)")
            pdf.ln(2)
            self._draw_readings_table(pdf, readings)

    # ------------------------------------------------------------------
    # Weekly details
    # ------------------------------------------------------------------
    def _draw_weekly_details(self, pdf: FPDF, details: dict):
        daily_stats = details.get("daily_stats", [])
        if daily_stats:
            self._section_header(pdf, "Estadisticas Diarias")
            pdf.ln(2)
            self._draw_daily_stats_table(pdf, daily_stats)
            pdf.ln(4)

        # Trends
        at = details.get("anomaly_trend", {})
        it = details.get("incident_trend", {})
        if at or it:
            self._section_header(pdf, "Tendencias")
            pdf.ln(2)
            rows = []
            if at:
                rows.append(("Tendencia Anomalias", self._trend_label(at.get("trend", "STABLE"))))
                rows.append(("Cambio Anomalias", f"{at.get('change_percentage', 0):+.1f}%"))
            if it:
                rows.append(("Tendencia Incidencias", self._trend_label(it.get("trend", "STABLE"))))
                rows.append(("Cambio Incidencias", f"{it.get('change_percentage', 0):+.1f}%"))
            self._kv_table(pdf, rows)
            pdf.ln(4)

    # ------------------------------------------------------------------
    # Custom details
    # ------------------------------------------------------------------
    def _draw_custom_details(self, pdf: FPDF, details: dict):
        anomalies = details.get("anomalies_list", [])
        if anomalies:
            self._section_header(pdf, f"Anomalias Detectadas ({len(anomalies)})")
            pdf.ln(2)
            self._draw_anomalies_table(pdf, anomalies)
            pdf.ln(4)

        incidents = details.get("incidents_list", [])
        if incidents:
            self._section_header(pdf, f"Incidencias ({len(incidents)})")
            pdf.ln(2)
            self._draw_incidents_table(pdf, incidents)
            pdf.ln(4)

    # ------------------------------------------------------------------
    # SLA details
    # ------------------------------------------------------------------
    def _draw_sla_details(self, pdf: FPDF, details: dict):
        if details:
            self._section_header(pdf, "Detalles SLA")
            pdf.ln(2)
            for key, value in details.items():
                label = key.replace("_", " ").title()
                if isinstance(value, dict):
                    pdf.set_font("Helvetica", "B", 10)
                    pdf.cell(0, 7, label, ln=True)
                    for k2, v2 in value.items():
                        pdf.set_font("Helvetica", "", 9)
                        pdf.cell(0, 6, f"    {k2}: {v2}", ln=True)
                else:
                    self._kv_table(pdf, [(label, value)])
            pdf.ln(4)

    # ------------------------------------------------------------------
    # Table helpers
    # ------------------------------------------------------------------
    def _section_header(self, pdf: FPDF, title: str):
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_fill_color(31, 78, 121)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 9, f"  {title}", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)

    def _kv_table(self, pdf: FPDF, rows: list):
        pdf.set_font("Helvetica", "", 10)
        alt = False
        for label, value in rows:
            pdf.set_fill_color(245, 248, 252) if alt else pdf.set_fill_color(255, 255, 255)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(70, 7, f"  {label}", border="B", fill=True)
            pdf.set_font("Helvetica", "", 10)
            val_str = str(value) if not isinstance(value, (int, float)) else f"{value}"
            pdf.cell(0, 7, f" {val_str}", border="B", ln=True, fill=True)
            alt = not alt

    def _draw_anomalies_table(self, pdf: FPDF, anomalies: list):
        headers = ["ID", "Fecha", "Severidad", "Estado"]
        widths = [20, 50, 40, 40]

        # Header row
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(31, 78, 121)
        pdf.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            pdf.cell(widths[i], 7, h, border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_text_color(0, 0, 0)

        # Data rows
        pdf.set_font("Helvetica", "", 8)
        alt = False
        for a in anomalies[:30]:  # Limit to 30 rows to avoid overflow
            pdf.set_fill_color(245, 248, 252) if alt else pdf.set_fill_color(255, 255, 255)
            row = [
                str(a.get("id", ""))[:18],
                str(a.get("date", ""))[:22],
                ANOMALY_SEVERITY_LABELS.get(a.get("severity", ""), a.get("severity", "")),
                INCIDENT_STATUS_LABELS.get(a.get("status", ""), a.get("status", "")),
            ]
            for i, val in enumerate(row):
                pdf.cell(widths[i], 6, val, border="B", fill=True, align="C")
            pdf.ln()
            alt = not alt

    def _draw_incidents_table(self, pdf: FPDF, incidents: list):
        headers = ["Codigo", "Titulo", "Prioridad", "Estado"]
        widths = [30, 70, 35, 35]

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(31, 78, 121)
        pdf.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            pdf.cell(widths[i], 7, h, border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_text_color(0, 0, 0)

        pdf.set_font("Helvetica", "", 8)
        alt = False
        for inc in incidents[:30]:
            pdf.set_fill_color(245, 248, 252) if alt else pdf.set_fill_color(255, 255, 255)
            row = [
                str(inc.get("code", ""))[:28],
                str(inc.get("title", ""))[:48],
                ANOMALY_SEVERITY_LABELS.get(inc.get("priority", ""), inc.get("priority", "")),
                INCIDENT_STATUS_LABELS.get(inc.get("status", ""), inc.get("status", "")),
            ]
            for i, val in enumerate(row):
                pdf.cell(widths[i], 6, val, border="B", fill=True, align="C")
            pdf.ln()
            alt = not alt

    def _draw_daily_stats_table(self, pdf: FPDF, stats: list):
        headers = ["Fecha", "Presion Prom", "Caudal Prom", "Lecturas", "Anomalias", "Perdidas (m3)"]
        widths = [28, 30, 30, 25, 25, 30]

        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(31, 78, 121)
        pdf.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            pdf.cell(widths[i], 7, h, border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_text_color(0, 0, 0)

        pdf.set_font("Helvetica", "", 8)
        alt = False
        for s in stats:
            pdf.set_fill_color(245, 248, 252) if alt else pdf.set_fill_color(255, 255, 255)
            row = [
                str(s.get("date", "")),
                f"{s.get('avg_pressure', 0):.1f}",
                f"{s.get('avg_flow', 0):.1f}",
                str(s.get("readings_count", 0)),
                str(s.get("anomalies_count", 0)),
                f"{s.get('water_loss', 0):.2f}",
            ]
            for i, val in enumerate(row):
                pdf.cell(widths[i], 6, val, border="B", fill=True, align="C")
            pdf.ln()
            alt = not alt

    def _draw_readings_table(self, pdf: FPDF, readings: list):
        """Show first 20 readings as a sample table."""
        headers = ["Hora", "Presion (mca)", "Caudal (LPS)", "Anomalia"]
        widths = [50, 40, 40, 30]

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(31, 78, 121)
        pdf.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            pdf.cell(widths[i], 7, h, border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_text_color(0, 0, 0)

        pdf.set_font("Helvetica", "", 8)
        alt = False
        for r in readings[:20]:
            pdf.set_fill_color(245, 248, 252) if alt else pdf.set_fill_color(255, 255, 255)
            ts = r.get("timestamp", "")
            if "T" in ts:
                ts = ts.split("T")[1][:5]
            row = [
                ts,
                f"{r.get('pressure_mca', 0):.1f}",
                f"{r.get('flow_lps', 0):.1f}",
                "Si" if r.get("is_anomaly") else "No",
            ]
            for i, val in enumerate(row):
                pdf.cell(widths[i], 6, val, border="B", fill=True, align="C")
            pdf.ln()
            alt = not alt

        if len(readings) > 20:
            pdf.set_font("Helvetica", "I", 8)
            pdf.cell(0, 6, f"  ... y {len(readings) - 20} lecturas mas", ln=True)

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------
    def _format_value(self, value, unit: str = "") -> str:
        if isinstance(value, float):
            formatted = f"{value:.2f}"
        elif isinstance(value, int):
            formatted = str(value)
        else:
            formatted = str(value)

        if unit:
            return f"{formatted} {unit}"
        return formatted

    def _trend_label(self, trend: str) -> str:
        labels = {
            "RISING": "En Aumento",
            "FALLING": "En Disminucion",
            "STABLE": "Estable",
        }
        return labels.get(trend, trend)


class PDFReport(FPDF):
    """Custom PDF report class with header and footer"""

    def header(self):
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, "SGIP-CAP  |  Sistema de Gestion Integral de Perdidas de Agua", align="C", ln=True)
        self.set_draw_color(31, 78, 121)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", align="C")
        self.set_text_color(0, 0, 0)
