# SGIP-CAP
**Sistema de Gestión Integral de Pérdidas - Control y Análisis de Presión**

## 📋 Descripción del Proyecto
SGIP-CAP es una aplicación web empresarial diseñada para la detección temprana y gestión de fugas de agua potable mediante el análisis inteligente de variables hidráulicas (presión y caudal).

**Objetivo Principal**: Reducir el Agua No Facturada (ANF) en SEDALIB mediante la detección temprana de fugas y la gestión eficiente de incidencias basándose en las mejores prácticas de ITIL 4.

**Alcance del MVP**: Sector Moche (DMA-MO-01).

---

## 🏗️ Stack Tecnológico
- **Backend**: FastAPI, Python 3.11
- **Base de Datos**: PostgreSQL 15 con SQLAlchemy ORM
- **ML / Analítica**: Isolation Forest (scikit-learn)
- **Caché y Tareas Asíncronas**: Redis y Celery
- **Comunicación en Tiempo Real**: WebSockets
- **Despliegue**: Docker Compose

## 🚀 Inicio Rápido
El proyecto está dockerizado para facilitar el despliegue.

Para levantar el entorno completo (Base de datos, Redis, Backend), ejecuta:
```bash
docker-compose up -d --build
```
Una vez levantado, la API estará disponible en `http://localhost:8000/api/docs`.