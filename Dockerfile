FROM python:3.9.10-slim

# 1. Creiamo un nuovo utente di sistema chiamato 'capitaluser' (senza password)
RUN useradd -m capitaluser

# 2. Copiamo i file assegnandone SUBITO la proprietà a 'capitaluser'
COPY --chown=capitaluser:capitaluser app /capital/app
COPY --chown=capitaluser:capitaluser requirements.txt /capital
COPY --chown=capitaluser:capitaluser alembic.ini /capital
COPY --chown=capitaluser:capitaluser main.py /capital

WORKDIR /capital

# 3. Restiamo temporaneamente come 'root' per fare le installazioni di sistema
RUN apt update -y && apt install -y procps
RUN pip install -r requirements.txt

# 4. IL TOCCO MAGICO: Abbassiamo i privilegi appena prima di far partire l'app
USER capitaluser

# 5. Avvio in sicurezza
CMD ["python3", "main.py"]