import os, time, joblib, numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
from sklearn.ensemble import IsolationForest

MODEL_PATH = Path("/app/model.joblib")
app = FastAPI(title="ObservaGuard ML", version="0.1.0")

class Features(BaseModel):
    features: list[float]

def load_or_train():
    if MODEL_PATH.exists():
        return joblib.load(MODEL_PATH)
    # Synthetic baseline
    X = np.random.normal(0, 1, size=(256, 3))
    clf = IsolationForest(contamination=0.1, random_state=42).fit(X)
    joblib.dump(clf, MODEL_PATH)
    return clf

model = load_or_train()

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/score")
def score(f: Features):
    x = np.array(f.features).reshape(1, -1)
    s = model.decision_function(x)  # higher is less anomalous
    # Convert to [0,1] anomaly score
    norm = float(1.0 / (1.0 + np.exp(5*s)))
    return {"score": norm}
