"""Image classification for the wardrobe scanner.

The model is a small CNN trained on Fashion-MNIST, so it only knows the ten
classes below. It is loaded lazily (first prediction or worker start-up) and
shared by all threads in a process.
"""

import logging
import threading
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from django.conf import settings
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

CLASS_NAMES = [
    "T-shirt/top",
    "Trouser",
    "Pullover",
    "Dress",
    "Coat",
    "Sandal",
    "Shirt",
    "Sneaker",
    "Bag",
    "Ankle boot",
]

# Maps each model class onto ClothingItem.CATEGORY_CHOICES.
CATEGORY_BY_CLASS = {
    "T-shirt/top": "top",
    "Pullover": "top",
    "Shirt": "top",
    "Coat": "top",
    "Trouser": "bottom",
    "Dress": "dress",
    "Sandal": "shoes",
    "Sneaker": "shoes",
    "Ankle boot": "shoes",
    "Bag": "accessory",
}

_predict_lock = threading.Lock()


@dataclass(frozen=True)
class Prediction:
    label: str
    category: str
    confidence: float


@lru_cache(maxsize=1)
def get_model():
    """Load the Keras model once per process."""
    # Imported here so that management commands (migrate, collectstatic, ...)
    # do not pay the TensorFlow import cost.
    from tensorflow.keras.models import load_model  # type: ignore

    logger.info("Loading model from %s", settings.MODEL_PATH)
    return load_model(settings.MODEL_PATH, compile=False)


def preprocess(img: Image.Image) -> np.ndarray:
    """Turn an arbitrary photo into the (1, 28, 28, 1) float array the model expects.

    Fashion-MNIST items are light on a dark background, so the photo is
    converted to greyscale and inverted (a dark garment on white becomes light on dark).
    """
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        # Flatten transparency onto white; otherwise transparent pixels read as black.
        rgba = img.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        img = Image.alpha_composite(background, rgba)
    img = img.convert("L")
    img = img.resize((28, 28), Image.Resampling.LANCZOS)
    img = ImageOps.invert(img)
    return (np.asarray(img, dtype="float32") / 255.0).reshape(1, 28, 28, 1)


def classify(fileobj) -> Prediction:
    """Classify an open image file (path or file-like object)."""
    with Image.open(fileobj) as img:
        batch = preprocess(img)
    model = get_model()
    with _predict_lock:
        probabilities = model.predict(batch, verbose=0)[0]
    index = int(np.argmax(probabilities))
    label = CLASS_NAMES[index]
    return Prediction(
        label=label,
        category=CATEGORY_BY_CLASS[label],
        confidence=float(probabilities[index]),
    )
