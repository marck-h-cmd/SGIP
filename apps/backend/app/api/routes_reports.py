"""Report Routes - Modular Architecture"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response
from datetime import datetime, timedelta
from typing import Optional
from app.services.report_service import ReportService
from app.schemas.report_schema import DailyReportResponse, WeeklyReportResponse
from app.core.exceptions import NotFoundException
from app.core.config import settings
from app.reports.generators import DailyReportGenerator, WeeklyReportGenerator, CustomReportGenerator, SLAReportGenerator
from app.reports.exporters import PDFExporter, XLSXExporter, CSVExporter

router = APIRouter(prefix="/api/reports", tags=["Reports"])


def get_generator(report_type: str):
    """Get report generator by type"""
    generators = {
        "daily": DailyReportGenerator(),
        "weekly": WeeklyReportGenerator(),
        "custom": CustomReportGenerator(),
        "sla": SLAReportGenerator()
    }
    return generators.get(report_type)


def get_exporter(format_type: str):
    """Get exporter by format"""
    exporters = {
        "pdf": PDFExporter(),
        "xlsx": XLSXExporter(),
        "csv": CSVExporter()
    }
    return exporters.get(format_type)


# === LEGACY ENDPOINTS (Maintained for backward compatibility) ===

@router.get("/daily")
async def get_daily_report(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    service: ReportService = Depends()
) -> DailyReportResponse:
    """Get daily report"""
    report_date = None
    if date:
        try:
            report_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    report = service.generate_daily_report(report_date)
    return DailyReportResponse(**report)


@router.get("/moche/daily")
async def get_moche_daily_report(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    service: ReportService = Depends()
) -> DailyReportResponse:
    """Get daily report for Moche sector"""
    report_date = None
    if date:
        try:
            report_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    report = service.generate_daily_report(report_date)
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
    
    return service.generate_custom_report(start_date, end_date, dma_id)


@router.get("/moche/custom")
async def get_moche_custom_report(
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(..., description="End date"),
    service: ReportService = Depends()
):
    """Get custom report for Moche sector"""
    return await get_custom_report(start_date, end_date, settings.target_dma, service)


# === NEW MODULAR ENDPOINTS ===

@router.get("/v2/{report_type}")
async def get_report_v2(
    report_type: str,
    format: str = Query("json", description="Export format: json, pdf, xlsx, csv"),
    date: Optional[str] = Query(None, description="Date for daily report (YYYY-MM-DD)"),
    start_date: Optional[datetime] = Query(None, description="Start date for custom report"),
    end_date: Optional[datetime] = Query(None, description="End date for custom report"),
    dma_id: Optional[str] = Query(None, description="DMA ID"),
    sla_breaches_only: bool = Query(False, description="SLA breaches only")
):
    """
    Generate report using modular architecture
    
    - report_type: daily, weekly, custom, sla
    - format: json, pdf, xlsx, csv
    """
    if report_type not in ["daily", "weekly", "custom", "sla"]:
        raise HTTPException(status_code=400, detail="Invalid report type. Use 'daily', 'weekly', 'custom', or 'sla'")
    
    # Get generator
    generator = get_generator(report_type)
    if not generator:
        raise HTTPException(status_code=500, detail="Report generator not found")
    
    # Generate report data
    try:
        if report_type == "daily":
            report_date = None
            if date:
                try:
                    report_date = datetime.strptime(date, "%Y-%m-%d")
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
            report_data = generator.generate(date=report_date, dma_id=dma_id)
        
        elif report_type == "weekly":
            report_data = generator.generate(dma_id=dma_id)
        
        elif report_type == "custom":
            if not start_date or not end_date:
                raise HTTPException(status_code=400, detail="start_date and end_date required for custom report")
            if start_date > end_date:
                raise HTTPException(status_code=400, detail="start_date must be before end_date")
            if (end_date - start_date).days > 90:
                raise HTTPException(status_code=400, detail="Date range cannot exceed 90 days")
            report_data = generator.generate(start_date=start_date, end_date=end_date, dma_id=dma_id)
        
        elif report_type == "sla":
            report_data = generator.generate(dma_id=dma_id)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")
    
    # Export if requested
    if format.lower() != "json":
        exporter = get_exporter(format.lower())
        if not exporter:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'json', 'pdf', 'xlsx', or 'csv'")
        
        try:
            content = exporter.export(report_data)
            mime_type = exporter.get_mime_type()
            extension = exporter.get_extension()
            filename = f"{report_type}_report_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.{extension}"
            
            return Response(
                content=content,
                media_type=mime_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error exporting report: {str(e)}")
    
    # Return JSON
    return {
        "report_type": report_data.report_type,
        "dma_id": report_data.dma_id,
        "dma_name": report_data.dma_name,
        "period_start": report_data.period_start.isoformat(),
        "period_end": report_data.period_end.isoformat(),
        "generated_at": report_data.generated_at.isoformat(),
        "summary": report_data.summary,
        "details": report_data.details,
        "metadata": report_data.metadata
    }


@router.get("/v2/moche/{report_type}")
async def get_moche_report_v2(
    report_type: str,
    format: str = Query("json", description="Export format"),
    date: Optional[str] = Query(None, description="Date for daily report"),
    start_date: Optional[datetime] = Query(None, description="Start date for custom report"),
    end_date: Optional[datetime] = Query(None, description="End date for custom report")
):
    """Generate report for Moche sector (DMA-MO-01)"""
    return await get_report_v2(
        report_type=report_type,
        format=format,
        date=date,
        start_date=start_date,
        end_date=end_date,
        dma_id=settings.target_dma
    )


@router.get("/v2/export/{report_type}")
async def export_report_v2(
    report_type: str,
    format: str = Query(..., description="Export format: pdf, xlsx, csv"),
    date: Optional[str] = Query(None, description="Date for daily report"),
    start_date: Optional[datetime] = Query(None, description="Start date for custom report"),
    end_date: Optional[datetime] = Query(None, description="End date for custom report"),
    dma_id: Optional[str] = Query(None, description="DMA ID")
):
    """Export report to file format"""
    if format.lower() == "json":
        raise HTTPException(status_code=400, detail="Use /v2/{report_type}?format=json for JSON output")
    
    return await get_report_v2(
        report_type=report_type,
        format=format,
        date=date,
        start_date=start_date,
        end_date=end_date,
        dma_id=dma_id
    )