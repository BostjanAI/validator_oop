# MES Excel Validator – spletni strežnik (FastAPI + vendoran React frontend).
# Gradnja s kontekstom = koren repozitorija (mapa validator_oop):
#   docker build -f web/deploy/Dockerfile -t mes-validator-web .
# Slika je samostojna in deluje brez interneta (vse JS knjižnice so vendorane).

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MES_WEB_WORKDIR=/data \
    MES_WEB_SERVE_FRONTEND=1

WORKDIR /app

COPY web/deploy/requirements-docker.txt /tmp/requirements-docker.txt
RUN pip install --no-cache-dir -r /tmp/requirements-docker.txt

# Paket validator_oop se kopira pod /app/validator_oop, da je "import validator_oop" mogoč.
COPY . /app/validator_oop

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /data
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health').status==200 else 1)"

CMD ["uvicorn", "validator_oop.web.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
