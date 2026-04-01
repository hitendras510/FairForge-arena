
# ============================================================
# SafetyGuard X — HTTP Client
# HTTP client to call the env API
# Used by baseline_inference.py to talk to the environment
# ============================================================

import httpx
from typing import Any, Dict, Optional


class SafetyGuardClient:
    """
    Simple HTTP client for the SafetyGuard X environment.
    Use this in your own agent scripts.
    """

    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url.rstrip("/")

    def health(self) -> Dict[str, Any]:
        return self._get("/health")

    def reset(self, task_id: str = "easy", scenario_index: int = 0) -> Dict[str, Any]:
        return self._post("/reset", {
            "task_id": task_id,
            "scenario_index": scenario_index,
        })

    def step(self, session_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/step", {
            "session_id": session_id,
            "action": action,
        })

    def state(self, session_id: str) -> Dict[str, Any]:
        return self._get("/state", params={"session_id": session_id})

    def grader(self, session_id: str) -> Dict[str, Any]:
        return self._post("/grader", {"session_id": session_id})

    def tasks(self) -> Dict[str, Any]:
        return self._get("/tasks")

    def baseline(self) -> Dict[str, Any]:
        return self._post("/baseline", {})

    def _get(self, path: str, params: Dict = None) -> Dict[str, Any]:
        with httpx.Client(timeout=30.0) as client:
            r = client.get(self.base_url + path, params=params)
            r.raise_for_status()
            return r.json()

    def _post(self, path: str, data: Dict) -> Dict[str, Any]:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(
                self.base_url + path,
                json=data,
                headers={"Content-Type": "application/json"},
            )
            r.raise_for_status()
            return r.json()


# ── Quick test ────────────────────────────────────────────────

if __name__ == "__main__":
    client = SafetyGuardClient()

    print("Health:", client.health())

    reset = client.reset("easy")
    sid   = reset["session_id"]
    print("Session:", sid[:8])
    print("Query:  ", reset["observation"]["current_query"])

    result = client.step(sid, {
        "decision":   "block",
        "reason":     "violates policy P001 harmful weapon request",
        "confidence": 0.95,
    })
    print("Score:", result["reward"]["score"])
    print("Done: ", result["done"])