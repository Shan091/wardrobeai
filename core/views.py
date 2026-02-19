import os
import numpy as np
from django.shortcuts import render, redirect
from django.conf import settings
from tensorflow.keras.models import load_model # type: ignore
from tensorflow.keras.preprocessing import image # type: ignore
from PIL import Image, ImageOps

# Import your database model
from .models import ClothingItem

# Load model once when server starts
MODEL_PATH = os.path.join(settings.BASE_DIR, 'core/wardrobe_model.keras')
model = load_model(MODEL_PATH)

class_names = ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat', 
               'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']

def home(request):
    context = {}
    
    # Grab all items from the database to display them
    items = ClothingItem.objects.all().order_by('-uploaded_at')
    context['items'] = items

    if request.method == 'POST' and request.FILES.get('image'):
        
        new_item = ClothingItem.objects.create(
            image=request.FILES['image'],
            name="Processing...", # Temporary name
            category="Uncategorized"
        )

        
        file_path = new_item.image.path

        try:
            img = Image.open(file_path)
            img = img.convert('L') # Gray
            img = img.resize((28, 28), Image.Resampling.LANCZOS) # Resize
            img = ImageOps.invert(img) # Invert colors
            
            # --- STEP 3: Predict ---
            img_array = np.array(img) / 255.0
            img_array = img_array.reshape(1, 28, 28, 1)
            
            prediction = model.predict(img_array)
            predicted_class = class_names[np.argmax(prediction)]
            
            # --- STEP 4: Update Database with AI Result ---
            new_item.name = predicted_class.title()  # Auto-name the item
            new_item.category = "top" if predicted_class in ['T-shirt/top', 'Pullover', 'Shirt', 'Coat'] else "bottom" # Simple auto-categorization
            new_item.save()  
            
            # Add result to context for the popup/display
            context['result'] = predicted_class.title()
            context['file_url'] = new_item.image.url
            
        except Exception as e:
            print(f"Error processing image: {e}")
            # Optional: Delete the item if AI fails, or keep it as 'Unknown'

    return render(request, 'home.html', context)
