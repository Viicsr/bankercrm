# Stage 1: builder — instala dependencias
FROM python:3.12-slim AS builder

WORKDIR /app

# Copia solo requirements primero (aprovecha cache de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: runtime — imagen final sin herramientas de build
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copia las dependencias instaladas del stage anterior
COPY --from=builder /root/.local /root/.local

# Copia el código
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Asegura que los scripts de .local están en PATH
ENV PATH=/root/.local/bin:$PATH

# Puerto expuesto (documentativo, no abre el puerto por sí solo)
EXPOSE 8000

# Health check para Docker y Railway
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

COPY scripts/entrypoint.sh ./scripts/entrypoint.sh
RUN chmod +x ./scripts/entrypoint.sh
  
CMD ["./scripts/entrypoint.sh"]