import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import pickle
import os

DATA_PATH = "datasets/placement_data.csv"
MODEL_PATH = "models/placement_model.pkl"

def train_model():
    """Trains the Random Forest model for placement prediction."""
    if not os.path.exists(DATA_PATH):
        print(f"Dataset not found at {DATA_PATH}")
        return

    # Load data
    df = pd.read_csv(DATA_PATH)

    # Features and target
    X = df[['CGPA', 'AptitudeScore', 'CodingScore', 'CommunicationSkills', 'Projects', 'TechnicalSkills']]
    y = df['Placed']

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Initialize and train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {acc * 100:.2f}%")

    # Save model
    if not os.path.exists('models'):
        os.makedirs('models')
    
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"Model saved to {MODEL_PATH}")

def predict_placement(cgpa, aptitude, coding, comms, projects, technical):
    """Predicts placement probability based on input metrics."""
    if not os.path.exists(MODEL_PATH):
        train_model()

    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)

    features = np.array([[cgpa, aptitude, coding, comms, projects, technical]])
    prediction = model.predict(features)[0]
    probability = model.predict_proba(features)[0][1] # Probability of being 'Placed'

    return prediction, probability

if __name__ == "__main__":
    train_model()
