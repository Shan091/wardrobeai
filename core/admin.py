from django.contrib import admin

from .models import ClothingItem


@admin.register(ClothingItem)
class ClothingItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "confidence", "uploaded_at")
    list_filter = ("category",)
    search_fields = ("name",)
    readonly_fields = ("uploaded_at",)
