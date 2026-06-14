"""
Application FastAPI pour l'interface web de Tych.
"""

from __future__ import annotations

import numpy as np
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from math import sqrt
from tych.pendulum import double_pendulum_random_list, simulate_trajectory
from tych.comparison import compute_comparison
from tych.statistics import compute_quality_score, compute_lyapunov

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Tych", description="Générateur de nombres aléatoires chaotique")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PhysicsParams(BaseModel):
    m1: float = Field(default=1.0, ge=0.1, le=10.0)
    m2: float = Field(default=1.0, ge=0.1, le=10.0)
    l1: float = Field(default=1.0, ge=0.2, le=5.0)
    l2: float = Field(default=1.0, ge=0.2, le=5.0)
    g: float = Field(default=9.81, ge=0.5, le=30.0)
    damping: float = Field(default=0.999, ge=0.900, le=1.0)


class GenerateRequest(PhysicsParams):
    n: int = Field(default=1000, ge=1, le=100000)
    pendulums: int = Field(default=3, ge=1, le=20)
    noise: float = Field(default=0.2, ge=0.0, le=5.0)


class CompareRequest(PhysicsParams):
    n: int = Field(default=5000, ge=100, le=100000)
    pendulums: int = Field(default=3, ge=1, le=20)
    noise: float = Field(default=0.2, ge=0.0, le=5.0)


class TrajectoryRequest(PhysicsParams):
    steps: int = Field(default=1500, ge=100, le=5000)
    pendulums: int = Field(default=3, ge=1, le=10)
    seed: Optional[int] = Field(default=None)


class EvaluateRequest(PhysicsParams):
    n: int = Field(default=2000, ge=200, le=20000)
    pendulums: int = Field(default=3, ge=1, le=20)
    noise: float = Field(default=0.2, ge=0.0, le=5.0)


class QualityRequest(PhysicsParams):
    n: int = Field(default=2000, ge=200, le=20000)
    pendulums: int = Field(default=3, ge=1, le=20)
    noise: float = Field(default=0.2, ge=0.0, le=5.0)
    compute_apen: bool = Field(default=True)
    compute_lyapunov: bool = Field(default=False)


class SweepRequest(PhysicsParams):
    param: str = Field(..., description="Nom du paramètre à faire varier (noise, pendulums, m1, m2, l1, l2, g, damping)")
    range_min: float
    range_max: float
    steps: int = Field(default=8, ge=2, le=20)
    n: int = Field(default=500, ge=100, le=5000)
    pendulums: int = Field(default=3, ge=1, le=20)
    noise: float = Field(default=0.2, ge=0.0, le=5.0)
    compute_apen: bool = Field(default=False)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/generate")
async def generate(req: GenerateRequest):
    try:
        numbers = await run_in_threadpool(
            double_pendulum_random_list,
            n=req.n,
            n_pendulums=req.pendulums,
            noise_level=req.noise,
            m1=req.m1, m2=req.m2,
            l1=req.l1, l2=req.l2,
            g=req.g, damping=req.damping,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    arr = np.array(numbers)
    counts, bin_edges = np.histogram(arr, bins=20, range=(0, 1))
    bin_centers = ((bin_edges[:-1] + bin_edges[1:]) / 2).tolist()

    return {
        "n": len(numbers),
        "mean": float(arr.mean()),
        "std": float(arr.std()),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "sample": numbers[:50],
        "histogram": {
            "bin_centers": bin_centers,
            "counts": counts.tolist(),
        },
    }


@app.post("/api/compare")
async def compare(req: CompareRequest):
    try:
        data = await run_in_threadpool(
            compute_comparison,
            n=req.n,
            n_pendulums=req.pendulums,
            noise_level=req.noise,
            m1=req.m1, m2=req.m2,
            l1=req.l1, l2=req.l2,
            g=req.g, damping=req.damping,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Retirer les données brutes internes (tableaux numpy lourds)
    data.pop("_a", None)
    data.pop("_b", None)
    data.pop("_a_norm", None)
    data.pop("_b_norm", None)

    return data


@app.post("/api/trajectory")
async def trajectory(req: TrajectoryRequest):
    try:
        data = await run_in_threadpool(
            simulate_trajectory,
            steps=req.steps,
            n_pendulums=req.pendulums,
            seed=req.seed,
            m1=req.m1, m2=req.m2,
            l1=req.l1, l2=req.l2,
            g=req.g, damping=req.damping,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return data


@app.post("/api/evaluate")
async def evaluate(req: EvaluateRequest):
    _IDEAL_MEAN = 0.5
    _IDEAL_STD  = 1.0 / sqrt(12)

    try:
        numbers = await run_in_threadpool(
            double_pendulum_random_list,
            n=req.n,
            n_pendulums=req.pendulums,
            noise_level=req.noise,
            m1=req.m1, m2=req.m2,
            l1=req.l1, l2=req.l2,
            g=req.g, damping=req.damping,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    arr = np.array(numbers)
    mean = float(arr.mean())
    std  = float(arr.std())

    score_centering  = max(0.0, 1.0 - abs(mean - _IDEAL_MEAN) / 0.10)
    score_dispersion = max(0.0, 1.0 - abs(std  - _IDEAL_STD)  / 0.05)

    try:
        from scipy.stats import kstest as _kstest
        ks_stat, ks_p = _kstest(arr, 'uniform')
        ks_stat, ks_p = float(ks_stat), float(ks_p)
    except Exception:
        ks_stat, ks_p = 0.5, 0.5
    score_ks = ks_p

    counts, bin_edges = np.histogram(arr, bins=20, range=(0, 1))
    bin_centers = ((bin_edges[:-1] + bin_edges[1:]) / 2).tolist()
    cv = float(np.std(counts) / np.mean(counts)) if np.mean(counts) > 0 else 1.0
    score_uniformity = max(0.0, 1.0 - cv / 0.5)

    score = round((score_centering  * 0.20
                 + score_dispersion * 0.20
                 + score_ks         * 0.40
                 + score_uniformity * 0.20) * 100)

    return {
        "score": score,
        "sub_scores": {
            "centering":   round(score_centering,  4),
            "dispersion":  round(score_dispersion, 4),
            "ks":          round(score_ks,          4),
            "uniformity":  round(score_uniformity,  4),
        },
        "raw": {
            "mean":         mean,
            "std":          std,
            "ks_statistic": ks_stat,
            "ks_p_value":   ks_p,
        },
        "histogram": {
            "bin_centers": bin_centers,
            "counts":      counts.tolist(),
        },
    }


@app.post("/api/quality")
async def quality(req: QualityRequest):
    try:
        numbers = await run_in_threadpool(
            double_pendulum_random_list,
            n=req.n,
            n_pendulums=req.pendulums,
            noise_level=req.noise,
            m1=req.m1, m2=req.m2,
            l1=req.l1, l2=req.l2,
            g=req.g, damping=req.damping,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    result = await run_in_threadpool(
        compute_quality_score,
        numbers,
        req.compute_apen,
    )

    if req.compute_lyapunov:
        lya = await run_in_threadpool(
            compute_lyapunov,
            req.m1, req.m2, req.l1, req.l2, req.g, req.damping,
        )
        result["lyapunov"] = round(lya, 4)

    return result


@app.post("/api/lab/sweep")
async def lab_sweep(req: SweepRequest):
    _PARAM_RANGES = {
        "noise":     (0.0, 5.0),
        "pendulums": (1,   20),
        "m1":        (0.1, 10.0),
        "m2":        (0.1, 10.0),
        "l1":        (0.2, 5.0),
        "l2":        (0.2, 5.0),
        "g":         (0.5, 30.0),
        "damping":   (0.900, 1.0),
    }
    if req.param not in _PARAM_RANGES:
        raise HTTPException(status_code=422, detail=f"Paramètre inconnu : {req.param}")

    values = np.linspace(req.range_min, req.range_max, req.steps).tolist()
    base = dict(
        n_pendulums=req.pendulums, noise_level=req.noise,
        m1=req.m1, m2=req.m2, l1=req.l1, l2=req.l2,
        g=req.g, damping=req.damping,
    )

    results = []
    for v in values:
        kwargs = dict(base)
        if req.param == "noise":
            kwargs["noise_level"] = float(v)
        elif req.param == "pendulums":
            kwargs["n_pendulums"] = max(1, int(round(v)))
        else:
            kwargs[req.param] = float(v)

        try:
            numbers = await run_in_threadpool(
                double_pendulum_random_list, n=req.n, **kwargs
            )
            score_data = await run_in_threadpool(
                compute_quality_score, numbers, req.compute_apen
            )
            results.append({
                "param_value":  round(float(v), 4),
                "global":       int(score_data["global"]),
                "uniformite":   float(score_data["uniformite"]["score"]),
                "independance": float(score_data["independance"]["score"]),
                "entropie":     float(score_data["entropie"]["score"]),
                "moments":      float(score_data["moments"]["score"]),
            })
        except Exception:
            results.append({"param_value": round(v, 4), "global": None})

    return {"param": req.param, "points": results}


# Fichiers statiques montés en dernier pour ne pas masquer les routes API
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
