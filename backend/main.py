import os, io, re, json, time, yaml, math, regex
from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
import httpx

API_TOKEN = os.getenv("API_TOKEN", "devtoken")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/events.db")
ML_URL = f"http://ml:{os.getenv('ML_PORT','8001')}"

# --- DB bootstrap ---
engine = create_engine(DATABASE_URL.replace("sqlite:///", "sqlite:////"))  # absolute path for container
with engine.connect() as conn:
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER NOT NULL,
        kind TEXT NOT NULL,
        details TEXT NOT NULL,
        score REAL DEFAULT 0.0
    )"""))
    conn.commit()

# --- Prometheus metrics ---
EVENTS_TOTAL = Counter("observa_events_total", "Total events", ["kind"])
DRIFT_SCORE_GAUGE = Gauge("observa_latest_drift_score", "Latest drift anomaly score")

# --- App ---
app = FastAPI(title="ObservaGuard Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def auth(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    if authorization.split(" ", 1)[1] != API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")

class DriftEvent(BaseModel):
    manifest: str
    source: str = "uploaded"

class CommitPayload(BaseModel):
    diff: str

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[-_]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
]
def shannon_entropy(s: str) -> float:
    if not s: return 0.0
    from collections import Counter
    counts = Counter(s)
    probs = [c/len(s) for c in counts.values()]
    return -sum(p*math.log2(p) for p in probs)

def score_secret_leak(text: str) -> float:
    hits = sum(1 for rgx in SECRET_PATTERNS if rgx.search(text))
    # entropy-based heuristic
    tokens = re.findall(r"[A-Za-z0-9_\-]{20,}", text)
    entropies = [shannon_entropy(t) for t in tokens]
    high_entropy = sum(1 for e in entropies if e > 3.6)  # heuristic
    return min(1.0, 0.2*hits + 0.1*high_entropy)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/drift/check")
def check_drift(evt: DriftEvent, authorization: str = Depends(auth)):
    # Parse YAML and basic checks
    try:
        data = list(yaml.safe_load_all(evt.manifest))
    except Exception as e:
        raise HTTPException(400, f"Invalid YAML: {e}")
    # Simple heuristic: replicas or image tag changes
    changes = 0
    for doc in data:
        if not isinstance(doc, dict): 
            continue
        spec = doc.get("spec", {})
        if "replicas" in spec and spec["replicas"] in (0, 100):
            changes += 1
        templ = spec.get("template", {}).get("spec", {})
        for c in templ.get("containers", []):
            image = c.get("image", "")
            if ":latest" in image or ":dev" in image:
                changes += 1
    # Ask ML for anomaly score
    payload = {"features": [changes, len(evt.manifest), evt.manifest.count("image:")]}
    try:
        r = httpx.post(f"{ML_URL}/score", json=payload, timeout=5.0)
        r.raise_for_status()
        score = r.json().get("score", 0.0)
    except Exception:
        score = min(1.0, changes/5.0)
    DRIFT_SCORE_GAUGE.set(score)
    EVENTS_TOTAL.labels(kind="drift").inc()
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO events(ts,kind,details,score) VALUES(:ts,:k,:d,:s)"),
                     dict(ts=int(time.time()), k="drift", d=json.dumps(payload), s=score))
    return {"score": score, "changes": changes}

@app.post("/secret/check")
def check_secret(payload: CommitPayload, authorization: str = Depends(auth)):
    leak_score = score_secret_leak(payload.diff)
    EVENTS_TOTAL.labels(kind="secret").inc()
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO events(ts,kind,details,score) VALUES(:ts,:k,:d,:s)"),
                     dict(ts=int(time.time()), k="secret", d=payload.diff, s=leak_score))
    return {"score": leak_score}

@app.get("/events")
def list_events(authorization: str = Depends(auth)):
    from fastapi.responses import JSONResponse
    rows = []
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id, ts, kind, score FROM events ORDER BY ts DESC LIMIT 200"))
        rows = [dict(r._mapping) for r in res.fetchall()]
    return rows

from fastapi.responses import Response
