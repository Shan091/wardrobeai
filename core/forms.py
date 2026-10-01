from django import forms
from django.conf import settings
from PIL import Image

# Refuse decompression bombs: Pillow raises DecompressionBombError above 2x this value.
Image.MAX_IMAGE_PIXELS = 40_000_000

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


class UploadForm(forms.Form):
    image = forms.ImageField()

    def clean_image(self):
        upload = self.cleaned_data["image"]
        max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
        if upload.size > max_bytes:
            raise forms.ValidationError(f"Image is too large (max {settings.MAX_UPLOAD_MB} MB).")
        # ImageField has already opened the file with Pillow and recorded its real format.
        image_format = getattr(getattr(upload, "image", None), "format", None)
        if image_format not in ALLOWED_FORMATS:
            raise forms.ValidationError("Please upload a JPEG, PNG or WebP image.")
        upload.seek(0)
        return upload
