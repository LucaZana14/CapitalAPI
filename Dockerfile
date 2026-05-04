FROM python:3.9.10-slim

# 1. AGGIORNAMENTO DI SISTEMA E PACCHETTI (Risolve i 17 errori Trivy di Linux)
# Facciamo l'update, l'upgrade, installiamo procps e puliamo la spazzatura in un solo colpo!
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y procps && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 2. CREAZIONE UTENTE
RUN useradd -m capitaluser
WORKDIR /capital

# 3. AGGIORNAMENTO CORE PYTHON (Risolve gli errori Trivy su wheel e setuptools)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 4. OTTIMIZZAZIONE DELLA CACHE (Dipendenze del tuo progetto)
COPY --chown=capitaluser:capitaluser requirements.txt /capital/
RUN pip install --no-cache-dir -r requirements.txt

# 5. COPIA DEL CODICE SORGENTE
COPY --chown=capitaluser:capitaluser app /capital/app
COPY --chown=capitaluser:capitaluser alembic.ini /capital/
COPY --chown=capitaluser:capitaluser main.py /capital/

# 6. BLINDATURA (Abbassiamo i privilegi)
USER capitaluser

# 7. AVVIO
CMD ["python3", "main.py"]

# Usa Python per fare una richiesta alla rotta principale dell'API
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1