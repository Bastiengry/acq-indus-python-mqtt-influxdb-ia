FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système nécessaires pour scikit-learn
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY src/ ./src/

# Lancement
CMD ["python", "src/main.py"]