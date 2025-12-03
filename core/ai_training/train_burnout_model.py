import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
import pickle
import os


print("Generating synthetic burnout dataset...")

# simulate 5000 samples
N = 5000

heart_rate = np.random.randint(55, 120, N)
hrv_score = np.random.uniform(10, 80, N)
sleep_hours = np.random.uniform(2, 10, N)
activity_level = np.random.randint(0, 10, N)
stress_level = np.random.randint(1, 10, N)
sleep_quality = np.random.choice(["Poor", "Fair", "Good", "Excellent"], N)

# astrology features
transit_planet = np.random.choice(["Mars", "Saturn", "Moon", "Mercury", "Venus"], N)
natal_house = np.random.choice(["1st","4th","6th","8th","12th"], N)

# burnout target score (0 to 1)
burnout_score = (
    (stress_level/10) * 0.5 +
    (heart_rate-55)/65 * 0.15 +
    (10 - sleep_hours)/10 * 0.2 +
    (1 - hrv_score/80) * 0.1 +
    np.random.uniform(0, 0.1, N)
)

burnout_score = np.clip(burnout_score, 0, 1)

# burnout category
def classify(score):
    if score < 0.33:
        return "low"
    elif score < 0.66:
        return "medium"
    return "high"

burnout_label = [classify(s) for s in burnout_score]

df = pd.DataFrame({
    "heart_rate": heart_rate,
    "hrv_score": hrv_score,
    "sleep_hours": sleep_hours,
    "activity_level": activity_level,
    "stress_level": stress_level,
    "sleep_quality": sleep_quality,
    "transit_planet": transit_planet,
    "natal_house": natal_house,
    "burnout_score": burnout_score,
    "burnout_label": burnout_label
})

print("Encoding features...")

# Encode categoricals
planet_enc = LabelEncoder()
house_enc = LabelEncoder()
sleep_enc = LabelEncoder()

df["planet_enc"] = planet_enc.fit_transform(df["transit_planet"])
df["house_enc"] = house_enc.fit_transform(df["natal_house"])
df["sleep_enc"] = sleep_enc.fit_transform(df["sleep_quality"])

# input features
X = df[[
    "heart_rate","hrv_score","sleep_hours",
    "activity_level","stress_level",
    "planet_enc","house_enc","sleep_enc"
]].values

y_score = df["burnout_score"].values  # numeric output
y_class = df["burnout_label"].values  # categorical output

# scale X
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

# encode burnout category
class_enc = LabelEncoder()
y_class_enc = class_enc.fit_transform(y_class)

X_train, X_test, class_train, class_test, score_train, score_test = train_test_split(
    X_scaled, y_class_enc, burnout_score, 
    test_size=0.2, random_state=42
)


print("Building burnout model neural network...")

# Multi-output model (classification + score)
input_layer = tf.keras.layers.Input(shape=(8,))
dense1 = tf.keras.layers.Dense(64, activation="relu")(input_layer)
dense2 = tf.keras.layers.Dense(32, activation="relu")(dense1)

# classification output
class_output = tf.keras.layers.Dense(
    len(class_enc.classes_), activation="softmax", name="class_output"
)(dense2)

# numeric burnout score output
score_output = tf.keras.layers.Dense(
    1, activation="sigmoid", name="score_output"
)(dense2)

model = tf.keras.Model(inputs=input_layer, outputs=[class_output, score_output])

model.compile(
    optimizer="adam",
    loss={
        "class_output": "sparse_categorical_crossentropy",
        "score_output": "mse"
    },
    metrics={
        "class_output": "accuracy",
        "score_output": "mse"
    }
)

print("Training model...")
model.fit(
    X_train,
    {
        "class_output": class_train,
        "score_output": score_train
    },
    validation_data=(
        X_test,
        {
            "class_output": class_test,
            "score_output": score_test
        }
    ),
    epochs=12,
    batch_size=32
)

print("Saving model...")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "model_files")
os.makedirs(MODEL_DIR, exist_ok=True)

model.save(os.path.join(MODEL_DIR, "burnout_model.keras"))

with open(os.path.join(MODEL_DIR, "burnout_scaler.pkl"), "wb") as f:
    pickle.dump(scaler, f)

with open(os.path.join(MODEL_DIR, "burnout_class_encoder.pkl"), "wb") as f:
    pickle.dump(class_enc, f)

with open(os.path.join(MODEL_DIR, "burnout_planet_encoder.pkl"), "wb") as f:
    pickle.dump(planet_enc, f)

with open(os.path.join(MODEL_DIR, "burnout_house_encoder.pkl"), "wb") as f:
    pickle.dump(house_enc, f)

with open(os.path.join(MODEL_DIR, "burnout_sleep_encoder.pkl"), "wb") as f:
    pickle.dump(sleep_enc, f)

print("Burnout model training complete!")
