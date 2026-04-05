# ============================================================
# SafetyGuard X — FastAPI Server
# ============================================================

import os
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.responses import HTMLResponse 


from app.config import PROJECT_NAME, VERSION, DESCRIPTION
from app.models import AgentAction, ResetResult, StepResult, StateResult, TaskInfo
from app.env import env_reset, env_step, env_state, env_grader, _leaderboard
from app.tasks import list_all_tasks

# ── App ───────────────────────────────────────────────────────
app = FastAPI(
    title=PROJECT_NAME,
    version=VERSION,
    description=DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request Models ────────────────────────────────────────────
class ResetRequest(BaseModel):
    task_id:        str = "easy"
    scenario_index: int = 0

class StepRequest(BaseModel):
    session_id: str
    action:     AgentAction

class GraderRequest(BaseModel):
    session_id: str

# ── Root → redirect to UI ─────────────────────────────────────

# @app.get("/", response_class=HTMLResponse, include_in_schema=False)
# async def root():
#     # Try multiple possible paths for HF Spaces compatibility
#     possible_paths = [
#         "app/static/index.html",
#         "static/index.html", 
#         os.path.join(os.path.dirname(__file__), "static", "index.html"),
#     ]
    
#     for path in possible_paths:
#         if os.path.exists(path):
#             with open(path, "r", encoding="utf-8") as f:
#                 return HTMLResponse(content=f.read())
    
#     # Final fallback — show working links
#     return HTMLResponse(content="""
# <!DOCTYPE html>
# <html>
# <head>
# <title>SafetyGuard X</title>
# <style>
# body{background:#050b18;color:#e8f4fd;font-family:monospace;margin:0;padding:40px;text-align:center;}
# h1{color:#00d4ff;font-size:2rem;margin-bottom:10px;}
# p{color:#00ff88;margin-bottom:30px;}
# .links{display:flex;flex-direction:column;gap:12px;max-width:500px;margin:0 auto;}
# a{display:block;padding:12px 20px;background:rgba(0,212,255,0.1);border:1px solid rgba(0,212,255,0.3);border-radius:8px;color:#00d4ff;text-decoration:none;font-size:0.9rem;}
# a:hover{background:rgba(0,212,255,0.2);}
# </style>
# </head>
# <body>
# <h1>🛡️ SafetyGuard X</h1>
# <p>Adversarial AI Safety Stress Testing Environment</p>
# <div class="links">
# <a href="/ui">🎮 Open Interactive Dashboard</a>
# <a href="/docs">📖 API Documentation</a>
# <a href="/health">✅ Health Check</a>
# <a href="/tasks">📋 Tasks List</a>
# <a href="/validate">✔️ Validate</a>
# <a href="/leaderboard">🏆 Leaderboard</a>
# </div>
# </body>
# </html>
# """)
#  grok update 
# ──────────────────────────────────────────────────────────────
# CRITICAL: Mount static folder (fixes CSS/JS not loading)
# ──────────────────────────────────────────────────────────────
base_dir = os.path.dirname(os.path.abspath(__file__))   # folder containing main.py
static_dir = os.path.join(base_dir, "static")

# HF sometimes puts the app one level deeper — safety check
if not os.path.exists(static_dir):
    static_dir = os.path.join(os.path.dirname(base_dir), "static")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ──────────────────────────────────────────────────────────────
# ROOT ROUTE — serves real index.html + perfect fallback
# ──────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    # All possible locations HF might place index.html
    possible_paths = [
        os.path.join(static_dir, "index.html"),                    # Best on HF
        os.path.join(base_dir, "static", "index.html"),
        "app/static/index.html",
        "static/index.html",
    ]
    
    for file_path in possible_paths:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    
    # Final nice fallback (never blank page again)
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
<title>SafetyGuard X</title>
<style>
body{background:#050b18;color:#e8f4fd;font-family:monospace;margin:0;padding:40px;text-align:center;}
h1{color:#00d4ff;font-size:2rem;margin-bottom:10px;}
p{color:#00ff88;margin-bottom:30px;}
.links{display:flex;flex-direction:column;gap:12px;max-width:500px;margin:0 auto;}
a{display:block;padding:12px 20px;background:rgba(0,212,255,0.1);border:1px solid rgba(0,212,255,0.3);border-radius:8px;color:#00d4ff;text-decoration:none;font-size:0.9rem;}
a:hover{background:rgba(0,212,255,0.2);}
</style>
</head>
<body>
<h1>🛡️ SafetyGuard X</h1>
<p>Adversarial AI Safety Stress Testing Environment</p>
<div class="links">
<a href="/ui">🎮 Open Interactive Dashboard</a>
<a href="/docs">📖 API Documentation</a>
<a href="/health">✅ Health Check</a>
<a href="/tasks">📋 Tasks List</a>
<a href="/validate">✔️ Validate</a>
<a href="/leaderboard">🏆 Leaderboard</a>
</div>
</body>
</html>
""")

@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "environment": PROJECT_NAME}

# ── Core OpenEnv Endpoints──────────────────────────────────────────────
@app.post("/reset", response_model=ResetResult, tags=["openenv"])
def reset(request: ResetRequest):
    try:
        return env_reset(request.task_id, request.scenario_index)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/step", response_model=StepResult, tags=["openenv"])
def step(request: StepRequest):
    try:
        return env_step(request.session_id, request.action)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state", response_model=StateResult, tags=["openenv"])
def state(session_id: str = Query(...)):
    try:
        return env_state(session_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks", response_model=List[TaskInfo], tags=["openenv"])
def tasks():
    try:
        return list_all_tasks()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/grader", tags=["openenv"])
def grader(request: GraderRequest):
    try:
        return env_grader(request.session_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/baseline", tags=["openenv"])
def baseline():
    try:
        from baseline_inference import run_baseline
        results = run_baseline()
        overall = round(sum(r["mean_score"] for r in results) / len(results), 4)
        return {"model": "mock_agent", "results": results, "overall_mean": overall}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/validate", tags=["openenv"])
def validate():
    return {
        "name":           "safetyguard-x",
        "version":        "1.0.0",
        "spec_compliant": True,
        "tasks":          ["easy", "medium", "hard", "expert"],
        "endpoints":      ["/reset","/step","/state","/tasks","/grader","/baseline","/leaderboard"],
        "reward_range":   [0.0, 1.0],
        "deterministic":  True,
        "multi_turn":     True,
        "attack_types":   ["direct","semantic_disguise","roleplay_jailbreak","emotional_manip","encoded"],
    }

@app.get("/leaderboard", tags=["openenv"])
def leaderboard():
    sorted_lb = sorted(_leaderboard, key=lambda x: x["score"], reverse=True)
    return {
        "top_scores":     sorted_lb[:10],
        "total_episodes": len(_leaderboard),
        "average_score":  round(sum(x["score"] for x in _leaderboard) / max(len(_leaderboard), 1), 4),
    }

# ── Static UI ─────────────────────────────────────────────────
_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(_static_dir):
    app.mount("/ui", StaticFiles(directory=_static_dir, html=True), name="ui")

# ── Entry Point ───────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)