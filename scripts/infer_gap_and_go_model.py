import pandas as pd
import joblib
import os

MODEL_PATH = "gap_and_go_model.pkl"

def load_model(path=MODEL_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model file not found: {path}")
    return joblib.load(path)

def predict_gap_and_go(input_data):
    model = load_model()
    required_features = ["gap_percent", "volatility", "volume"]

    if isinstance(input_data, dict):
        input_data = pd.DataFrame([input_data])
    elif isinstance(input_data, list):
        input_data = pd.DataFrame(input_data)

    if not all(feature in input_data.columns for feature in required_features):
        raise ValueError(f"Input data must contain: {required_features}")

    predictions = model.predict(input_data[required_features])
    input_data["prediction"] = predictions
    return input_data

if __name__ == "__main__":
    # Example usage
    sample_input = {
        "gap_percent": 6.5,
        "volatility": 9.2,
        "volume": 2200000
    }

    result = predict_gap_and_go(sample_input)
    print(result)
