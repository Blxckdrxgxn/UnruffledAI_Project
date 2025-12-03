import os
import numpy as np
import tensorflow as tf
from django.conf import settings

MODEL_PATH = os.path.join(settings.BASE_DIR, "core", "model_files", "burnout_model.keras")

model = tf.keras.models.load_model(MODEL_PATH)


def predict_burnout(values):
    arr = np.array(values).reshape(1, -1)
    score = float(model.predict(arr)[0][0])
    return max(0, min(score, 100))
