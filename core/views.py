import os
import numpy as np
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from tensorflow.keras.models import load_model # type: ignore
from tensorflow.keras.preprocessing import image # type: ignore
from PIL import Image, ImageOps

# Load model once when server starts
MODEL_PATH = os.path.join(settings.BASE_DIR, 'core/wardrobe_model.keras')
model = load_model(MODEL_PATH)

class_names = ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat', 
               'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']

def home(request):
    context = {}
    if request.method == 'POST' and request.FILES['image']:
        # 1. Save Image
        upload = request.FILES['image']
        fs = FileSystemStorage()
        filename = fs.save(upload.name, upload)
        file_url = fs.url(filename)
        file_path = fs.path(filename)

        # 2. Process Image for AI
        img = Image.open(file_path)
        img = img.convert('L') # Gray
        img = img.resize((28, 28), Image.Resampling.LANCZOS) # Resize
        img = ImageOps.invert(img) # Invert colors
        
        # 3. Predict
        img_array = np.array(img) / 255.0
        img_array = img_array.reshape(1, 28, 28, 1)
        
        prediction = model.predict(img_array)
        result = class_names[np.argmax(prediction)]
        confidence = round(np.max(prediction) * 100, 2)
        predicted_class = class_names[np.argmax(prediction)]

        context['result'] = predicted_class.title() 
        context['file_url'] = file_url

    return render(request, 'home.html', context)