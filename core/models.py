from django.db import models

class ClothingItem(models.Model):
    # Categories for filtering later
    CATEGORY_CHOICES = [
        ('top', 'Topwear'),
        ('bottom', 'Bottomwear'),
        ('shoes', 'Footwear'),
        ('accessory', 'Accessory'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    color = models.CharField(max_length=50, blank=True)
    
    # This saves the image to 'media/wardrobe_images/' and the path to the DB
    image = models.ImageField(upload_to='wardrobe_images/')
    
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name