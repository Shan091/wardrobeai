import logging

from django.conf import settings
from django.db import connection
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from . import ml
from .forms import UploadForm
from .models import ClothingItem

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def home(request):
    context = {"form": UploadForm(), "error": None}

    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.cleaned_data["image"]
            try:
                # Classify before saving so a failure leaves no orphaned row or file.
                prediction = ml.classify(upload)
            except Exception:
                logger.exception("Image classification failed")
                context["error"] = "Sorry, we couldn't analyse that image. Please try another one."
            else:
                upload.seek(0)
                item = ClothingItem.objects.create(
                    image=upload,
                    name=prediction.label,
                    category=prediction.category,
                    confidence=prediction.confidence,
                )
                # Post/Redirect/Get: refreshing the page must not re-upload the file.
                return redirect(f"{request.path}?scan={item.pk}")
        else:
            context["error"] = " ".join(form.errors["image"])
    else:
        scan_id = request.GET.get("scan", "")
        if scan_id.isdigit():
            item = ClothingItem.objects.filter(pk=int(scan_id)).first()
            if item:
                context["item"] = item
                context["uncertain"] = (item.confidence or 0) < settings.CONFIDENCE_THRESHOLD

    return render(request, "home.html", context, status=400 if context["error"] else 200)


@require_GET
def media_file(request, path):
    """Serve an uploaded image, but only if it belongs to a ClothingItem.

    Django does not serve MEDIA_ROOT outside development. Looking the path up in the
    database (rather than joining it onto MEDIA_ROOT) rules out path traversal.
    For high traffic, serve MEDIA_ROOT directly from nginx / object storage instead.
    """
    item = ClothingItem.objects.filter(image=path).first()
    if item is None:
        raise Http404
    try:
        response = FileResponse(item.image.open("rb"))
    except FileNotFoundError:
        raise Http404 from None
    # File names are random UUIDs and never change, so they can be cached aggressively.
    response["Cache-Control"] = "public, max-age=86400, immutable"
    return response


@require_GET
def healthz(request):
    """Liveness/readiness probe: verifies the database is reachable."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        logger.exception("Health check failed")
        return JsonResponse({"status": "error"}, status=503)
    return JsonResponse({"status": "ok"})
