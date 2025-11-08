FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd -m appuser \
    && mkdir -p /app/.streamlit \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app

COPY . .

EXPOSE 8501

USER appuser

ENV PYTHONPATH=/app/src
ENV APP_DATA_DIR=/app

ENTRYPOINT ["streamlit", "run", "streamlit_app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
