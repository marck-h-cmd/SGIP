"""
Módulo de escenarios realistas de anomalías hidráulicas para el sector Moche.
Cada escenario tiene: tipo, descripción, efectos en presión/caudal, severidad, y causa raíz.
"""
from dataclasses import dataclass, field
from typing import List, Tuple
import random


@dataclass
class AnomalyScenario:
    """Representa un tipo real de anomalía en una red de distribución de agua"""
    code: str
    name: str
    description: str
    root_cause: str
    pressure_effect: Tuple[float, float]  # (min_delta, max_delta) en MCA
    flow_effect: Tuple[float, float]       # (min_delta, max_delta) en LPS
    duration_hours: Tuple[int, int]        # (min, max) horas que dura el evento
    severity_weights: dict = field(default_factory=lambda: {
        "CRITICAL": 0.1, "HIGH": 0.3, "MEDIUM": 0.4, "LOW": 0.2
    })
    tags: List[str] = field(default_factory=list)


# ============================================================
# Catálogo de escenarios reales del sector Moche
# ============================================================

ANOMALY_CATALOG: List[AnomalyScenario] = [
    # --- FUGAS ---
    AnomalyScenario(
        code="FUGA_SUB",
        name="Fuga Subterránea",
        description="Pérdida de agua en tubería subterránea. Presión disminuye gradualmente y caudal aumenta compensando la fuga. Requiere inspección con correlador acústico.",
        root_cause="Deterioro de tubería de asbesto-cemento por antigüedad (>30 años) o asentamiento de terreno",
        pressure_effect=(-8.0, -2.0),
        flow_effect=(3.0, 15.0),
        duration_hours=(4, 48),
        severity_weights={"CRITICAL": 0.15, "HIGH": 0.35, "MEDIUM": 0.35, "LOW": 0.15},
        tags=["fuga", "subterranea", "perdida"]
    ),
    AnomalyScenario(
        code="FUGA_SUP",
        name="Fuga Superficial Visible",
        description="Fuga visible en superficie. Se observa humedad o acumulación de agua en vía pública. Caudal aumentado significativamente.",
        root_cause="Rotura de junta o acoplamiento en tubería superficial. Posible daño por excavación.",
        pressure_effect=(-5.0, -1.0),
        flow_effect=(5.0, 20.0),
        duration_hours=(2, 24),
        severity_weights={"CRITICAL": 0.2, "HIGH": 0.4, "MEDIUM": 0.3, "LOW": 0.1},
        tags=["fuga", "superficial", "visible"]
    ),
    AnomalyScenario(
        code="FUGA_ENT",
        name="Fuga en Entrada de Edificio",
        description="Fuga en conexión de entrada a predio. Caudal elevado en horario nocturno cuando no hay consumo normal.",
        root_cause="Conexión clandestina o deterioro de llave de paso del predio",
        pressure_effect=(-3.0, -0.5),
        flow_effect=(2.0, 8.0),
        duration_hours=(8, 72),
        severity_weights={"CRITICAL": 0.05, "HIGH": 0.2, "MEDIUM": 0.5, "LOW": 0.25},
        tags=["fuga", "predio", "conexion"]
    ),

    # --- ROTURAS ---
    AnomalyScenario(
        code="ROTURA_TUB",
        name="Rotura de Tubería Principal",
        description="Rotura catastrófica de tubería de distribución. Caída súbita de presión y aumento extremo de caudal. Requiere acometida de emergencia.",
        root_cause="Golpe de ariete, corrosión avanzada, o falla material en tubería de hierro fundido",
        pressure_effect=(-20.0, -8.0),
        flow_effect=(15.0, 40.0),
        duration_hours=(1, 6),
        severity_weights={"CRITICAL": 0.6, "HIGH": 0.3, "MEDIUM": 0.1, "LOW": 0.0},
        tags=["rotura", "emergencia", "tuberia"]
    ),
    AnomalyScenario(
        code="ROTURA_AC",
        name="Rotura de Acoplamiento",
        description="Desconexión parcial de acoplamiento en unión de tuberías. Pérdida moderada con variabilidad según presión de red.",
        root_cause="Vibración, asentamiento diferencial, o instalación deficiente del acoplamiento",
        pressure_effect=(-6.0, -2.0),
        flow_effect=(4.0, 12.0),
        duration_hours=(3, 36),
        severity_weights={"CRITICAL": 0.1, "HIGH": 0.3, "MEDIUM": 0.45, "LOW": 0.15},
        tags=["rotura", "acoplamiento", "union"]
    ),

    # --- ROBO DE AGUA ---
    AnomalyScenario(
        code="ROBO_AGA",
        name="Conexión Clandestina / Robo de Agua",
        description="Incremento sostenido de caudal sin variación de presión significativa. Patrón sugiere conexión no autorizada al tendido.",
        root_cause="Conexión ilegal mediante perforación de tubería o derivación de hidrante",
        pressure_effect=(-2.0, 0.5),
        flow_effect=(3.0, 10.0),
        duration_hours=(24, 168),
        severity_weights={"CRITICAL": 0.05, "HIGH": 0.25, "MEDIUM": 0.5, "LOW": 0.2},
        tags=["robo", "clandestina", "ilegal"]
    ),

    # --- PROBLEMAS OPERATIVOS ---
    AnomalyScenario(
        code="SOBREPRES",
        name="Sobrepresión en Red",
        description="Presión anormalmente alta que puede dañar conexiones y artefactos. Riesgo de roturas secundarias.",
        root_cause="Bomba de bombeo con falla en variador de frecuencia o válvula reguladora atascada",
        pressure_effect=(8.0, 18.0),
        flow_effect=(-5.0, 2.0),
        duration_hours=(1, 8),
        severity_weights={"CRITICAL": 0.25, "HIGH": 0.35, "MEDIUM": 0.3, "LOW": 0.1},
        tags=["sobrepresion", "bomba", "regulacion"]
    ),
    AnomalyScenario(
        code="BOMBA_OFF",
        name="Parada de Bomba / Falta de Energía",
        description="Caída brusca de presión por apagado de estación de bombeo. Caudal disminuye dramáticamente.",
        root_cause="Corte de energía eléctrica, falla en tablero de control, o mantenimiento no programado",
        pressure_effect=(-15.0, -5.0),
        flow_effect=(-15.0, -5.0),
        duration_hours=(0.5, 4),
        severity_weights={"CRITICAL": 0.3, "HIGH": 0.4, "MEDIUM": 0.25, "LOW": 0.05},
        tags=["bomba", "energia", "operacion"]
    ),
    AnomalyScenario(
        code="VALVULA_C",
        name="Válvula de Corte Parcial",
        description="Válvula de seccionamiento parcialmente cerrada. Reduce caudal y presión aguas abajo del punto de corte.",
        root_cause="Válvula obstruida por sedimentos, o cierre accidental durante mantenimiento",
        pressure_effect=(-7.0, -2.0),
        flow_effect=(-10.0, -3.0),
        duration_hours=(2, 24),
        severity_weights={"CRITICAL": 0.1, "HIGH": 0.3, "MEDIUM": 0.45, "LOW": 0.15},
        tags=["valvula", "operacion", "mantenimiento"]
    ),

    # --- SENSOR / MEDICIÓN ---
    AnomalyScenario(
        code="SENSOR_ERR",
        name="Falla de Sensor / Errata de Medición",
        description="Lecturas erráticas o fuera de rango físico. Patrón no consistente con comportamiento hidráulico real.",
        root_cause="Falla eléctrica en transmisor, cables dañados, o퓰 sensor descalibrado",
        pressure_effect=(-15.0, 15.0),
        flow_effect=(-10.0, 10.0),
        duration_hours=(1, 12),
        severity_weights={"CRITICAL": 0.05, "HIGH": 0.1, "MEDIUM": 0.35, "LOW": 0.5},
        tags=["sensor", "medicion", "calidad"]
    ),
    AnomalyScenario(
        code="AIRE_RED",
        name="Aire Entrañado en Red",
        description="Presencia de aire en tuberías causando fluctuaciones erráticas de presión. Lecturas inestables.",
        root_cause="Entrada de aire por juntas defectuosas, tanque de nivel bajo, o válvula aireadora fallida",
        pressure_effect=(-4.0, 4.0),
        flow_effect=(-3.0, 3.0),
        duration_hours=(2, 12),
        severity_weights={"CRITICAL": 0.0, "HIGH": 0.15, "MEDIUM": 0.4, "LOW": 0.45},
        tags=["aire", "fluctuacion", "estabilidad"]
    ),

    # --- CONSUMO ANÓMALO ---
    AnomalyScenario(
        code="CONSUMO_IND",
        name="Consumo Industrial Anómalo",
        description="Incremento sostenido de caudal por usuario industrial con consumo fuera de contrato. Presión ligeramente reducida.",
        root_cause="Usuario con proceso productivo que excede su Dotación contratada",
        pressure_effect=(-3.0, -1.0),
        flow_effect=(5.0, 18.0),
        duration_hours=(8, 48),
        severity_weights={"CRITICAL": 0.05, "HIGH": 0.2, "MEDIUM": 0.5, "LOW": 0.25},
        tags=["consumo", "industrial", "usuario"]
    ),
]


def get_scenario_by_code(code: str) -> AnomalyScenario:
    """Obtener escenario por código"""
    for s in ANOMALY_CATALOG:
        if s.code == code:
            return s
    return None


def get_random_scenario() -> AnomalyScenario:
    """Seleccionar un escenario aleatorio con pesos"""
    # Pesos de probabilidad por tipo de escenario
    weights = {
        "FUGA_SUB": 25,
        "FUGA_SUP": 15,
        "FUGA_ENT": 10,
        "ROTURA_TUB": 5,
        "ROTURA_AC": 10,
        "ROBO_AGA": 8,
        "SOBREPRES": 8,
        "BOMBA_OFF": 7,
        "VALVULA_C": 5,
        "SENSOR_ERR": 3,
        "AIRE_RED": 2,
        "CONSUMO_IND": 2,
    }
    codes = list(weights.keys())
    w = [weights[c] for c in codes]
    chosen = random.choices(codes, weights=w, k=1)[0]
    return get_scenario_by_code(chosen)


def select_severity(scenario: AnomalyScenario) -> str:
    """Seleccionar severidad según los pesos del escenario"""
    severities = list(scenario.severity_weights.keys())
    w = [scenario.severity_weights[s] for s in severities]
    return random.choices(severities, weights=w, k=1)[0]


def compute_effects(scenario: AnomalyScenario, severity: str) -> Tuple[float, float]:
    """
    Calcular los efectos de presión y caudal según la severidad.
    Severidad más alta = efecto más intenso.
    """
    severity_multiplier = {
        "CRITICAL": 1.0,
        "HIGH": 0.75,
        "MEDIUM": 0.5,
        "LOW": 0.25
    }
    mult = severity_multiplier.get(severity, 0.5)

    p_min, p_max = scenario.pressure_effect
    f_min, f_max = scenario.flow_effect

    # Aplicar multiplicador de severidad
    p_delta = random.uniform(p_min, p_max) * mult
    f_delta = random.uniform(f_min, f_max) * mult

    return round(p_delta, 1), round(f_delta, 1)
