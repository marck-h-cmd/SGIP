# SGIP-CAP - Documentacion de Vistas del Sistema

## Glosario de Acrónimos y Términos

| Acrónimo | Significado | Descripción |
|----------|-------------|-------------|
| **SGIP** | Sistema de Gestión Integral de Pérdidas | Sistema principal para la detección, análisis y gestión de pérdidas de agua en la red de distribución. |
| **CAP** | Centro de Análisis y Prevención | Unidad organizacional que opera el sistema para prevenir y mitigar pérdidas. |
| **DMA** | District Metered Area (Área Medida por Distrito) | Zona de la red de distribución de agua delimitada y monitoreada individualmente, con medición de caudal de entrada. Permite identificar pérdidas por sector. Ejemplo: `DMA-MO-01` = sector Moche 01. |
| **SEDALIB** | Sociedad de Servicios de Agua Potable de Trujillo | Empresa de servicios de agua potable que opera en la región La Libertad, Perú. |
| **SCADA** | Supervisory Control and Data Acquisition | Sistema de control y adquisición de datos de proceso. Fuente principal de datos hidráulicos (presión, caudal) en tiempo real. |
| **MCA** | Metros de Columna de Agua | Unidad de medida de presión hidráulica. 1 MCA ≈ 0.098 bar. Ejemplo: 55 MCA = ~5.4 bar. |
| **LPS** | Litros Por Segundo | Unidad de medida de caudal (flujo de agua). Ejemplo: 25 LPS = 25 litros de agua pasando por un punto por segundo. |
| **m³** | Metros Cúbicos | Unidad de volumen. 1 m³ = 1,000 litros. Se usa para medir pérdidas de agua acumuladas. |
| **SLA** | Service Level Agreement (Acuerdo de Nivel de Servicio) | Compromiso formal de tiempo de respuesta/resolución para incidentes. Ejemplo: un incidente CRITICAL debe resolverse en ≤ 4 horas. |
| **ITIL** | Information Technology Infrastructure Library | Marco de buenas prácticas para la gestión de servicios de TI. El sistema usa el ciclo de vida ITIL para incidentes: NEW → CLASSIFIED → ASSIGNED → IN_PROGRESS → RESOLVED → CLOSED. |
| **ML** | Machine Learning (Aprendizaje Automático) | Modelo de inteligencia artificial que detecta anomalías de forma no supervisada. |
| **JWT** | JSON Web Token | Token de autenticación usado para identificar usuarios en cada petición a la API. |
| **API** | Application Programming Interface (Interfaz de Programación de Aplicaciones) | Conjunto de endpoints HTTP/WS que expone el backend para consumir datos y ejecutar acciones. |
| **WebSocket** | Protocolo de comunicación bidireccional | Conexión persistente entre frontend y backend para recibir actualizaciones en tiempo real (lecturas de sensores). |
| **KPI** | Key Performance Indicator (Indicador Clave de Desempeño) | Métrica cuantificable que mide el rendimiento del sistema de distribución. |
| **MVP** | Minimum Viable Product (Producto Mínimo Viable) | Versión inicial del sistema con funcionalidades esenciales para validación. |

---

## 1. Vista de Login (`/login`)

### Qué es
Página de autenticación que controla el acceso al sistema. Es la primera pantalla que ve el usuario.

### Para qué sirve
- Identificar al usuario antes de permitir acceso al panel de control.
- Generar un token JWT que se usa en todas las peticiones posteriores.

### Qué muestra
- Formulario con campos: **Usuario** y **Contraseña**.
- Botón "Ingresar" con indicador de carga.
- Mensajes de error cuando las credenciales son incorrectas.
- Indicador visual "SGIP-CAP - SEDALIB — Sector Moche".

### Credenciales por defecto (MVP)
| Campo | Valor |
|-------|-------|
| Usuario | `admin` |
| Contraseña | `admin123` |

### Backend asociado
- **Endpoint**: `POST /api/auth/login`
- **Respuesta**: Token JWT con expiración de 30 minutos.

---

## 2. Vista de Dashboard (`/dashboard`)

### Qué es
Panel de control principal que ofrece una vista consolidada del estado operativo del sistema de distribución de agua.

### Para qué sirve
- Dar al operador una **visión general rápida** del estado del sector sin necesidad de navegar a múltiples secciones.
- Detectar **alertas críticas** de forma inmediata al ingresar al sistema.
- Monitorear los **KPIs más importantes** en un solo lugar.

### Qué muestra

#### Barra de Alertas Críticas
Si existen alertas críticas sin atender, aparece una barra roja en la parte superior con el número de alertas y un botón para ir a la sección de Incidentes.

#### Tarjetas KPI (4 indicadores principales)
| KPI | Descripción | Fuente |
|-----|-------------|--------|
| DMAs Monitoreados | Número total de zonas de distribución activas | API de DMAs |
| Incidencias Activas | Incidentes abiertos (no resueltos/cerrados) | API de Incidentes |
| Tiempo Prom. Detección | Horas promedio entre la detección de una anomalía y su registro como incidente | API de KPIs |
| Pérdida Estimada | Volumen de agua perdida estimado en metros cúbicos por día | API de KPIs |

#### Gráfico de Tendencia de Presión y Caudal
- Gráfico de líneas duales (eje Y izquierdo: presión en MCA, eje Y derecho: caudal en LPS).
- Muestra la evolución temporal de las lecturas del sector Moche.
- Permite identificar picos, caídas y tendencias anómalas.

#### Panel de Lectura Actual
- Muestra la lectura más reciente del sensor principal:
  - **Presión** (MCA) con badge de calidad.
  - **Caudal** (LPS).
  - ID del DMA y bandera de calidad (`GOOD`, `SUSPECT`, `BAD`).

#### Panel de Cumplimiento SLA
- Indicador circular con el porcentaje de cumplimiento de acuerdos de nivel de servicio.
- Objetivo: >95%.

#### Últimas Anomalías
- Lista de las 5 anomalías más recientes con:
  - Descripción
  - Fecha/hora de detección
  - Badge de severidad (CRITICAL, HIGH, MEDIUM, LOW)

#### Incidentes Recientes
- Lista de los 5 incidentes más recientes con:
  - Código del ticket (ej: `INC-20260709-001`)
  - Título del incidente
  - Badge de estado (NEW, IN_PROGRESS, RESOLVED, etc.)

### Backend asociado
- `GET /api/kpis/moche/executive` → KPIs ejecutivos
- `GET /api/telemetry/moche/latest` → Última lectura
- `GET /api/alerts/` → Alertas activas
- `GET /api/anomalies/moche/recent` → Anomalías recientes
- `GET /api/incidents/` → Incidentes
- `GET /api/telemetry/moche/trends` → Tendencias

---

## 3. Vista de Monitoreo en Tiempo Real (`/monitoring`)

### Qué es
Vista de operación en vivo que muestra las lecturas de sensores hidráulicos actualizadas en tiempo real mediante conexión WebSocket.

### Para qué sirve
- **Supervisar en tiempo real** la presión y caudal del sector Moche.
- Detectar **cambios bruscos** que indiquen fugas, roturas o conexiones clandestinas.
- Verificar el estado de la **conexión en tiempo real** con los sensores.
- Revisar **eventos anómalos** detectados automáticamente.

### Qué muestra

#### Tarjetas de Estado en Vivo (4 paneles)
| Panel | Descripción |
|-------|-------------|
| Presión Actual | Valor en MCA del sensor, con badge de calidad |
| Caudal Actual | Valor en LPS del sensor, con ID del DMA |
| Conexión WebSocket | Estado de la conexión: `Conectado` (verde), `Conectando...` (amarillo), `Desconectado` (rojo). Incluye botón de reconexión. |
| Fuente de Datos | Tipo de proveedor (mock, csv, scada) y sensor activo |

#### Gráficos de Área - Tendencias
- **Gráfico de Presión**: Área con gradiente que muestra la tendencia temporal de presión.
- **Gráfico de Caudal**: Área con gradiente que muestra la tendencia temporal de caudal.
- Ambos gráficos se actualizan con datos de las últimas 24 horas.

#### Tabla de Eventos Detectados
Columnas de la tabla:
| Columna | Descripción |
|---------|-------------|
| Fecha | Fecha y hora de detección |
| DMA | Zona de distribución donde se detectó |
| Score | Valor de confianza del modelo ML (0-1) |
| Severidad | CRITICAL / HIGH / MEDIUM / LOW |
| Estado | PENDING / CONFIRMED / REJECTED / RESOLVED |
| Pérdida Est. | Volumen estimado de pérdida en m³ |

### Conexión WebSocket
- URL: `ws://localhost:8000/ws/{client_id}`
- Mensajes recibidos: tipo `TELEMETRY_UPDATE` con datos de lectura.
- Reconexión automática cada 5 segundos si se pierde la conexión.

### Backend asociado
- WebSocket: `/ws/{client_id}`
- `GET /api/telemetry/moche/latest`
- `GET /api/telemetry/moche/trends`
- `GET /api/anomalies/moche/recent`

---

## 4. Vista de Mapa de DMAs (`/dmas`)

### Qué es
Vista geográfica interactiva que muestra la ubicación de todas las zonas de distribución (DMAs) en un mapa, con sus estados operativos.

### Para qué sirve
- Visualizar la **distribución geográfica** de las zonas monitoreadas.
- Identificar de forma visual qué DMAs tienen problemas (por color del marcador).
- Acceder rápidamente al detalle de cualquier DMA haciendo clic.
- Comprender la **cobertura territorial** del sistema.

### Qué muestra

#### Tarjetas Resumen de DMAs (fila superior)
Cada DMA se muestra como una tarjeta clickeable con:
- Código (ej: `DMA-MO-01`)
- Nombre (ej: `Moche 01`)
- Distrito (ej: `Moche`)
- Badge de estado (ACTIVE, WARNING, CRITICAL)
- Lecturas actuales: Presión (P) y Caudal (Q)

#### Mapa Interactivo (Leaflet/OpenStreetMap)
- Centro: Trujillo, Perú (coordenadas: -8.12, -79.02)
- **Marcadores coloreados** según estado:
  - Verde: `ACTIVE` (operativo)
  - Amarillo: `WARNING` (precaución)
  - Rojo: `CRITICAL` (crítico)
- **Popup al hacer clic** en un marcador:
  - Nombre y código del DMA
  - Badge de estado
  - Lecturas actuales de presión y caudal
  - Botón "Ver detalle →"

#### DMAs configurados en el sistema
| Código | Nombre | Distrito | Latitud | Longitud |
|--------|--------|----------|---------|----------|
| DMA-MO-01 | Moche 01 | Moche | -8.1700 | -79.0050 |
| DMA-EP-01 | El Porvenir 01 | El Porvenir | -8.0800 | -79.0150 |
| DMA-EP-02 | El Porvenir 02 | El Porvenir | -8.0750 | -79.0200 |
| DMA-VL-01 | Víctor Larco 01 | Víctor Larco | -8.1400 | -79.0500 |
| DMA-LE-01 | La Esperanza 01 | La Esperanza | -8.0600 | -79.0400 |

### Backend asociado
- `GET /api/dmas/` → Lista de DMAs
- `GET /api/telemetry/latest` → Últimas lecturas por DMA

---

## 5. Vista de Detalle de DMA (`/dmas/:id`)

### Qué es
Vista detallada de un DMA específico que muestra toda la información operativa, histórica y de incidents de una zona de distribución.

### Para qué sirve
- Realizar un **análisis profundo** del comportamiento de un DMA particular.
- Revisar el **historial de presión y caudal** para identificar tendencias.
- Ver los **sensores instalados** y su estado.
- Consultar las **anomalías e incidentes** específicos de ese DMA.

### Qué muestra

#### Encabezado del DMA
- Nombre, código y distrito
- Badge de estado
- Población beneficiada (si está disponible)
- Botón "Volver al mapa"

#### Tarjetas KPI del DMA (4 indicadores)
| KPI | Descripción |
|-----|-------------|
| Presión Actual | Lectura más reciente en MCA |
| Caudal Actual | Lectura más reciente en LPS |
| Nivel de Riesgo | Clasificación de riesgo + anomalías en 24h |
| Pérdida Estimada | Volumen de pérdida en m³/día |

#### Gráficos de Historial (2 gráficos de líneas)
- **Historial de Presión**: Evolución temporal de la presión.
- **Historial de Caudal**: Evolución temporal del caudal.

#### Panel de Sensores
Lista de sensores instalados en el DMA:
| Campo | Descripción |
|-------|-------------|
| Nombre/Código | Identificador del sensor (ej: `SENS-MO-01-P`) |
| Tipo | `PRESSURE` (presión) o `FLOW` (caudal) |
| Unidad | MCA o LPS |
| Estado | ACTIVE, INACTIVE, MAINTENANCE |

#### Panel de Anomalías Recientes
Lista de anomalías detectadas en ese DMA con score, severidad y fecha.

#### Tabla de Incidentes del Sector
Tabla con todos los incidentes registrados para ese DMA con código, título, prioridad, estado, asignado y fecha de creación.

### Backend asociado
- `GET /api/dmas/{dma_id}` → Info del DMA
- `GET /api/dmas/{dma_id}/sensors` → Sensores
- `GET /api/dmas/{dma_id}/kpis` → KPIs
- `GET /api/telemetry/history/{dma_id}` → Historial
- `GET /api/incidents/` → Incidentes filtrados
- `GET /api/anomalies/recent` → Anomalías

---

## 6. Vista de Incidentes (`/incidents`)

### Qué es
Gestor completo de incidentes que sigue el marco ITIL para el ciclo de vida de incidentes de pérdida de agua.

### Para qué sirve
- **Registrar y rastrear** todos los incidentes detectados en el sistema.
- **Gestionar el flujo de trabajo** ITIL: clasificar, asignar, resolver, escalar y cerrar incidentes.
- **Monitorear el cumplimiento de SLAs** y detectar incidentes que están por vencerse.
- Mantener un **historial completo** (audit log) de todas las acciones realizadas sobre cada incidente.

### Qué muestra

#### Tarjetas de Resumen (5 indicadores)
| KPI | Descripción |
|-----|-------------|
| Total | Número total de incidentes |
| Activos | Incidentes no resueltos ni cerrados |
| Escalados | Incidentes que requieren atención superior |
| SLA Vencido | Incidentes cuyo plazo de SLA ya expiró |
| Resueltos | Incidentes con estado RESOLVED o CLOSED |

#### Filtros y Búsqueda
- **Barra de búsqueda**: Buscar por código, título o nombre del DMA.
- **Filtros de prioridad**: TODOS, CRITICAL, HIGH, MEDIUM, LOW.
- **Filtros de estado**: TODOS, NEW, CLASSIFIED, ASSIGNED, IN_PROGRESS, ESCALATED, RESOLVED, CLOSED.

#### Tabla de Incidentes
Columnas:
| Columna | Descripción |
|---------|-------------|
| Código | Identificador único (ej: `INC-20260709-001`) |
| Título | Descripción breve del incidente |
| DMA | Zona de distribución afectada |
| Prioridad | CRITICAL (rojo) / HIGH (naranja) / MEDIUM (amarillo) / LOW (verde) |
| Estado | Badge del estado actual |
| Asignado | Persona o equipo responsable |
| SLA | Fecha límite de resolución (en rojo si vencido) |
| Creado | Fecha y hora de creación |
| Acciones | Botones de acción rápida (resolver, escalar, ver detalle) |

#### Paginación
- 10 incidentes por página.
- Navegación con botones "Anterior" / "Siguiente".
- Indicador de rango mostrado y total.

#### Modal de Detalle de Incidente
Al hacer clic en un incidente, se abre un modal con dos pestañas:

**Pestaña "Detalles":**
- Descripción completa del incidente.
- Datos: DMA, asignado a, SLA due, fecha de creación.
- ID de anomalía asociada (si existe).
- **Acciones ITIL**: Botones para cambiar el estado según las transiciones válidas:
  - `NEW` → Clasificar, Cancelar
  - `CLASSIFIED` → Asignar, Cancelar
  - `ASSIGNED` → Iniciar, Cancelar
  - `IN_PROGRESS` → Resolver, Escalar, Cancelar
  - `ESCALATED` → Reanudar, Resolver, Cancelar
  - `RESOLVED` → Cerrar, Reabrir

**Pestaña "Historial" (Audit Log):**
- Timeline vertical con todos los cambios de estado.
- Cada entrada incluye: acción, usuario, timestamp y comentarios.
- Iconos distintivos por tipo de acción (cambio de estado, comentario, edición).

### Flujo ITIL de Estados
```
NEW → CLASSIFIED → ASSIGNED → IN_PROGRESS → RESOLVED → CLOSED
                                    ↓              ↑
                                ESCALATED ────────┘
```

### Backend asociado
- `GET /api/incidents/` → Lista con filtros y paginación
- `GET /api/incidents/{id}` → Detalle
- `PATCH /api/incidents/{id}/status` → Cambiar estado
- `POST /api/incidents/{id}/assign` → Asignar
- `POST /api/incidents/{id}/comment` → Comentar
- `POST /api/incidents/{id}/escalate` → Escalar
- `POST /api/incidents/{id}/resolve` → Resolver
- `POST /api/incidents/{id}/close` → Cerrar
- `GET /api/incidents/{id}/audit-log` → Historial
- `GET /api/incidents/sla/metrics` → Métricas SLA

---

## 7. Vista de Analytics (`/analytics`)

### Qué es
Centro de análisis de anomalías que muestra el funcionamiento del modelo de Machine Learning, sus resultados y la explicabilidad de las detecciones.

### Para qué sirve
- **Entender cómo funciona** el modelo de detección de anomalías (Isolation Forest).
- **Visualizar la distribución** de anomalías por severidad.
- **Analizar patrones** de comportamiento presión vs caudal.
- **Evaluar la explicabilidad** del modelo: por qué determinó que algo es una anomalía.
- **Simular anomalías** para probar la respuesta del sistema.

### Qué muestra

#### Tarjetas de Estado del Modelo (4 paneles)
| KPI | Descripción |
|-----|-------------|
| Modelo | Nombre del algoritmo: "Isolation Forest" |
| Umbral de Detección | Score mínimo para clasificar como anomalía (0.75) |
| Total Anomalías | Número de anomalías en las últimas 24 horas |
| Tasa de Detección | Score promedio de las anomalías detectadas |

#### Gráfico de Distribución por Severidad
- Gráfico circular (Pie Chart) con distribución de anomalías por nivel:
  - CRITICAL (rojo)
  - HIGH (naranja)
  - MEDIUM (amarillo)
  - LOW (verde)

#### Gráfico de Historial de Detecciones (7 días)
- Gráfico de barras que muestra el número de anomalías detectadas por día durante la última semana.
- Permite identificar patrones temporales (¿hay más anomalías los fines de semana?).

#### Información del Modelo ML
Sección que explica en detalle:
| Campo | Valor |
|-------|-------|
| Algoritmo | Ensemble de árboles de aislamiento |
| Variables de Entrada | Presión (MCA), Caudal (LPS), Hora del día, Día de la semana, Media móvil 1h, Desviación estándar |
| Entrenamiento | Automático — ventana de 30 días |
| Método | Detección no supervisada. El modelo aprende el comportamiento normal y detecta desviaciones. Arquitectura preparada para migrar a LSTM. |

#### Matriz de Comportamiento (Presión vs Caudal)
- Gráfico de dispersión (Scatter Plot) que grafica cada lectura de telemetría:
  - **Puntos azules**: Comportamiento normal.
  - **Puntos rojos**: Anomalía detectada.
- Permite ver visualmente la separación entre comportamiento normal y anómalo.

#### Tabla de Últimas Anomalías Detectadas
Columnas: Fecha, DMA, Score, Severidad, Estado, Pérdida Estimada.
- Incluye botón "Simular Anomalía Crítica" que inyecta datos artificiales con valores críticos aleatorios para probar el pipeline completo.

#### Explicabilidad del Modelo (Última Anomalía)
Sección que muestra por qué el modelo determinó que el evento más reciente es una anomalía:
- **Impacto de la Presión**: Porcentaje de influencia de la variación de presión.
- **Impacto del Caudal**: Porcentaje de influencia de la variación de caudal.
- **Valores Registrados**: Presión y caudal medidos, variaciones y score final.

### Backend asociado
- `GET /api/anomalies/moche/stats` → Estadísticas
- `GET /api/anomalies/moche/recent` → Anomalías recientes
- `GET /api/telemetry/history/DMA-MO-01` → Historial de telemetría
- `POST /api/anomalies/simulate` → Simular anomalía

---

## 8. Vista de Reportes (`/reports`)

### Qué es
Centro de generación y exportación de reportes operativos e históricos del sector de distribución.

### Para qué sirve
- Generar **reportes diarios, semanales o personalizados** del sector Moche.
- **Exportar datos** en múltiples formatos (PDF, Excel, CSV) para análisis externos o presentaciones.
- Revisar **tendencias históricas** de presión, caudal, anomalías e incidentes.
- Apoyar la **toma de decisiones** gerenciales con datos consolidados.

### Qué muestra

#### Selector de Tipo de Reporte (3 pestañas)
| Pestaña | Descripción |
|---------|-------------|
| Reporte Diario | Resumen de un día específico |
| Reporte Semanal | Resumen de los últimos 7 días |
| Personalizado | Rango de fechas definido por el usuario (máx. 90 días) |

---

### 8.1 Reporte Diario

**Selector de Fecha**: Calendario para elegir la fecha del reporte (no puede ser futura).

**Métricas Principales:**
| Métrica | Descripción |
|---------|-------------|
| Presión Promedio | Promedio del día en MCA |
| Caudal Promedio | Promedio del día en LPS |
| Anomalías | Total de anomalías detectadas |
| Incidentes | Total de incidentes generados |

**Gráfico de Evolución Diaria:**
- Gráfico de áreas con dos series: Presión y Caudal.
- Muestra las 24 horas del día seleccionado.

---

### 8.2 Reporte Semanal

**Resumen de la Semana:**
| Métrica | Descripción |
|---------|-------------|
| Lecturas Totales | Número total de lecturas de sensores |
| Anomalías Detectadas | Total de anomalías en la semana |
| Nuevos Incidentes | Incidentes creados en el período |
| Pérdida Estimada | Volumen total de pérdida en m³ (estimado por ML) |

**Gráfico de Promedios y Comportamiento Diario:**
- Gráfico de barras comparativo de presión y caudal promedio por día de la semana.

---

### 8.3 Reporte Personalizado

**Formulario de Fechas:**
- Fecha Inicial y Fecha Final.
- Validación: la fecha inicial debe ser anterior a la final.
- Límite: el rango no puede exceder 90 días.

**Resultados del Período:**
| Métrica | Descripción |
|---------|-------------|
| Total Lecturas | Lecturas en el período |
| Anomalías Detectadas | Anomalías en el período |
| Presión Promedio | Promedio general en MCA |
| Caudal Promedio | Promedio general en LPS |

**Gestión de Mantenimiento:**
| Métrica | Descripción |
|---------|-------------|
| Incidentes Creados | Tickets generados en el período |
| Incidentes Resueltos | Tickets resueltos en el período |

---

### Formatos de Exportación
Cada reporte puede exportarse en 3 formatos:
| Formato | Extensión | Uso típico |
|---------|-----------|------------|
| Excel (XLSX) | `.xlsx` | Análisis de datos, tablas dinámicas, gráficos propios |
| PDF | `.pdf` | Presentaciones, impresión, distribución formal |
| CSV | `.csv` | Importación a otros sistemas, análisis con scripts |

### Backend asociado
- `GET /api/reports/moche/daily` → Reporte diario
- `GET /api/reports/moche/weekly` → Reporte semanal
- `GET /api/reports/moche/custom` → Reporte personalizado
- `GET /api/reports/v2/moche/{type}?format={fmt}` → Exportación v2

---

## 9. Vista de Configuración (`/settings`)

### Qué es
Panel de visualización de las variables de entorno y parámetros operativos del sistema.

### Para qué sirve
- **Auditar la configuración** actual del sistema sin modificar archivos.
- **Verificar** que los parámetros críticos estén correctamente configurados.
- **Documentar** los valores operativos para el equipo técnico.

### Qué muestra

#### Secciones de Configuración

| Sección | Parámetros |
|---------|-----------|
| **Fuente de Datos** | `DATA_PROVIDER` (mock/csv/scada), `CSV_DATA_PATH` |
| **Detección de Anomalías** | `ANOMALY_THRESHOLD` (0.75), `TRAINING_WINDOW_DAYS` (30) |
| **Sector** | `TARGET_DMA` (DMA-MO-01), `TARGET_DMA_NAME` (Moche 01) |
| **Base de Datos** | `DATABASE_URL` (PostgreSQL), `REDIS_URL` (Redis) |
| **Seguridad** | `ALGORITHM` (HS256), `ACCESS_TOKEN_EXPIRE_MINUTES` (30) |

> **Nota**: Esta vista es de solo lectura en la versión actual. Los valores se configuran mediante variables de entorno o archivo `.env`.

---

## 10. API Endpoints (Referencia Técnica)

### Autenticación
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/auth/login` | Autenticar y obtener token JWT |
| GET | `/api/auth/me` | Obtener información del usuario actual |
| POST | `/api/auth/verify` | Verificar validez del token |

### Telemetría
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/telemetry/latest` | Últimas lecturas de sensores |
| GET | `/api/telemetry/history/{dma_id}` | Historial de lecturas por DMA |
| GET | `/api/telemetry/summary/{dma_id}` | Resumen de un DMA |
| GET | `/api/telemetry/trends/{dma_id}` | Tendencias de presión/caudal |
| GET | `/api/telemetry/moche/trends` | Tendencias del sector Moche |
| GET | `/api/telemetry/moche/latest` | Última lectura de Moche |
| GET | `/api/telemetry/dmas` | Lista de todos los DMAs |

### Anomalías
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/anomalies/analyze` | Analizar una lectura |
| POST | `/api/anomalies/simulate` | Inyectar anomalía simulada |
| POST | `/api/anomalies/analyze/batch` | Analizar múltiples lecturas |
| GET | `/api/anomalies/dma/{dma_id}` | Análisis por DMA |
| GET | `/api/anomalies/moche/analyze` | Análisis del sector Moche |
| GET | `/api/anomalies/recent` | Anomalías recientes |
| GET | `/api/anomalies/moche/recent` | Anomalías recientes de Moche |
| GET | `/api/anomalies/stats` | Estadísticas de anomalías |
| GET | `/api/anomalies/moche/stats` | Estadísticas de Moche |
| GET | `/api/anomalies/{anomaly_id}` | Detalle de una anomalía |

### Incidentes
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/incidents/create` | Crear incidente desde anomalía |
| POST | `/api/incidents/create-from-anomaly/{id}` | Crear desde ID de anomalía |
| GET | `/api/incidents/` | Listar incidentes (con filtros) |
| GET | `/api/incidents/moche` | Incidentes del sector Moche |
| GET | `/api/incidents/{ticket_id}` | Detalle de un incidente |
| GET | `/api/incidents/code/{code}` | Buscar por código |
| PATCH | `/api/incidents/{id}/status` | Cambiar estado (ITIL) |
| POST | `/api/incidents/{id}/assign` | Asignar responsable |
| POST | `/api/incidents/{id}/comment` | Agregar comentario |
| POST | `/api/incidents/{id}/escalate` | Escalar incidente |
| POST | `/api/incidents/{id}/resolve` | Resolver incidente |
| POST | `/api/incidents/{id}/close` | Cerrar incidente |
| POST | `/api/incidents/{id}/link-anomaly` | Vincular anomalía |
| GET | `/api/incidents/{id}/audit-log` | Historial de cambios |
| POST | `/api/incidents/check-sla-breaches` | Verificar vencimientos SLA |
| GET | `/api/incidents/sla/metrics` | Métricas de SLA |

### KPIs
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/kpis/executive` | KPIs ejecutivos globales |
| GET | `/api/kpis/moche/executive` | KPIs del sector Moche |
| GET | `/api/kpis/dma/{dma_id}` | KPIs por DMA |
| GET | `/api/kpis/dmas/all` | KPIs de todos los DMAs |
| GET | `/api/kpis/water-loss` | Métricas de pérdida de agua |
| GET | `/api/kpis/moche/water-loss` | Pérdida de agua de Moche |
| GET | `/api/kpis/sla-compliance` | Cumplimiento de SLA global |
| GET | `/api/kpis/moche/sla-compliance` | SLA de Moche |

### DMAs
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/dmas/` | Listar todos los DMAs |
| GET | `/api/dmas/moche` | Info del sector Moche |
| GET | `/api/dmas/{dma_id}` | Detalle de un DMA |
| GET | `/api/dmas/{dma_id}/summary` | Resumen de un DMA |
| GET | `/api/dmas/{dma_id}/status` | Estado actual de un DMA |
| GET | `/api/dmas/{dma_id}/sensors` | Sensores de un DMA |
| GET | `/api/dmas/{dma_id}/kpis` | KPIs de un DMA |

### Alertas
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/alerts/` | Listar todas las alertas |
| GET | `/api/alerts/{dma_id}` | Alertas por DMA |
| GET | `/api/alerts/summary` | Resumen de alertas |
| POST | `/api/alerts/{id}/acknowledge` | Reconocer alerta |
| POST | `/api/alerts/{id}/resolve` | Resolver alerta |
| GET | `/api/alerts/history` | Historial de alertas |

### Reportes
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/reports/daily` | Reporte diario |
| GET | `/api/reports/moche/daily` | Reporte diario de Moche |
| GET | `/api/reports/weekly` | Reporte semanal |
| GET | `/api/reports/moche/weekly` | Reporte semanal de Moche |
| GET | `/api/reports/custom` | Reporte personalizado |
| GET | `/api/reports/moche/custom` | Reporte personalizado de Moche |
| GET | `/api/reports/v2/{type}` | Reporte v2 (con exportación) |
| GET | `/api/reports/v2/moche/{type}` | Reporte v2 de Moche |

### WebSocket
| Endpoint | Descripción |
|----------|-------------|
| `WS /ws/{client_id}` | Conexión en tiempo real para actualizaciones de telemetría |

---

## 11. Arquitectura de la Aplicación

### Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Frontend | React + TypeScript (Vite) |
| UI Components | Tailwind CSS + Lucide Icons |
| Gráficos | Recharts |
| Mapa | Leaflet + OpenStreetMap |
| Estado/Cache | TanStack Query (React Query) |
| Backend | Python + FastAPI |
| Base de Datos | PostgreSQL |
| Cache | Redis |
| Tareas en Background | Celery |
| ML | scikit-learn (Isolation Forest) |
| WebSocket | FastAPI WebSocket |
| Autenticación | JWT (HS256) |

### Flujo de Datos
```
Sensores/SCADA → Data Provider → Backend (FastAPI)
                                      ↓
                              Anomaly Detection (ML)
                                      ↓
                         Alerts → Incidents (ITIL)
                                      ↓
                         Reports → Export (PDF/XLSX/CSV)
                                      ↓
                              Frontend (React)
                                      ↕
                              WebSocket (tiempo real)
```
