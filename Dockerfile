FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FIESC_RUNTIME_DIR=/tmp/fiesc-runtime \
    ENABLE_OLLAMA_FALLBACK=false

WORKDIR /app

RUN groupadd --system fiesc \
    && useradd --system --gid fiesc --home-dir /nonexistent --shell /usr/sbin/nologin fiesc \
    && mkdir -p /tmp/fiesc-runtime \
    && chown fiesc:fiesc /tmp/fiesc-runtime

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml README.md ./
COPY src ./src
COPY app ./app
COPY artifacts ./artifacts
COPY data/demo ./data/demo
RUN pip install --no-cache-dir --no-deps .

USER fiesc

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health')"

CMD ["streamlit", "run", "app/streamlit_app.py", "--server.address=0.0.0.0"]
