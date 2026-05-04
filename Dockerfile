FROM python:3.9.10-slim

# 1. Creiamo l'utente
RUN useradd -m capitaluser
WORKDIR /capital

# 2. OTTIMIZZAZIONE DELLA CACHE: Copiamo PRIMA solo i requirements!
# In questo modo, se cambi il codice di 'app', Docker userà la cache per le librerie 
# e salterà il noiosissimo 'pip install'.
COPY --chown=capitaluser:capitaluser requirements.txt /capital/

# 3. PULIZIA DELLA SPAZZATURA: Installiamo e puliamo la cache nella stessa riga
RUN apt update -y && apt install -y procps && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

# 4. Ora copiamo il resto del codice, che cambia spesso
COPY --chown=capitaluser:capitaluser app /capital/app
COPY --chown=capitaluser:capitaluser alembic.ini /capital/
COPY --chown=capitaluser:capitaluser main.py /capital/

# 5. Abbassiamo i privilegi
USER capitaluser

# 6. Avvio in sicurezza
CMD ["python3", "main.py"]