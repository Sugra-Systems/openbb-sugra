FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py widgets.json apps.json ./

EXPOSE 8000

# SUGRA_API_KEY is injected at runtime (-e SUGRA_API_KEY=...), never baked in.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
