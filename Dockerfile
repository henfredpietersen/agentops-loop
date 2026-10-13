FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080 AGENTOPS_CACHE=/app/.cache
COPY requirements.txt requirements-models.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements-models.txt
COPY . .
RUN useradd --create-home --uid 10001 app && mkdir -p /app/.cache && chown -R app:app /app
USER app
# Pull MiniLM + cross-encoder at build time so the container never fetches models at request time.
RUN AGENTOPS_REQUIRE_MODELS=1 python -c "from app.config import load_config; from app.corpus import load_corpus; from app.retrieve import KnowledgeBase; c=load_config(); KnowledgeBase(c, load_corpus())"
EXPOSE 8080
CMD ["sh", "-c", "uvicorn app.api:app --host 0.0.0.0 --port ${PORT}"]
