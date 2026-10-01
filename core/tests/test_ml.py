import io

import numpy as np
import pytest
from PIL import Image

from core import ml


def test_every_class_has_a_valid_category():
    from core.models import ClothingItem

    valid = {value for value, _ in ClothingItem.CATEGORY_CHOICES}
    assert set(ml.CATEGORY_BY_CLASS) == set(ml.CLASS_NAMES)
    assert set(ml.CATEGORY_BY_CLASS.values()) <= valid


def test_preprocess_shape_and_range():
    out = ml.preprocess(Image.new("RGB", (300, 120), "white"))
    assert out.shape == (1, 28, 28, 1)
    assert out.dtype == np.float32
    assert 0.0 <= out.min() <= out.max() <= 1.0


def test_preprocess_inverts_so_white_background_becomes_dark():
    out = ml.preprocess(Image.new("RGB", (50, 50), "white"))
    assert out.max() == pytest.approx(0.0)


def test_preprocess_flattens_transparency_onto_white():
    transparent = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
    out = ml.preprocess(transparent)
    assert out.max() == pytest.approx(0.0)  # same as a white background


def test_classify_with_real_model():
    """Runs the shipped model end to end; skipped if TensorFlow isn't installed."""
    pytest.importorskip("tensorflow")
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), "white").save(buf, "PNG")
    buf.seek(0)
    prediction = ml.classify(buf)
    assert prediction.label in ml.CLASS_NAMES
    assert 0.0 <= prediction.confidence <= 1.0
