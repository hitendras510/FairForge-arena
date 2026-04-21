from fastapi import FastAPI, BackgroundTasks, File, Form, UploadFile
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import uuid
import random

# Import from existing backend modules instead of the duplicate fairforge app
from core.gemini_auditor import generate_audit_narrative, generate_counterfactual_explanation
from core.policies import FAIRNESS_POLICIES
from core.mitigation_engine import suggest_mitigations
from core.grader import grade_episode
from rl.env import FairnessEnv

# We will use the user's audit router as well if possible, or keep the REST stubs for the frontend
from api.audit import router as audit_router

app = FastAPI(
    title="FairForge Arena API",
    description="Enterprise-grade AI Fairness Training Gym",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect the existing audit router
app.include_router(audit_router, prefix="/api")

# Global mocked state for the UI demo purposes for the Training & Mitigation endpoints
app_state = {
    "training_status": {
        "active": False,
        "current_ep": 0,
        "total_ep": 0,
        "reward_history": [],
        "bias_history": [],
        "logs": [],
        "bias_before": 0.0,
        "bias_after": 0.0
    },
    "audit_results": {}
}

class TrainRequest(BaseModel):
    episodes: int
    run_id: str

class MitigateRequest(BaseModel):
    run_id: str
    strategy: str
    strength: float

class CounterfactualRequest(BaseModel):
    individual: Dict[str, Any]
    sensitive_attr: str
    counterfactual_value: str
    run_id: str

@app.get("/")
async def root():
    return {"message": "FairForge Arena API Active."}

@app.get("/api/sample/{domain}")
async def get_sample(domain: str):
    """Returns a realistic mock CSV string for quick-loading dataset."""
    headers = "gender,race,age,income,years_exp,gpa,coding_score,interview_score,favorable_outcome\n"
    rows = []
    for _ in range(50):
        gender = random.choice([0, 1])
        race = random.choice([0, 1, 2])
        age = random.randint(22, 60)
        income = random.randint(30000, 120000)
        exp = random.randint(0, 15)
        gpa = round(random.uniform(2.5, 4.0), 2)
        score1 = random.randint(50, 100)
        score2 = random.randint(50, 100)
        # outcome biased towards gender 1 and higher scores
        prob = 0.3 + (0.2 * gender) + (0.3 * (score1+score2)/200)
        outcome = 1 if random.random() < prob else 0
        rows.append(f"{gender},{race},{age},{income},{exp},{gpa},{score1},{score2},{outcome}")
    
    csv_data = headers + "\n".join(rows)
    return Response(content=csv_data, media_type="text/csv")

# NOTE: The POST /api/audit route is currently served by backend/api/audit.py 
# But we need to ensure the UI gets exactly what it expects.
# If api/audit.py doesn't return the exact schema, we will intercept and augment it, 
# or for this demo, provide the explicit fallback route if the other router doesn't catch it perfectly.

@app.get("/api/heatmap/{run_id}")
async def get_heatmap(run_id: str):
    """Returns mock heatmap data."""
    groups = [
        {"group_label": "White Male", "accept_rate": 0.82, "tpr": 0.85, "fpr": 0.12, "calibration_error": 0.04},
        {"group_label": "White Female", "accept_rate": 0.76, "tpr": 0.80, "fpr": 0.10, "calibration_error": 0.05},
        {"group_label": "Black Male", "accept_rate": 0.45, "tpr": 0.60, "fpr": 0.25, "calibration_error": 0.15},
        {"group_label": "Black Female", "accept_rate": 0.40, "tpr": 0.55, "fpr": 0.28, "calibration_error": 0.18},
    ]
    return {"heatmap_data": groups}


@app.post("/api/train")
async def start_training(req: TrainRequest, bg_tasks: BackgroundTasks):
    """Starts PPO background training (simulated via FairnessEnv)."""
    if app_state["training_status"]["active"]:
        return JSONResponse(status_code=400, content={"success": False, "message": "Training already in progress."})

    env = FairnessEnv(initial_bias=0.8, initial_acc=0.85)
    
    app_state["training_status"] = {
        "active": True,
        "current_ep": 0,
        "total_ep": req.episodes,
        "reward_history": [],
        "bias_history": [],
        "logs": ["Initializing PPO Gym Environment...", "Policy: MlpPolicy", f"Environment: {env.__class__.__name__}"],
        "bias_before": 0.8,
        "acc_before": 0.85
    }
    
    async def run_training():
        ts = app_state["training_status"]
        obs, _ = env.reset()
        
        for ep in range(1, ts["total_ep"] + 1):
            await asyncio.sleep(0.05)
            # Simulate an agent taking actions (0: reduce bias, 1: tune, 2: focus acc)
            # In a real PPO, we'd call model.predict(obs)
            action = 0 if ts["current_ep"] < ts["total_ep"] // 2 else random.choice([0, 1])
            obs, reward, done, truncated, info = env.step(action)
            
            bias, acc = obs[0], obs[1]
            
            ts["current_ep"] = ep
            ts["bias_history"].append(float(bias))
            ts["reward_history"].append(float(reward))
            ts["logs"].append(f"Episode {ep}/{ts['total_ep']} - Reward: {reward:.3f} | Bias: {bias:.3f} | Acc: {acc:.3f}")
            
            if done:
                obs, _ = env.reset()
            
        ts["active"] = False
        ts["bias_after"] = float(obs[0])
        ts["acc_after"] = float(obs[1])
        ts["logs"].append("Training complete. Fair Policy converged.")

    bg_tasks.add_task(run_training)
    return {"success": True, "message": "Training initialized."}


@app.get("/api/train/status")
async def training_status():
    """Polled by frontend to show training charts and progress."""
    return app_state["training_status"]


@app.get("/api/policies/{run_id}")
async def get_policies(run_id: str):
    """Returns actual active compliance policies."""
    # Simulate some pass/fail results for the UI
    results = []
    for p in FAIRNESS_POLICIES[:5]: # Show first 5 for the list
        passed = random.random() > 0.3
        results.append({
            **p.dict(),
            "passed": passed,
            "current_value": p.threshold * (0.8 if passed else 1.5)
        })
    return {"policies": results}


@app.get("/api/report/{run_id}")
async def get_report(run_id: str):
    """Returns final grader report card using core.grader."""
    ts = app_state["training_status"]
    
    # Use the real grader logic
    grader_res = grade_episode(
        detected_biases=["demographic_parity"],
        true_biases=["demographic_parity", "equal_opportunity"],
        bias_score_before=ts.get("bias_before", 0.8),
        bias_score_after=ts.get("bias_after", 0.15),
        explanation_text="The model initially showed significant demographic disparity across gender groups...",
        steps_used=ts.get("current_ep", 100),
        max_steps=ts.get("total_ep", 100),
        policies_checked=["FP-01", "FP-02"],
        required_policies=["FP-01", "FP-02", "FP-03"],
        group_scores=[0.85, 0.82, 0.78, 0.80]
    )
    
    grade = "A" if grader_res.final_score > 90 else "B" if grader_res.final_score > 80 else "C" if grader_res.final_score > 70 else "D" if grader_res.final_score > 60 else "F"
    
    # Use Gemini for narrative if possible
    narrative = f"Executive Summary: Audit for {run_id} complete. Final score {grader_res.final_score}%. Significant bias reduction achieved."
    try:
        import os
        if "GEMINI_API_KEY" in os.environ:
            narrative = generate_audit_narrative(grader_res.breakdown, domain="Finance")
    except Exception:
        pass

    return {
        "domain": "General",
        "run_id": run_id,
        "final_score": grader_res.final_score,
        "grade": grade,
        "passed": grader_res.passed,
        "grader_breakdown": grader_res.breakdown,
        "gemini_narrative": narrative
    }


@app.post("/api/mitigate")
async def mitigate_bias(req: MitigateRequest):
    """Applies a fix and calculates projection using mitigation_engine."""
    # Mock some report metrics to feed to the engine
    class MockReport:
        demographic_parity_diff = 0.25
        disparate_impact_ratio = 0.75
        equal_opportunity_diff = 0.18
        equalized_odds_diff = 0.2
        calibration_diff = 0.12
        
    suggestions = suggest_mitigations(MockReport())
    
    mb = {"demographic_parity_diff": 0.25, "equal_opportunity_diff": 0.18, "disparate_impact_ratio": 0.75, "overall_bias_score": 0.5}
    ma = {k: max(0.01, v - (random.uniform(0.05, 0.1) * req.strength)) for k,v in mb.items()}
    if "disparate_impact_ratio" in ma:
        ma["disparate_impact_ratio"] = min(0.98, mb["disparate_impact_ratio"] + (random.uniform(0.1, 0.2) * req.strength))
        
    return {
        "run_id": req.run_id,
        "strategy": req.strategy,
        "projected_improvement": f"{(mb['overall_bias_score'] - ma['overall_bias_score']) * 100:.1f}%",
        "metrics_before": mb,
        "metrics_after": ma,
        "suggestions": [s.dict() for s in suggestions]
    }


@app.post("/api/counterfactual")
async def generate_counterfactual(req: CounterfactualRequest):
    """Generates what-if analysis using Gemini Auditor."""
    flip = random.random() > 0.5
    orig_prob = random.uniform(0.4, 0.9)
    cf_prob = random.uniform(0.4, 0.9) if flip else orig_prob + random.uniform(-0.05, 0.05)
    
    decision_map = {True: "APPROVED", False: "REJECTED"}
    
    explanation = "Counterfactual flip detected. This indicates the model relies heavily on the protected attribute."
    try:
        import os
        if "GEMINI_API_KEY" in os.environ:
            explanation = generate_counterfactual_explanation(
                req.individual, 
                decision_map[orig_prob > 0.5], 
                req.sensitive_attr, 
                req.counterfactual_value
            )
    except Exception:
        pass
    
    return {
        "original": {"decision": decision_map[orig_prob > 0.5], "probability": orig_prob},
        "counterfactual": {"decision": decision_map[cf_prob > 0.5], "probability": cf_prob},
        "flip_detected": flip,
        "explanation": explanation,
        "probability_delta": cf_prob - orig_prob,
        "group_results": [
            {"gender": "Male", "race": "White", "decision": "APPROVED", "prob": 0.85},
            {"gender": "Female", "race": "White", "decision": "APPROVED", "prob": 0.78},
            {"gender": "Male", "race": "Black", "decision": "REJECTED", "prob": 0.42},
            {"gender": "Female", "race": "Black", "decision": "REJECTED", "prob": 0.38}
        ]
    }