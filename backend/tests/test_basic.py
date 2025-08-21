import os, json
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)
headers = {"Authorization": "Bearer " + os.getenv("API_TOKEN","devtoken")}

def test_health():
    r = client.get("/health")
    assert r.status_code == 200

def test_secret():
    r = client.post("/secret/check", json={"diff":"api_key=ABCD1234EFGH5678TOKEN"}, headers=headers)
    assert r.status_code == 200
    assert "score" in r.json()

def test_drift():
    manifest = """
apiVersion: apps/v1
kind: Deployment
metadata: {name: demo}
spec:
  replicas: 0
  template:
    spec:
      containers:
        - name: web
          image: nginx:latest
"""
    r = client.post("/drift/check", json={"manifest": manifest}, headers=headers)
    assert r.status_code == 200
    assert "score" in r.json()
