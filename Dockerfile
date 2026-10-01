FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    TF_ENABLE_ONEDNN_OPTS=0

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Collect static files at build time. The key below is a throwaway used only for this
# command; the real DJANGO_SECRET_KEY is supplied at runtime.
RUN DJANGO_SECRET_KEY=build-only DJANGO_ALLOWED_HOSTS=build python manage.py collectstatic --noinput

# Run as an unprivileged user; /data holds the SQLite database and uploaded images.
RUN useradd --system --uid 1000 --no-create-home app \
    && mkdir -p /data/media \
    && chown -R app:app /data \
    && chmod +x docker-entrypoint.sh
ENV DATABASE_URL=sqlite:////data/db.sqlite3 \
    MEDIA_ROOT=/data/media
VOLUME /data
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz/', timeout=4)" || exit 1

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wardrobe_project.wsgi"]
