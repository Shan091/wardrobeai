import uuid
from pathlib import Path

from django.db import models


def upload_path(instance, filename):
    """Store uploads under a random name so user-supplied names never hit the disk."""
    ext = Path(filename).suffix.lower() or ".jpg"
    return f"wardrobe_images/{uuid.uuid4().hex}{ext}"


class ClothingItem(models.Model):
    CATEGORY_CHOICES = [
        ("top", "Topwear"),
        ("bottom", "Bottomwear"),
        ("dress", "Dress"),
        ("shoes", "Footwear"),
        ("accessory", "Accessory"),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    color = models.CharField(max_length=50, blank=True)
    image = models.ImageField(upload_to=upload_path)
    confidence = models.FloatField(
        null=True, blank=True, help_text="Model confidence for the predicted class (0-1)."
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.name
