import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

DATA_DIR = os.path.join(os.path.dirname(__file__), "../Data")
OUTPUT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "gap_and_go_model.pkl")

def load_all_data(data_dir):
    all_data = []
    for file in os.listdir(data_dir):
        if file.endswith(".csv"):
            path = os.path.join(data_dir, file)
            df = pd.read_csv(path)
            all_data.append(df)
    return pd.concat(all_data, ignore_index=True)

def main():
    print("[+] Loading data...")
    df = load_all_data(DATA_DIR)

    X = df[["gap_percent", "volatility", "volume"]]
    y = df["target_10pct_spike"]

    print("[+] Splitting dataset...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("[+] Training model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    print("[+] Evaluating model...")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))

    print(f"[+] Saving model to {OUTPUT_MODEL_PATH}...")
    joblib.dump(model, OUTPUT_MODEL_PATH)

if __name__ == "__main__":
    main()
