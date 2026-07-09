from fastapi import APIRouter, Depends, Query, HTTPException
from datetime import datetime, timedelta
from typing import Optional
from app.services.report_service import ReportService
from app.schemas.report_schema import DailyReportResponse, WeeklyReportResponse
from app.core.exceptions import NotFoundException
from app.core.config import settings

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/daily")
async def get_daily_report(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    service: ReportService = Depends()
) -> DailyReportResponse:
    """Get daily report"""
    if date:
        try:
            report_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        report_date = None
    
    report = service.generate_daily_report(report_date)
    return DailyReportResponse(**report)


@router.get("/moche/daily")
async def get_moche_daily_report(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    service: ReportService = Depends()
) -> DailyReportResponse:
    """Get daily report for Moche sector"""
    if date:
        try:
            report_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        report_date = None
    
    report = service.generate_daily_report(report_date)
    # Ensure it's for Moche
    if report["dma"]["code"] != settings.target_dma:
        raise NotFoundException("Report", f"Moche sector on {date or 'today'}")
    return DailyReportResponse(**report)


@router.get("/weekly")
async def get_weekly_report(
    service: ReportService = Depends()
) -> WeeklyReportResponse:
    """Get weekly report"""
    report = service.generate_weekly_report()
    return WeeklyReportResponse(**report)


@router.get("/moche/weekly")
async def get_moche_weekly_report(
    service: ReportService = Depends()
) -> WeeklyReportResponse:
    """Get weekly report for Moche sector"""
    report = service.generate_weekly_report()
    if report["dma"] != settings.target_dma:
        raise NotFoundException("Report", "Moche sector")
    return WeeklyReportResponse(**report)


@router.get("/custom")
async def get_custom_report(
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(..., description="End date"),
    dma_id: Optional[str] = Query(None, description="DMA ID"),
    service: ReportService = Depends()
):
    """Get custom report for a date range"""
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    
    if (end_date - start_date).days > 90:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 90 days")
    
    # Get data for the period
    dma = dma_id or settings.target_dma
    
    readings = service.telemetry_service.get_historical_readings(
        dma,
        start_date,
        end_date,
        limit=10000
    )
    
    anomalies = service.anomaly_service.get_recent_anomalies(
        dma,
        hours=int((end_date - start_date).total_seconds() / 3600)
    )
    
    incidents = service.incident_service.get_all_tickets(
        dma_id=dma,
        limit=1000
    )
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "dma_id": dma,
        "statistics": {
            "total_readings": len(readings),
            "avg_pressure": round(sum(r.pressure_mca for r in readings) / len(readings), 1) if readings else 0,
            "avg_flow": round(sum(r.flow_lps for r in readings) / len(readings), 1) if readings else 0,
            "anomalies_detected": len(anomalies),
            "incidents_created": len(incidents),
            "incidents_resolved": len([i for i in incidents if i.status.value in ["RESOLVED", "CLOSED"]])
        },
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/moche/custom")
async def get_moche_custom_report(
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(..., description="End date"),
    service: ReportService = Depends()
):
    """Get custom report for Moche sector"""
    return await get_custom_report(start_date, end_date, settings.target_dma, service)


@router.get("/export/{report_type}")
async def export_report(
    report_type: str,
    format: str = Query("json", description="Export format (json or csv)"),
    date: Optional[str] = Query(None, description="Date for daily report"),
    service: ReportService = Depends()
):
    """Export a report in specified format"""
    if report_type not in ["daily", "weekly"]:
        raise HTTPException(status_code=400, detail="Invalid report type. Use 'daily' or 'weekly'")
    
    if report_type == "daily":
        report = service.generate_daily_report(date)
    else:
        report = service.generate_weekly_report()
    
    if format.lower() == "csv":
        # Convert to CSV format
        import csv
        from io import StringIO
        
        output = StringIO()
        if report_type == "daily":
            writer = csv.writer(output)
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Date", report.get("date")])
            writer.writerow(["DMA", report.get("dma", {}).get("name")])
            writer.writerow(["Avg Pressure", report.get("summary", {}).get("avg_pressure")])
            writer.writerow(["Avg Flow", report.get("summary", {}).get("avg_flow")])
            writer.writerow(["Total Anomalies", report.get("anomalies", {}).get("total")])
            writer.writerow(["Total Incidents", report.get("incidents", {}).get("total")])
        else:
            writer = csv.writer(output)
            writer.writerow(["Date", "Avg Pressure", "Avg Flow"])
            for day in report.get("daily_stats", []):
                writer.writerow([day.get("date"), day.get("avg_pressure"), day.get("avg_flow")])
        
        return {
            "content": output.getvalue(),
            "filename": f"{report_type}_report_{datetime.utcnow().strftime('%Y%m%d')}.csv",
            "format": "csv"
        }
    
    return {
        "report": report,
        "format": "json",
        "generated_at": datetime.utcnow().isoformat()
    }