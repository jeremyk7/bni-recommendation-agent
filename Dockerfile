FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# We doen GEEN apt-get update meer om tijd te besparen. 
# De meeste moderne python wheels hebben geen build-essential nodig.
# Indien er een 'missing library' error komt bij het booten, voegen we die gericht toe.

# Pip upgraden (verplicht voor moderne wheels)
RUN python -m pip install --no-cache-dir --upgrade pip

# Eerst requirements kopiëren voor optimale caching
COPY requirements.txt ./

# Pip installeren met de 'Total Lock' lijst (stopt alle backtracking)
RUN pip install --no-cache-dir -r requirements.txt

# Applicatie kopiëren
COPY . .

# Startcommando
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "2", "--timeout", "600", "--bind", ":8080", "app:app"]