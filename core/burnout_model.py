import os
import pickle
import numpy as np
import tensorflow as tf
from django.conf import settings

# Path to the model_files directory
MODEL_DIR = os.path.join(settings.BASE_DIR, "core", "model_files")

# Path to burnout model file
MODEL_PATH = os.path.join(MODEL_DIR, "burnout_model.keras")

# Load TensorFlow model
burnout_model = tf.keras.models.load_model(MODEL_PATH)

# Load scalers/encoders
with open(os.path.join(MODEL_DIR, "burnout_scaler.pkl"), "rb") as f:
    scaler = pickle.load(f)

with open(os.path.join(MODEL_DIR, "burnout_class_encoder.pkl"), "rb") as f:
    class_encoder = pickle.load(f)

with open(os.path.join(MODEL_DIR, "burnout_planet_encoder.pkl"), "rb") as f:
    planet_encoder = pickle.load(f)

with open(os.path.join(MODEL_DIR, "burnout_house_encoder.pkl"), "rb") as f:
    house_encoder = pickle.load(f)

with open(os.path.join(MODEL_DIR, "burnout_sleep_encoder.pkl"), "rb") as f:
    sleep_encoder = pickle.load(f)


def predict_burnout(heart_rate, hrv_score, sleep_hours,
                    activity_level, stress_level,
                    transit_planet, natal_house, sleep_quality):
    """
    Returns burnout category (low/medium/high) AND numeric risk (0-1).
    """
    # Encode categorical values
    planet_val = planet_encoder.transform([transit_planet])[0]
    house_val = house_encoder.transform([natal_house])[0]
    sleep_val = sleep_encoder.transform([sleep_quality])[0]

    # Build feature array
    features = np.array([[
        heart_rate,
        hrv_score,
        sleep_hours,
        activity_level,
        stress_level,
        planet_val,
        house_val,
        sleep_val
    ]])

    # Scale numerical inputs
    features_scaled = scaler.transform(features)

    # Run the model
    class_pred, score_pred = burnout_model.predict(features_scaled)

    # Convert class prediction to label
    class_idx = np.argmax(class_pred, axis=1)[0]
    burnout_category = class_encoder.inverse_transform([class_idx])[0]

    # Extract numeric burnout score (0–1)
    burnout_score = float(score_pred[0][0])

    return burnout_category, burnout_score
