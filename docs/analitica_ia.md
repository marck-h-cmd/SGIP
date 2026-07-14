# Analítica IA — Documentación Técnica del Módulo

**Proyecto:** SGIP — Sistema de Gestión Inteligente de Presión  
**Sector:** Moche, Trujillo (DMA-MO-01)  
**Fecha de documentación:** 14/07/2026  
**Estado:** ✅ Implementado y validado con datos simulados  

---

## 1. Visión General

El módulo de **Analítica IA** es el núcleo inteligente del SGIP. Su función principal es detectar automáticamente anomalías hidráulicas (caídas de presión, picos de caudal, fugas, conexiones clandestinas) usando un modelo de Machine Learning no supervisado, y presentar los resultados de forma visual y explicable en el dashboard.

> **Nota sobre los datos:** Actualmente el sistema opera con datos **simulados** generados por `MockTelemetryProvider`. Toda la arquitectura está diseñada para reemplazar esta fuente por datos reales (sensores IoT / SCADA) sin modificar la lógica de ML ni la capa de presentación.

---

## 2. Arquitectura del Sistema

```
Frontend (React/TSX)          Backend (FastAPI/Python)          Base de Datos
─────────────────────         ─────────────────────────         ───────────────
AnalyticsPage.tsx             routes_anomalies.py               PostgreSQL
    │                              │
    │  GET /api/anomalies/         │
    │  moche/recent  ─────────────►│  AnomalyService
    │  moche/stats                 │    ├── IsolationForestModel   ◄── Entrenado en memoria
    │  POST /simulate              │    ├── FeatureEngineer              al iniciar
    │                              │    ├── AnomalyRepository
    │◄─ JSON response ─────────────│    └── AlertService
    │
    │  React Query (invalidateQueries)
    │  actualización en tiempo real sin recarga
```

### Archivos clave

| Capa | Archivo | Responsabilidad |
|---|---|---|
| Frontend | `apps/frontend/src/pages/analytics/AnalyticsPage.tsx` | Dashboard de Analítica IA |
| Frontend | `apps/frontend/src/services/hooks.ts` | React Query hooks (`useRecentAnomalies`, `useAnomalyStats`) |
| Frontend | `apps/frontend/src/utils/format.ts` | Formateo de fechas con zona horaria correcta |
| Backend — API | `apps/backend/app/api/routes_anomalies.py` | Endpoints REST de anomalías |
| Backend — Servicio | `apps/backend/app/services/anomaly_service.py` | Lógica de negocio y orquestación |
| Backend — ML | `apps/backend/app/ml/isolation_forest_model.py` | Modelo Isolation Forest |
| Backend — ML | `apps/backend/app/ml/feature_engineering.py` | Extracción de características |

---

## 3. Modelo de Machine Learning

### Algoritmo: Isolation Forest

**Tipo:** Detección de anomalías no supervisada  
**Librería:** `scikit-learn` (`sklearn.ensemble.IsolationForest`)

#### Parámetros de entrenamiento

```python
IsolationForest(
    contamination=0.05,  # 5% de los datos de entrenamiento se asumen outliers
    random_state=42,
    n_estimators=100,
    max_samples='auto',
    bootstrap=False
)
```

#### Variables de entrada (features)

| Feature | Descripción | Tipo |
|---|---|---|
| `pressure_mca` | Presión en metros columna de agua | Continua |
| `flow_lps` | Caudal en litros por segundo | Continua |
| `hour` | Hora del día (0-23) | Cíclica |
| `day_of_week` | Día de la semana (0=lun, 6=dom) | Ordinal |

#### Datos de entrenamiento (datos simulados actuales)

El modelo se auto-entrena en memoria al iniciarse el servicio, usando **120 lecturas sintéticas** que representan el comportamiento normal del sector Moche:

```python
# Patrón simulado de operación normal
pressure_mca = 55.0 + 2.0 * (hora_pico) + (variación_menor)  # ~53–57 MCA
flow_lps     = 25.0 - 1.0 * (hora_pico) + (variación_menor)  # ~24–26 LPS
```

> **Para datos reales:** Reemplazar `_initialize_model()` en `anomaly_service.py` con una consulta a la base de datos de las últimas N lecturas históricas.

#### Cálculo del Score de Anomalía

El `decision_function` de Isolation Forest devuelve valores negativos para anomalías. El sistema normaliza a [0, 1]:

```
score_normalizado = 1 - ((ds - ds_min) / (ds_max - ds_min))
```

Donde `ds_min` y `ds_max` son los límites del conjunto de entrenamiento. El resultado final se limita al rango [0.0, 1.0].

---

## 4. Lógica de Detección (AnomalyService)

### Flujo principal de `analyze_reading()`

```
1. Llamar al modelo ML → is_anomaly, score
      │
      ▼
2. Heurística de emergencia (Override físico)
   Si presión < 40 MCA  OR  caudal > 35 LPS:
   → is_anomaly = True
   → Si score < 0.8: score = 1.0  (certeza máxima)
      │
      ▼
3. Determinar Severidad
   presión < 30 MCA  OR  caudal > 45 LPS  → CRITICAL
   presión < 35 MCA  OR  caudal > 40 LPS  → HIGH
   presión < 45 MCA  OR  caudal > 35 LPS  → MEDIUM
   De lo contrario                         → LOW
      │
      ▼
4. Calcular variaciones vs. baseline normal
   pressure_variation = pressure_mca - 55.2
   flow_variation     = flow_lps - 25.4
      │
      ▼
5. Guardar en PostgreSQL (tabla anomalies)
6. Disparar alerta en AlertService
```

### ¿Por qué existe el Override (paso 2)?

El Isolation Forest está entrenado con datos que rondan los 55 MCA. Cuando recibe un dato extremadamente alejado (ej: 15 MCA), el modelo puede clasificarlo como "normal" por un fenómeno matemático donde el punto cae fuera de la caja de decisión de sus árboles. La heurística garantiza que las violaciones físicas graves **siempre** sean detectadas, independientemente del resultado del modelo.

### Niveles de Severidad y umbrales

| Nivel | Presión | Caudal | Descripción |
|---|---|---|---|
| 🔴 **CRITICAL** | < 30 MCA | > 45 LPS | Rotura de tubería, fuga masiva |
| 🟠 **HIGH** | < 35 MCA | > 40 LPS | Fuga significativa, conexión no autorizada |
| 🟡 **MEDIUM** | < 45 MCA | > 35 LPS | Anomalía moderada, posible fuga incipiente |
| 🟢 **LOW** | Dentro de umbral general | | Desviación leve a monitorear |

---

## 5. API REST — Endpoints de Anomalías

**Prefijo:** `/api/anomalies`

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/analyze` | Analiza una lectura individual |
| `POST` | `/simulate` | Inyecta una anomalía crítica simulada (aleatorizada) |
| `POST` | `/analyze/batch` | Analiza múltiples lecturas |
| `GET` | `/recent` | Anomalías recientes (filtrables por DMA y horas) |
| `GET` | `/moche/recent` | Anomalías recientes del sector Moche |
| `GET` | `/stats` | Estadísticas agregadas (últimas 24h y 7 días) |
| `GET` | `/moche/stats` | Estadísticas del sector Moche |
| `GET` | `/{anomaly_id}` | Detalle de una anomalía por ID |

### Endpoint de Simulación (`POST /simulate`)

Genera una anomalía **crítica aleatoria** seleccionando uno de 4 escenarios de falla realistas:

| Escenario | Presión (MCA) | Caudal (LPS) | Descripción física |
|---|---|---|---|
| 1 — Rotura de tubería | 10.0 – 28.0 | 20.0 – 30.0 | Caída severa de presión |
| 2 — Conexión clandestina | 48.0 – 60.0 | 46.0 – 72.0 | Spike de caudal sin caída de presión |
| 3 — Fuga combinada | 15.0 – 27.0 | 50.0 – 68.0 | Presión baja + caudal alto simultáneo |
| 4 — Fuga gradual | 20.0 – 29.5 | 28.0 – 35.0 | Presión cerca del límite crítico |

---

## 6. Frontend — Dashboard de Analítica IA

### Componentes visuales

#### 6.1 KPI Cards (fila superior)
- **Modelo:** Nombre del algoritmo (Isolation Forest)
- **Umbral de Detección:** Score mínimo para clasificar como anomalía (0.75)
- **Total Anomalías:** Cantidad en las últimas 24h
- **Tasa de Detección:** Score promedio de las anomalías detectadas

#### 6.2 Distribución por Severidad (Pie Chart)
Muestra la proporción de anomalías por nivel (CRITICAL / HIGH / MEDIUM / LOW) en las últimas 24h. Los colores son: rojo, naranja, amarillo, verde.

#### 6.3 Historial de Detecciones (Bar Chart)
Agrupa el conteo de anomalías por día para los últimos 7 días, con etiquetas en español (lun, mar, mié...).

#### 6.4 Información del Modelo ML
Descripción del algoritmo: variables de entrada, tipo de entrenamiento y método de detección.

#### 6.5 Matriz de Comportamiento (Scatter Chart)
Grafica cada lectura de telemetría de las últimas 24h en un plano **Presión vs. Caudal**:
- 🔵 **Puntos azules:** Comportamiento normal
- 🔴 **Puntos rojos:** Anomalía detectada

Se aplica un jitter visual (±0.75 unidades) para evitar superposición de puntos con valores similares.

#### 6.6 Últimas Anomalías Detectadas (Tabla)
Muestra hasta 20 anomalías recientes con:
- Fecha/Hora (en zona horaria local del navegador — Lima UTC-5)
- DMA ID
- Score del modelo
- Nivel de severidad (badge de color)
- Estado (PENDING / RESOLVED)
- Pérdida estimada en m³

**Botón "Simular Anomalía Crítica":** Llama al endpoint `POST /simulate`, luego invalida las queries de React Query para actualizar la tabla **en tiempo real** sin recargar la página.

#### 6.7 Explicabilidad del Modelo (Última Anomalía)
Sección que desglosa por qué el modelo clasificó el último evento como anomalía:

**Impacto relativo (barras de progreso):**
```
Impacto Presión = |pressure_variation| / 55.2
Impacto Caudal  = |flow_variation|     / 25.4
```
Ambos se normalizan para sumar 100%, mostrando qué variable "pesó más" en la detección.

**Valores Registrados (panel derecho):**
- **Presión medida:** `55.2 + pressure_variation` MCA (valor real del sensor)
- **Caudal medido:** `25.4 + flow_variation` LPS (valor real del sensor)
- **Variación Presión:** Desviación respecto al baseline normal (negativa = caída)
- **Variación Caudal:** Desviación respecto al baseline normal (positiva = exceso)
- **Score Final:** Valor 0–1 del modelo ML

> Si la anomalía proviene del sistema de mock antiguo y no tiene datos de variación, se muestra el mensaje: *"Sin datos de variación registrados para esta anomalía."*

---

## 7. Zona Horaria

**Problema:** El backend almacena todos los timestamps en **UTC** sin sufijo `Z`. El navegador, al crear `new Date("2026-07-14T05:43:00")` sin zona horaria explícita, lo interpretaba como hora local, mostrando +5h en Lima (UTC-5).

**Solución en `format.ts`:**
```typescript
const utcStr = iso.endsWith('Z') || iso.includes('+') ? iso : iso + 'Z';
const d = new Date(utcStr);
// El navegador convierte UTC → hora local del usuario (Lima, UTC-5)
```

Así `05:43 UTC` se muestra correctamente como `00:43 AM` en Lima.

---

## 8. Actualización en Tiempo Real (React Query)

La tabla de anomalías se actualiza automáticamente de dos formas:

1. **Polling automático:** El hook `useRecentAnomalies` hace refetch cada **30 segundos** (`refetchInterval: 30000`)
2. **Actualización inmediata post-simulación:** Al presionar el botón de simulación, el handler invalida las queries con las claves exactas:

```typescript
await queryClient.invalidateQueries({ queryKey: ['anomalies-recent'] });
await queryClient.invalidateQueries({ queryKey: ['anomaly-stats'] });
await queryClient.invalidateQueries({ queryKey: ['telemetry-history'] });
```

> **Nota importante:** Las claves deben coincidir *exactamente* con las definidas en `hooks.ts`. Una discrepancia hace que React Query no encuentre la caché y la actualización no ocurre.

---

## 9. Datos Simulados (Mock Data)

### Generación automática de fallback
Si la base de datos no tiene anomalías para el período consultado, `AnomalyService.get_recent_anomalies()` llama a `_generate_mock_anomalies()`:

1. Genera 96 lecturas históricas via `MockTelemetryProvider`
2. Filtra solo las que cumplan umbrales de anomalía
3. Las persiste en la base de datos
4. Asigna un score fijo de **0.85**

### Scores de simulación manual

Al usar el botón "Simular Anomalía Crítica":
- Si el modelo ML calcula score ≥ 0.8 → se usa ese score
- Si el modelo ML calcula score < 0.8 (fenómeno de extremos fuera del rango de entrenamiento) → se **fuerza a 1.0**

---

## 10. Casos de Prueba Validados

Pruebas ejecutadas en el contenedor Docker `sgip-cap-backend`:

| Caso | Presión | Caudal | Severidad Esperada | Resultado |
|---|---|---|---|---|
| Lectura Normal | 55.5 MCA | 25.2 LPS | No anomalía | ✅ `False`, score 0.252 |
| Rotura de tubería | 20.0 MCA | 26.0 LPS | CRITICAL | ✅ `True`, score 1.0, CRITICAL |
| Spike de caudal | 52.0 MCA | 42.0 LPS | HIGH | ✅ `True`, score 1.0, HIGH |
| Presión y caudal límite | 43.0 MCA | 36.5 LPS | MEDIUM | ✅ `True`, score 1.0, MEDIUM |
| Presión baja moderada | 34.0 MCA | 26.0 LPS | HIGH | ✅ `True`, score 1.0, HIGH |

---

## 11. Hoja de Ruta — Migración a Datos Reales

Cuando se disponga de datos reales del sistema SCADA/IoT de Moche, los puntos de cambio son mínimos:

| Qué cambiar | Dónde | Descripción |
|---|---|---|
| Fuente de entrenamiento | `anomaly_service.py` → `_initialize_model()` | Reemplazar lecturas sintéticas por query a BD histórica |
| Proveedor de telemetría | `MockTelemetryProvider` → `RealTelemetryProvider` | Nuevo provider que lea de SCADA/API real |
| Baseline de variaciones | `anomaly_service.py` líneas 92-93 | Reemplazar `55.2` y `25.4` por promedios calculados de datos reales |
| Umbral de detección | `core/config.py` → `anomaly_threshold` | Ajustar según análisis de datos históricos reales |
| Umbrales físicos | `anomaly_service.py` y `_generate_mock_anomalies` | Ajustar rangos MCA/LPS según condiciones reales del sector Moche |

---

## 12. Dependencias Técnicas

**Backend:**
- `scikit-learn` — Isolation Forest
- `numpy` — Procesamiento de features
- `joblib` — Serialización del modelo (preparado para persistencia en disco)
- `fastapi` — Framework API REST
- `sqlalchemy` — ORM para PostgreSQL

**Frontend:**
- `@tanstack/react-query` — Gestión de estado del servidor y caché
- `recharts` — Visualizaciones (Pie, Bar, Scatter)
- `lucide-react` — Iconos

---

*Documentación generada el 14/07/2026. El módulo fue desarrollado de forma iterativa validando cada componente en entorno Docker (contenedores `sgip-cap-backend` y `sgip-cap-frontend`).*
