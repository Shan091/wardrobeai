from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import ClothingItem


@receiver(post_delete, sender=ClothingItem)
def delete_image_file(sender, instance, **kwargs):
    """Remove the file from storage when its database row is deleted."""
    if instance.image:
        instance.image.delete(save=False)
