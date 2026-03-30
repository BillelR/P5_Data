# ── Image de base légère Python 3.11 ──────────────────────────────────────────
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="DataSoluTech – Stagiaire Data Engineer"
LABEL description="Service de migration du dataset médical vers MongoDB"

# Répertoire de travail dans le conteneur
WORKDIR /app

# Copie des dépendances en premier (cache Docker)
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY scripts/ ./scripts/

# Commande par défaut
CMD ["python", "scripts/migrate.py", "--csv", "/app/healthcare_dataset.csv"]
