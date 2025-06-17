# predict_service.py ─────────────────────────────────────────────
# API de “prédiction” aléatoire (+5/+10/+15 min)
# ---------------------------------------------------------------
import random
from typing import List, Tuple

from fastapi import FastAPI
from pydantic import BaseModel, Field

# ────────────────────────────────────────────────────────────────
class VesselInput(BaseModel):
    mmsi: int
    lat: float
    lon: float
    sog: float = Field(..., alias="sog")  # non utilisé, mais on garde la clé
    cog: float = Field(..., alias="cog")

class PredictionPoint(BaseModel):
    minutes: int
    lat: float
    lon: float

class PredictionOut(BaseModel):
    mmsi: int
    now: Tuple[float, float]
    predictions: List[PredictionPoint]

# ────────────────────────────────────────────────────────────────
app = FastAPI(title="Predictrix-Random", version="0.1")

PRED_MINUTES = [5, 10, 15]
NOISE_DEG    = 0.01              # ±0.01° ≈ 1 km

# ------------------------------------------------------------
# Compatibilité CLI : fonction simple qui renvoie (lat, lon)
# ------------------------------------------------------------
#  Pour compatibilité avec predict_cli.py
def predict(lat: float, lon: float, sog: float, cog: float, minutes: int):
    """
    Renvoie (lat, lon) aléatoires à 'minutes' minutes.
    Signature = 5 arguments comme l'exige predict_cli.py
    """
    dlat = random.uniform(-NOISE_DEG, NOISE_DEG)
    dlon = random.uniform(-NOISE_DEG, NOISE_DEG)
    return lat + dlat, lon + dlon


@app.post("/predict", response_model=PredictionOut)
def predict_stub(inp: VesselInput):
    preds: List[PredictionPoint] = []

    for m in PRED_MINUTES:
        dlat = random.uniform(-NOISE_DEG, NOISE_DEG)
        dlon = random.uniform(-NOISE_DEG, NOISE_DEG)
        preds.append(
            PredictionPoint(
                minutes=m,
                lat=inp.lat + dlat,
                lon=inp.lon + dlon
            )
        )

    return PredictionOut(
        mmsi=inp.mmsi,
        now=(inp.lat, inp.lon),
        predictions=preds
    )

# Lancement rapide :  python predict_service.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("predict_service:app", host="127.0.0.1", port=8000, reload=True)
