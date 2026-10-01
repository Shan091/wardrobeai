import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from core import ml
from core.models import ClothingItem

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def isolated_media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def fake_classifier(monkeypatch):
    """Avoid loading TensorFlow in view tests."""
    prediction = ml.Prediction(label="Sneaker", category="shoes", confidence=0.93)
    monkeypatch.setattr(ml, "classify", lambda fileobj: prediction)
    return prediction


def make_upload(name="shoe.png", fmt="PNG", size=(40, 40)):
    buf = io.BytesIO()
    Image.new("RGB", size, "white").save(buf, fmt)
    return SimpleUploadedFile(name, buf.getvalue(), content_type=f"image/{fmt.lower()}")


def test_home_get(client):
    response = client.get(reverse("home"))
    assert response.status_code == 200
    assert b"Wardrobe AI" in response.content


def test_upload_saves_item_and_redirects_to_result(client, fake_classifier):
    response = client.post(reverse("home"), {"image": make_upload()})
    item = ClothingItem.objects.get()
    assert response.status_code == 302
    assert response["Location"].endswith(f"?scan={item.pk}")
    assert (item.name, item.category) == ("Sneaker", "shoes")
    assert item.confidence == pytest.approx(0.93)
    assert item.image.name.startswith("wardrobe_images/")
    assert "shoe" not in item.image.name  # random name, not the user's


def test_result_page_shows_prediction(client, fake_classifier):
    response = client.post(reverse("home"), {"image": make_upload()}, follow=True)
    assert response.status_code == 200
    assert b"Sneaker" in response.content
    assert b"93% confident" in response.content


def test_low_confidence_is_labelled_best_guess(client, monkeypatch):
    low = ml.Prediction(label="Shirt", category="top", confidence=0.2)
    monkeypatch.setattr(ml, "classify", lambda fileobj: low)
    response = client.post(reverse("home"), {"image": make_upload()}, follow=True)
    assert b"Best guess" in response.content


def test_non_image_rejected(client, fake_classifier):
    bad = SimpleUploadedFile("notes.txt", b"hello", content_type="text/plain")
    response = client.post(reverse("home"), {"image": bad})
    assert response.status_code == 400
    assert ClothingItem.objects.count() == 0


def test_unsupported_format_rejected(client, fake_classifier):
    response = client.post(reverse("home"), {"image": make_upload("a.gif", "GIF")})
    assert response.status_code == 400
    assert b"JPEG, PNG or WebP" in response.content
    assert ClothingItem.objects.count() == 0


def test_oversized_upload_rejected(client, fake_classifier, settings):
    settings.MAX_UPLOAD_MB = 0
    response = client.post(reverse("home"), {"image": make_upload()})
    assert response.status_code == 400
    assert b"too large" in response.content
    assert ClothingItem.objects.count() == 0


def test_classifier_failure_leaves_no_orphans(client, monkeypatch, tmp_path):
    def boom(fileobj):
        raise RuntimeError("model exploded")

    monkeypatch.setattr(ml, "classify", boom)
    response = client.post(reverse("home"), {"image": make_upload()})
    assert response.status_code == 400
    assert b"couldn" in response.content
    assert ClothingItem.objects.count() == 0
    assert not list(tmp_path.rglob("*.png"))


def test_scan_param_is_validated(client):
    assert client.get(reverse("home") + "?scan=abc").status_code == 200
    assert client.get(reverse("home") + "?scan=99999").status_code == 200


def test_media_served_only_for_known_items(client, fake_classifier):
    client.post(reverse("home"), {"image": make_upload()})
    item = ClothingItem.objects.get()
    ok = client.get(item.image.url)
    assert ok.status_code == 200
    assert b"".join(ok.streaming_content)[:4] == b"\x89PNG"
    assert client.get("/media/wardrobe_images/unknown.png").status_code == 404
    assert client.get("/media/../../etc/passwd").status_code == 404


def test_deleting_item_removes_file(client, fake_classifier, tmp_path):
    client.post(reverse("home"), {"image": make_upload()})
    item = ClothingItem.objects.get()
    assert len(list(tmp_path.rglob("*.png"))) == 1
    item.delete()
    assert not list(tmp_path.rglob("*.png"))


def test_healthz(client):
    response = client.get(reverse("healthz"))
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_post_without_csrf_rejected():
    from django.test import Client

    strict = Client(enforce_csrf_checks=True)
    assert strict.post(reverse("home"), {}).status_code == 403
