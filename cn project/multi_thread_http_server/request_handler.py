import tensorflow as tf
import numpy as np
from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
import io

# ----------------------------
# Load Model (Singleton Pattern)
# ----------------------------
_model = None

def load_model():
    """
    Loads the pre-trained ResNet50 model only once.
    This avoids reloading for every request/thread.
    """
    global _model
    if _model is None:
        _model = tf.keras.applications.ResNet50(weights='imagenet')
    return _model

# ----------------------------
# Preprocess Image
# ----------------------------
def preprocess_image(file_bytes):
    """
    Preprocess the uploaded image file (bytes) for model inference.
    Args:
        file_bytes: raw bytes of the image file
    Returns:
        preprocessed numpy array suitable for model input
    """
    try:
        img = image.load_img(io.BytesIO(file_bytes), target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        return img_array
    except Exception as e:
        raise ValueError(f"Error processing image: {e}")

# ----------------------------
# Decode Model Predictions
# ----------------------------
def decode_predictions_result(preds):
    """
    Decodes model predictions into human-readable labels.
    Args:
        preds: raw model predictions
    Returns:
        dictionary containing top-3 predictions and confidence
    """
    decoded = decode_predictions(preds, top=3)[0]
    results = [
        {"label": label, "description": desc, "confidence": float(conf)}
        for (_, label, desc, conf) in decoded
    ]
    return results
