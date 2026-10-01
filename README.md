# Wardrobe AI

[![CI](https://github.com/Shan091/wardrobeai/actions/workflows/ci.yml/badge.svg)](https://github.com/Shan091/wardrobeai/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Django](https://img.shields.io/badge/django-5.2-092E20)
![License](https://img.shields.io/badge/license-MIT-green)

Upload a photo of a clothing item and Wardrobe AI identifies it, files it into a category
(top, bottom, dress, footwear, accessory) and saves it to your wardrobe. A small convolutional
neural network does the classification; Django handles uploads, storage and the web UI.

<!-- Add a screenshot or short GIF here: ![Wardrobe AI](docs/screenshot.png) -->

## How it works

1. You upload a JPEG, PNG or WebP photo (validated for real file type and size).
2. The image is converted to 28×28 greyscale and inverted, which is the format the model was trained on.
3. A Keras CNN (3 convolution blocks with batch norm and dropout) predicts one of ten classes:
   T-shirt/top, Trouser, Pullover, Dress, Coat, Sandal, Shirt, Sneaker, Bag, Ankle boot.
4. The result is mapped to a wardrobe category and stored with its confidence score.
   Predictions below 50% confidence are shown as a "best guess".

## Limitations

- The model is trained on [Fashion-MNIST](https://github.com/zalandoresearch/fashion-mnist): tiny
  greyscale studio images of a single item. It works best on a single garment photographed against a
  plain, light background. Busy photos, people wearing the clothes, or items outside the ten classes
  will be misclassified.
- There is no user login. Anyone who can reach the app can upload and see scans, so don't expose it
  publicly with personal photos. Put it behind authentication (for example your reverse proxy) and
  add rate limiting if you deploy it on the open internet.

## Quick start (development)

Requires Python 3.11 or newer.

```bash
git clone https://github.com/Shan091/wardrobeai.git
cd wardrobeai
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

cp .env.example .env
# edit .env and set DJANGO_DEBUG=true

python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
python manage.py runserver
```

Open <http://127.0.0.1:8000>. The first scan is slower while TensorFlow loads the model.

## Production deployment

### Docker

```bash
cp .env.example .env
# set DJANGO_SECRET_KEY, DJANGO_ALLOWED_HOSTS and DJANGO_CSRF_TRUSTED_ORIGINS
docker compose up -d --build
```

The container runs migrations on start, serves the app with gunicorn on port 8000, runs as a
non-root user, and keeps the database and uploads in the `wardrobe_data` volume. Put a TLS-terminating
reverse proxy (nginx, Caddy, a cloud load balancer) in front of it and set
`DJANGO_TRUST_PROXY_HEADERS=true` so Django knows requests arrived over HTTPS.

To try the production setup on plain HTTP locally, set `DJANGO_SECURE_SSL=false` in `.env`.

### Without Docker

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn -c gunicorn.conf.py wardrobe_project.wsgi
```

### Configuration

All settings are environment variables; see [`.env.example`](.env.example) for the full list.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | none (required) | Signing key. The app refuses to start without it when `DJANGO_DEBUG` is off. |
| `DJANGO_ALLOWED_HOSTS` | none (required) | Comma-separated hostnames. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | empty | Full origins such as `https://wardrobe.example.com`. |
| `DJANGO_DEBUG` | `false` | Development mode. Never enable in production. |
| `DJANGO_SECURE_SSL` | on when not debugging | HTTPS redirect, secure cookies and HSTS. |
| `DATABASE_URL` | SQLite file | Any URL supported by `dj-database-url`, such as PostgreSQL. |
| `MEDIA_ROOT` | `./media` | Where uploads are stored. |
| `MAX_UPLOAD_MB` | `5` | Upload size limit. |
| `WEB_CONCURRENCY` | `1` | Gunicorn workers. Each loads its own copy of the model, so scale threads first. |

A health check is available at `/healthz/` and returns `{"status": "ok"}` when the database is reachable.

## Development

```bash
pytest                # tests, including one that runs the real model
ruff check . && ruff format --check .
```

CI runs linting, Django checks, a migrations check and the test suite on Python 3.11 and 3.12,
then builds the Docker image.

## Project structure

```
core/
  ml.py            model loading, preprocessing and prediction
  forms.py         upload validation
  views.py         home page, media serving, health check
  models.py        ClothingItem
  wardrobe_model.keras   trained model
  tests/
wardrobe_project/  Django settings and URLs
gunicorn.conf.py   production server config
Dockerfile, docker-compose.yml
```

## Retraining the model

The model file is a Keras 3 `.keras` archive taking a `(28, 28, 1)` float input in `[0, 1]` and
returning 10 softmax probabilities in the class order listed in `core/ml.py`. Any replacement with
that interface can be dropped in at `core/wardrobe_model.keras`, or pointed to with `MODEL_PATH`.

## License

[MIT](LICENSE)
