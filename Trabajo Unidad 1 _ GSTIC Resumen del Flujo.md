A nivel usuario, el **SGIP-CAP** se verá como una aplicación web profesional con menú lateral y varias secciones. Al ingresar, el usuario verá un **dashboard ejecutivo** con indicadores principales como DMAs monitoreados, incidencias activas, alertas críticas, tiempo promedio de detección y posibles pérdidas estimadas. 

Desde la vista de **monitoreo hidráulico** , podrá observar gráficos en tiempo real de presión y caudal por sector. En el **mapa de DMAs** , cada zona aparecerá con colores según su estado: verde si está normal, amarillo si hay sospecha y rojo si se detecta una posible fuga. 

Cuando el sistema detecte una anomalía, aparecerá una alerta visual indicando el sector afectado, la caída de presión, el aumento de caudal y la severidad. Automáticamente se generará un **ticket de incidencia ITIL** , que el usuario podrá revisar, clasificar, asignar, atender y cerrar desde el módulo de incidencias. 

En resumen, el usuario no verá solo gráficos, sino una plataforma completa para **monitorear sectores, detectar fugas, gestionar incidencias y tomar decisiones operativas** . 

## **Flujo de funcionamiento del sistema SGIP-CAP** 

Datos hidráulicos mock / CSV / SCADA exportado ↓ Normalización de datos ↓ Almacenamiento en base de datos ↓ Análisis con IA ↓ Detección de anomalía ↓ Generación de alerta ↓ Creación de incidencia ITIL ↓ Visualización en dashboard ↓ Seguimiento y cierre del ticket 

## **1. Ingreso de datos hidráulicos** 

El sistema recibe lecturas de presión y caudal de los sectores o DMAs monitoreados. 

En el MVP, estos datos pueden venir de: 

- datos simulados; 

- archivos CSV; 

- escenarios mock. 

En una fase futura, podrían venir de exportaciones reales de SEDALIB, como datos históricos de SCADA. 

## **2. Normalización de la información** 

Antes de analizar los datos, el sistema los transforma a un formato estándar. 

Esto permite que no importe si los datos vienen de mock, CSV o una exportación real. Todos se convierten al mismo modelo interno: 

Fecha y hora DMA Sensor Presión Caudal Fuente de datos Estado de calidad 

## **3. Registro de lecturas** 

Las lecturas normalizadas se guardan en la base de datos. 

Esto permite consultar: 

- historial de presión; 

- historial de caudal; 

- comportamiento por DMA; 

- eventos anteriores; 

- evolución de las anomalías. 

## **4. Análisis con inteligencia artificial** 

El motor de IA analiza el comportamiento de presión y caudal. 

El sistema busca patrones anormales, por ejemplo: 

Presión bajando de forma brusca Caudal subiendo de forma anormal Cambios extraños durante la noche Comportamientos fuera del rango normal 

## **5. Detección de anomalía** 

Si el modelo identifica un comportamiento sospechoso, el sistema clasifica el estado del sector. 

Por ejemplo: 

Normal Sospechoso Crítico 

Un caso crítico sería: 

El Porvenir 02: Presión disminuye Caudal aumenta Probable fuga detectada 

## **6. Generación de alerta** 

Cuando la anomalía supera cierto nivel de riesgo, el sistema genera una alerta visual. 

La alerta aparece en el dashboard con información como: 

DMA afectado Nivel de severidad Presión actual 

Caudal actual Hora de detección Probabilidad o score de anomalía 

## **7. Creación automática de incidencia ITIL** 

La alerta no queda solo como aviso visual. El sistema genera automáticamente una incidencia tipo ticket. 

El ticket contiene: 

Código de incidencia DMA afectado Descripción del problema Prioridad Estado SLA estimado Fecha y hora de creación Recomendación operativa 

Ejemplo: 

INC-2026-001 Posible fuga detectada en DMA El Porvenir 02 Prioridad: Alta Estado: Nuevo SLA: 4 horas 

## **8. Visualización en el frontend** 

El usuario puede ver la situación desde diferentes vistas: 

Dashboard Ejecutivo Monitoreo Hidráulico Mapa de DMAs Incidencias ITIL Detalle del DMA Analítica IA 

El mapa muestra los sectores por color: 

Verde: normal Amarillo: sospechoso Rojo: fuga detectada 

## **9. Seguimiento de la incidencia** 

El ticket puede cambiar de estado según el avance de atención: 

Nuevo Clasificado Asignado En atención Resuelto Cerrado 

Esto permite simular una mesa de servicios alineada a ITIL 4. 

## **10. Actualización de KPIs** 

Finalmente, el sistema actualiza indicadores de gestión como: 

Incidencias activas DMAs críticos Tiempo promedio de detección SLA en riesgo Pérdida estimada de agua Cantidad de anomalías detectadas 

## **Resumen del flujo en una frase** 

El **SGIP-CAP recibe datos hidráulicos de presión y caudal, los normaliza, los analiza con IA, detecta posibles fugas, genera alertas, crea incidencias bajo ITIL 4 y permite hacer seguimiento operativo desde un dashboard profesional.** 

