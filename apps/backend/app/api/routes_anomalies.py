from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from app.services.anomaly_service import AnomalyService
from app.services.telemetry_service import TelemetryService
from app.domain.telemetry import TelemetryReading
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/api/anomalies", tags=["Anomalies"])


@router.post("/analyze")
async def analyze_reading(
    reading: TelemetryReading,
    service: AnomalyService = Depends()
):
    """Analyze a single reading for anomalies"""
    result = service.analyze_reading(reading)
    return result

@router.post("/simulate")
async def simulate_anomaly(
    service: AnomalyService = Depends()
):
    """Inject a simulated critical anomaly with randomized critical-range values"""
    import random
    from app.core.config import settings

    # Pick one of several realistic critical-failure scenarios
    scenario = random.choice([
        # Scenario 1: Major pressure drop (pipe burst / major leak)
        {"pressure": round(random.uniform(10.0, 28.0), 1), "flow": round(random.uniform(20.0, 30.0), 1)},
        # Scenario 2: Flow surge (clandestine connection / meter bypass)
        {"pressure": round(random.uniform(48.0, 60.0), 1), "flow": round(random.uniform(46.0, 72.0), 1)},
        # Scenario 3: Combined anomaly (pressure drop + flow spike)
        {"pressure": round(random.uniform(15.0, 27.0), 1), "flow": round(random.uniform(50.0, 68.0), 1)},
        # Scenario 4: Near-critical low pressure (gradual leak)
        {"pressure": round(random.uniform(20.0, 29.5), 1), "flow": round(random.uniform(28.0, 35.0), 1)},
    ])

    reading = TelemetryReading(
        timestamp=datetime.utcnow(),
        dma_id=settings.target_dma,
        dma_name="Moche",
        sensor_id="SENS-MO-SIM",
        pressure_mca=scenario["pressure"],
        flow_lps=scenario["flow"],
        source="simulation",
        quality_flag="GOOD"
    )
    result = service.analyze_reading(reading)
    # Attach the simulated values for frontend awareness
    return {
        **result,
        "simulated_pressure": scenario["pressure"],
        "simulated_flow": scenario["flow"],
    }


@router.post("/analyze/batch")
async def analyze_batch(
    readings: List[TelemetryReading],
    service: AnomalyService = Depends()
):
    """Analyze multiple readings for anomalies"""
    results = []
    for reading in readings:
        result = service.analyze_reading(reading)
        results.append(result)
    return {
        "total": len(results),
        "anomalies_found": sum(1 for r in results if r.get("is_anomaly")),
        "results": results
    }


@router.get("/dma/{dma_id}")
async def analyze_dma(
    dma_id: str,
    hours: int = Query(24, ge=1, le=168, description="Hours to analyze"),
    service: AnomalyService = Depends()
):
    """Analyze a DMA for anomalies"""
    result = service.analyze_dma(dma_id, hours)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/moche/analyze")
async def analyze_moche(
    hours: int = Query(24, ge=1, le=168, description="Hours to analyze"),
    service: AnomalyService = Depends()
):
    """Analyze Moche sector for anomalies"""
    from app.core.config import settings
    result = service.analyze_dma(settings.target_dma, hours)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/recent")
async def get_recent_anomalies(
    dma_id: Optional[str] = Query(None, description="Filter by DMA ID"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    limit: int = Query(100, le=500, description="Limit results"),
    service: AnomalyService = Depends()
):
    """Get recent anomalies"""
    anomalies = service.get_recent_anomalies(dma_id, hours)
    return {
        "total": len(anomalies),
        "anomalies": anomalies[:limit]
    }


@router.get("/moche/recent")
async def get_moche_recent_anomalies(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    limit: int = Query(100, le=500, description="Limit results"),
    service: AnomalyService = Depends()
):
    """Get recent anomalies for Moche sector"""
    from app.core.config import settings
    anomalies = service.get_recent_anomalies(settings.target_dma, hours)
    return {
        "sector": "Moche",
        "total": len(anomalies),
        "anomalies": anomalies[:limit]
    }


@router.get("/stats")
async def get_anomaly_stats(
    dma_id: Optional[str] = Query(None, description="Filter by DMA ID"),
    service: AnomalyService = Depends()
):
    """Get anomaly statistics"""
    # Get anomalies from last 24 hours
    recent = service.get_recent_anomalies(dma_id, hours=24)
    
    severity_dist = service._calculate_severity_distribution(
        [{"anomaly": a.get("anomaly")} for a in recent if a.get("anomaly")]
    ) if recent else {}
    
    # Get anomalies from last 7 days for history
    recent_7d = service.get_recent_anomalies(dma_id, hours=168)
    
    # Group by day
    counts_by_date = {}
    now = datetime.utcnow()
    for i in range(6, -1, -1):
        d = now - timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        day_str = d.strftime("%a")
        es_days = {"Mon": "lun", "Tue": "mar", "Wed": "mié", "Thu": "jue", "Fri": "vie", "Sat": "sáb", "Sun": "dom"}
        counts_by_date[date_str] = {"dia": es_days.get(day_str, day_str), "anomalias": 0}
        
    for a in recent_7d:
        anom = a.get("anomaly")
        if anom and anom.detected_at:
            date_str = anom.detected_at.strftime("%Y-%m-%d")
            if date_str in counts_by_date:
                counts_by_date[date_str]["anomalias"] += 1
    
    history_7d = list(counts_by_date.values())
    
    from app.core.config import settings
    
    return {
        "total_anomalies_24h": len(recent),
        "severity_distribution": severity_dist,
        "avg_score": sum(a.get("score", 0) for a in recent) / len(recent) if recent else 0,
        "high_priority_count": len([a for a in recent if a.get("severity") in ["HIGH", "CRITICAL"]]),
        "critical_count": len([a for a in recent if a.get("severity") == "CRITICAL"]),
        "history_7d": history_7d,
        "threshold": settings.anomaly_threshold,
        "features": ['Presión (MCA)', 'Caudal (LPS)', 'Hora del día', 'Día de la semana']
    }


@router.get("/moche/stats")
async def get_moche_anomaly_stats(
    service: AnomalyService = Depends()
):
    """Get anomaly statistics for Moche sector"""
    from app.core.config import settings
    return await get_anomaly_stats(settings.target_dma, service)


@router.get("/{anomaly_id}")
async def get_anomaly_detail(
    anomaly_id: int,
    service: AnomalyService = Depends()
):
    """Get detailed information about a specific anomaly"""
    # Get recent anomalies and find the specific one
    anomalies = service.get_recent_anomalies(hours=168)
    for anomaly in anomalies:
        if anomaly.get("anomaly") and anomaly["anomaly"].id == anomaly_id:
            return anomaly
    raise NotFoundException("Anomaly", str(anomaly_id))