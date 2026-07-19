# Manual de Usuario - SGIP-CAP (Sistema de Gestión Integral de Pérdidas)

Este documento es el Manual de Usuario oficial del **SGIP-CAP (Sistema de Gestión Integral de Pérdidas — Sector Moche)** operado por **SEDALIB S.A.** El sistema está diseñado para la detección de anomalías, gestión de incidencias y monitoreo de telemetría de agua utilizando Inteligencia Artificial (Isolation Forest).

Este manual está dividido en tres grandes módulos funcionales, cada uno asignado a un responsable del equipo para su revisión, documentación gráfica y exposición:
- **Parte 1 (Daniel):** Acceso al Sistema, Dashboard Ejecutivo y Monitoreo en Tiempo Real.
- **Parte 2 (Marck):** Mapa de DMAs, Detalle de DMA y Gestión de Incidentes (ITIL).
- **Parte 3 (Mario):** Analítica IA, Centro de Reportes y Configuración del Sistema.

---

## Parte 1: Acceso, Dashboard y Monitoreo (Responsable: Daniel)

Esta sección cubre las funcionalidades de entrada al sistema y la supervisión de alto nivel, ideal para operadores y gerencia que necesitan conocer el estado actual de la red de un vistazo.

### 1.1 Acceso al Sistema (Login)
El Login es la puerta de entrada al SGIP-CAP. Está protegido mediante autenticación de tokens de seguridad (JWT).

**Pasos de uso:**
1. Ingrese a la URL principal de la aplicación web en su navegador.
2. En la pantalla de inicio, visualizará el logotipo de SGIP-CAP - SEDALIB.
3. Ingrese su **Usuario** y **Contraseña** en los campos de texto correspondientes.
   - *Nota (MVP):* Las credenciales por defecto son Usuario: `admin`, Contraseña: `admin123`.
4. Haga clic en el botón **"Ingresar"**.
5. Si las credenciales son incorrectas, aparecerá un mensaje de error en rojo. Si son correctas, el sistema lo redirigirá al **Dashboard**.

> **[IMAGEN REQUERIDA AQUÍ: Captura de pantalla completa de la página de Login mostrando los campos de Usuario, Contraseña, el botón de "Ingresar" y la identidad visual de SEDALIB/SGIP-CAP]**

> **[IMAGEN REQUERIDA AQUÍ: Recorte o captura mostrando el mensaje de advertencia/error de credenciales incorrectas en el Login]**

### 1.2 Dashboard Ejecutivo
El Dashboard es el panel principal diseñado para los gerentes operativos. Muestra el estado global de pérdidas e incidentes.

**Funcionalidades principales:**
- **Barra de Alertas Críticas:** En la parte superior. Si hay eventos muy graves sin atender (CRITICAL), aparecerá un aviso color rojo llamativo.
- **Tarjetas de Indicadores (KPIs):** Cuatro paneles que resumen rápidamente la red: DMAs Monitoreados, Incidencias Activas, Tiempo Promedio de Detección y Volumen de Pérdida Estimada (m³).
- **Gráfico Dual (Presión y Caudal):** Un gráfico central que muestra cómo se han comportado la presión (MCA) y el caudal (LPS) en las últimas horas en el sector Moche.
- **Lectura Actual y SLA:** Un panel a la derecha indicando la última lectura recibida y un gráfico circular con el porcentaje de cumplimiento de Acuerdos de Nivel de Servicio (SLA).
- **Listados de Anomalías e Incidentes Recientes:** Tablas resumen ubicadas en la parte inferior para ver los últimos eventos sin salir de la vista principal.

> **[IMAGEN REQUERIDA AQUÍ: Captura panorámica del Dashboard Ejecutivo con la barra de alertas críticas visible (color rojo) en la parte superior]**

> **[IMAGEN REQUERIDA AQUÍ: Recorte enfocado en las 4 tarjetas superiores de KPIs ejecutivos (DMAs, Incidencias, Tiempo, Pérdida)]**

> **[IMAGEN REQUERIDA AQUÍ: Recorte del Gráfico de Tendencia Dual mostrando las líneas de Presión y Caudal con sus respectivos ejes (izquierdo y derecho)]**

### 1.3 Monitoreo en Tiempo Real
Esta vista está pensada para los operadores de sala de control, quienes deben estar observando el flujo en tiempo real (Live).

**Funcionalidades principales:**
- **Conexión en Vivo (WebSocket):** Un indicador que muestra si el sistema está "Conectado" (verde) o "Desconectado" (rojo) al motor de datos. Si se desconecta, se reconecta solo automáticamente en 5 segundos.
- **Medidores Actuales:** Tarjetas que parpadean o se actualizan cada vez que ingresa una nueva lectura de Presión y Caudal.
- **Gráficos de Área Activos:** Gráficos que se mueven y actualizan a medida que llegan los datos en vivo de las últimas 24 horas.
- **Eventos Detectados en Vivo:** Una tabla inferior que se llena dinámicamente si el motor de Machine Learning capta una caída de presión brusca o un pico de caudal en ese instante.

> **[IMAGEN REQUERIDA AQUÍ: Captura de pantalla de la vista de Monitoreo mostrando los medidores de Presión Actual y Caudal Actual, y la tarjeta que certifica la "Conexión WebSocket" en estado verde (Conectado)]**

> **[IMAGEN REQUERIDA AQUÍ: Recorte de los Gráficos de Área (Tendencias en vivo) de Presión y Caudal]**

---

## Parte 2: Gestión Geográfica e Incidentes (Responsable: Marck)

Esta sección abarca el análisis espacial (dónde ocurren las fugas) y la gestión operativa para resolver los problemas mediante la generación de tickets ITIL.

### 2.1 Mapa de DMAs (Distribución Geográfica)
Permite visualizar la distribución de los Distritos de Medición (DMAs) en la ciudad de Trujillo de forma interactiva.

**Pasos y uso:**
1. Navegue a la vista **Mapa de DMAs** en el menú lateral.
2. En la parte superior, verá tarjetas resumen con el estado operativo de cada sector (Moche 01, El Porvenir 01, etc.).
3. El mapa central mostrará marcadores ubicados geográficamente.
   - **Verde:** Funcionamiento Normal.
   - **Amarillo:** Zona en Precaución.
   - **Rojo:** Nivel Crítico (posible rotura/fuga masiva).
4. **Interacción:** Haga clic en cualquier marcador del mapa. Se desplegará una ventana flotante (Popup) con las lecturas actuales de ese DMA específico y un botón que dice "Ver detalle".

> **[IMAGEN REQUERIDA AQUÍ: Captura del Mapa de DMAs centrado en Trujillo, mostrando múltiples marcadores de diferentes colores (verde, amarillo, rojo)]**

> **[IMAGEN REQUERIDA AQUÍ: Recorte del Popup del mapa abierto, tras hacer clic en un marcador, donde se vea el nombre del DMA, presión, caudal y el botón de "Ver detalle"]**

### 2.2 Detalle de DMA
Al ingresar al detalle de una zona de distribución específica, el operador puede hacer un análisis minucioso.

**Funcionalidades principales:**
- **Encabezado:** Muestra el nombre oficial (ej. DMA-MO-01), distrito, y el botón para volver al mapa general.
- **Riesgo y Pérdida del Sector:** Tarjetas específicas del sector con la clasificación de riesgo.
- **Gráficos de Historial Exclusivo:** Evolución histórica del sector.
- **Lista de Sensores:** Tabla con los sensores instalados físicamente (ej. SENS-MO-01-P), si miden presión o flujo, y si están activos o en mantenimiento.
- **Incidentes Aislados:** Tabla que filtra y muestra SOLO los incidentes ocurridos en ese DMA.

> **[IMAGEN REQUERIDA AQUÍ: Captura superior de la vista de Detalle de DMA (ej. DMA-MO-01) mostrando sus KPIs, historial, y el botón de volver]**

> **[IMAGEN REQUERIDA AQUÍ: Recorte de la tabla de "Sensores Instalados" en el DMA]**

### 2.3 Gestión de Incidentes (Ciclo ITIL)
Esta es una de las herramientas más potentes del sistema. Todo evento anómalo se convierte en un ticket de incidente que debe ser gestionado bajo buenas prácticas ITIL.

**Pasos y uso:**
1. En el menú, diríjase a **Incidentes**.
2. **Filtrado:** Use la barra superior para buscar un ticket por su código (ej: `INC-2026...`), o filtre por **Prioridad** (Crítico, Alto, Medio, Bajo) o por **Estado**.
3. En la tabla central, verá el estado de vencimiento del **SLA**. Si un ticket se pone rojo, significa que el equipo demoró más del tiempo establecido para atenderlo.
4. **Acciones ITIL:** Haga clic en un incidente. Se abrirá un **Modal de Detalle**.
5. En la pestaña **"Detalles"**, el operador puede presionar botones de estado para mover el ticket:
   - Pasar de `NUEVO` a `CLASIFICADO`.
   - De `ASIGNADO` a `EN PROGRESO`.
   - Si es muy complejo, `ESCALAR`. Si está resuelto, `RESOLVER`.
6. En la pestaña **"Historial" (Audit Log)**, el sistema registra cada clic, cambio de estado o comentario que hace el equipo, creando una línea de tiempo inalterable.

> **[IMAGEN REQUERIDA AQUÍ: Captura completa de la Tabla de Incidentes, resaltando visualmente las etiquetas de colores (Badges) de Prioridad y Estado, y un registro con SLA vencido en rojo]**

> **[IMAGEN REQUERIDA AQUÍ: Captura del Modal de "Detalle de Incidente" (Pestaña Detalles) abierto, donde se evidencien los botones de acción del flujo ITIL como 'Asignar', 'Resolver', o 'Cerrar']**

> **[IMAGEN REQUERIDA AQUÍ: Recorte de la Pestaña "Historial" (Audit Log) dentro del mismo modal, mostrando la línea de tiempo vertical (Timeline) con las fechas y autores de cada cambio]**

---

## Parte 3: Analítica IA, Reportes y Configuración (Responsable: Mario)

Esta sección engloba la Inteligencia Artificial del sistema y la extracción formal de información, muy útil para auditorías, gerentes de sistemas y jefes de planta.

### 3.1 Analítica IA (Machine Learning)
Vista dedicada a explicar "cómo" y "por qué" el sistema detecta fugas sin necesidad de que un humano fije límites manuales, mediante un modelo de "Isolation Forest".

**Funcionalidades principales:**
- **Tarjetas de Estado del Modelo:** Muestra el algoritmo utilizado, el umbral de detección, y la tasa promedio de detección.
- **Gráfico de Severidad y Detección (7 días):** Visualiza en formato torta (Pie Chart) cuántas anomalías son críticas, altas, etc. Y un gráfico de barras de los últimos 7 días.
- **Matriz de Comportamiento:** Un gráfico de puntos cruzados (Scatter plot) donde los puntos azules son lecturas normales del día a día, y los puntos rojos son los "aislados" por el algoritmo (anomalías).
- **Simulador de Anomalías:** Un botón estratégico para "inyectar" datos artificiales y probar si la alarma del sistema reacciona correctamente.
- **Explicabilidad (Explainability):** Un panel que toma la última anomalía y detalla en porcentaje por qué saltó (ej: 80% causado por caída abrupta de presión, 20% por pico de caudal).

> **[IMAGEN REQUERIDA AQUÍ: Captura de las tarjetas de resumen del Modelo IA (Isolation Forest) y el Gráfico de Severidad (Pie Chart)]**

> **[IMAGEN REQUERIDA AQUÍ: Recorte del Gráfico "Matriz de Comportamiento" (Scatter Plot) con los puntos de dispersión azules y rojos]**

> **[IMAGEN REQUERIDA AQUÍ: Recorte de la sección de "Explicabilidad del Modelo", demostrando los porcentajes de impacto de Presión vs Caudal]**

### 3.2 Centro de Reportes
Permite al área gerencial y técnica generar informes exportables sobre el funcionamiento de la red y el cumplimiento operativo.

**Pasos y uso:**
1. Navegue a la sección **Reportes**.
2. Podrá elegir entre tres pestañas principales: **Diario, Semanal o Personalizado**.
   - **Reporte Diario:** Seleccione un día del calendario. Muestra promedios y evolución hora por hora.
   - **Reporte Semanal:** Resumen de la última semana comparando días.
   - **Reporte Personalizado:** Ingrese Fecha Inicial y Fecha Final (máximo 90 días).
3. Una vez generado, los datos se presentarán visualmente en pantalla.
4. **Exportar Reporte:** Utilice los botones de exportación ubicados en la interfaz para descargar el archivo en el formato que necesite.

**Formatos soportados:**
- **PDF:** Formato formal con plantilla institucional para impresión.
- **Excel (.xlsx):** Datos crudos para que los analistas realicen cruces propios o tablas dinámicas.
- **CSV:** Formato plano de sistemas.

> **[IMAGEN REQUERIDA AQUÍ: Captura general del Centro de Reportes mostrando el formulario de selección de fechas de la pestaña "Personalizado"]**

> **[IMAGEN REQUERIDA AQUÍ: Recorte del reporte generado en pantalla, mostrando el gráfico de evolución y las tarjetas de resumen del período]**

> **[IMAGEN REQUERIDA AQUÍ: Recorte enfocado en los botones de exportación (Botones de PDF, Excel, CSV) o barra de progreso de descarga]**

### 3.3 Configuración del Sistema
Esta es una vista técnica para auditar los parámetros centrales sobre los que corre la plataforma, sin intervenir directamente en el servidor.

**Funcionalidades:**
- Visualizar el proveedor de datos activo (`mock`, `csv`, o `scada`).
- Revisar parámetros del motor ML (ventana de entrenamiento, umbrales).
- Verificar conexiones de la base de datos (PostgreSQL y Redis) y variables de seguridad (tiempo de expiración del JWT).
- *Nota:* Esta vista es de "Solo Lectura", diseñada para asegurar que las variables de entorno están correctamente cargadas.

> **[IMAGEN REQUERIDA AQUÍ: Captura de pantalla de la vista de Configuración mostrando la lista de parámetros técnicos, fuente de datos y configuraciones del motor ML]**
