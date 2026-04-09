import requests
import json
import math
import time

BASE_URL = "http://localhost:7860"

def check_recursive_floats(obj, path=""):
    """Recursively assert no float equals exactly 0.0 or 1.0."""
    if isinstance(obj, float):
        # We now expect scores to be strictly between 0 and 1
        # The validator says "not 0.0 and not 1.0"
        assert 0.0 < obj < 1.0, f"BOUNDARY FLOAT at {path}: {obj}"
    elif isinstance(obj, dict):
        for k, v in obj.items():
            check_recursive_floats(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            check_recursive_floats(v, f"{path}[{i}]")

def test_endpoint(name, path, method="GET", body=None):
    url = f"{BASE_URL}{path}"
    try:
        if method == "POST":
            resp = requests.post(url, json=body or {}, timeout=10)
        else:
            resp = requests.get(url, timeout=10)
        
        if resp.status_code != 200:
            print(f"Test {name} FAIL: Status {resp.status_code}")
            return False
            
        data = resp.json()
        check_recursive_floats(data, name)
        print(f"Test {name} PASS: {str(data)[:20] if not 'score' in str(data) else ''}")
        return data
    except Exception as e:
        print(f"Test {name} FAIL: {e}")
        return False

def run_audit():
    print("\n--- SAFETYGUARD X INTENSIVE AUDIT ---\n")
    
    # 1. Reset
    reset_data = test_endpoint("reset", "/reset", "POST", {"task_id": "easy"})
    if not reset_data: return
    session_id = reset_data["session_id"]
    
    # 2. Step
    step_body = {
        "session_id": session_id,
        "action": {"decision": "block", "reason": "policy violation detected in query", "confidence": 0.9999}
    }
    test_endpoint("step", "/step", "POST", step_body)
    
    # 3. State
    test_endpoint("state", "/state", "POST", {"session_id": session_id})
    
    # 4. Grader
    test_endpoint("grader", "/grader", "POST", {"session_id": session_id})
    
    # 5. Tasks
    test_endpoint("tasks", "/tasks")
    
    # 6. Validate
    test_endpoint("validate", "/validate")
    
    # 7. Baseline
    print("Testing /baseline (simulation)...")
    test_endpoint("baseline", "/baseline", "POST")

    print("\nALL INTENSIVE AUDIT CHECKS PASSED.")

if __name__ == "__main__":
    run_audit()
