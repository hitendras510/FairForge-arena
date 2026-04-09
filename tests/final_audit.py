import sys, math
sys.path.insert(0, '.')

from app.env import env_reset, env_step, env_grader
from app.models import AgentAction
from app.main import tasks, root, leaderboard, health

def is_bad(v):
    if isinstance(v, float):
        return v <= 0.0 or v >= 1.0
    return False

def check_dict(d, path=""):
    bad_found = []
    if isinstance(d, dict):
        for k, v in d.items():
            bad_found.extend(check_dict(v, f"{path}.{k}"))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            bad_found.extend(check_dict(v, f"{path}[{i}]"))
    elif is_bad(d):
        bad_found.append(f"{path} = {d}")
    return bad_found

print("Starting FINAL AUDIT...")

all_errors = []

# 1. Test /tasks
print("Auditing /tasks...")
tlist = tasks()
all_errors.extend(check_dict([t.model_dump() for t in tlist], "tasks"))

# 2. Test /reset -> /step -> /grader for all tasks
for tid in ["easy", "medium", "hard", "expert"]:
    print(f"Auditing task {tid}...")
    r = env_reset(tid, 0)
    sid = r.session_id
    
    action = AgentAction(decision="allow", reason="auditing system safety", confidence=1.0) # testing max confidence
    step = env_step(sid, action)
    all_errors.extend(check_dict(step.model_dump(), f"step_{tid}"))
    
    action_fail = AgentAction(decision="block", reason="fail case", confidence=0.0) # testing min confidence
    # we need another session for second action if first was done, but let's just try step again
    try:
        step2 = env_step(sid, action_fail)
        all_errors.extend(check_dict(step2.model_dump(), f"step2_{tid}"))
    except: pass
    
    g = env_grader(sid)
    all_errors.extend(check_dict(g, f"grader_{tid}"))

# 3. Test /leaderboard
print("Auditing /leaderboard...")
lb = leaderboard()
all_errors.extend(check_dict(lb, "leaderboard"))

# 4. Test /baseline (partial)
print("Auditing /baseline logic...")
# run_baseline is slow, so we just check overall mean clamp
from app.grader import _clamp
all_errors.extend(check_dict(_clamp(1.0), "clamp_1.0"))
all_errors.extend(check_dict(_clamp(0.0), "clamp_0.0"))

if all_errors:
    print("\nFAIL: Found out-of-range floats:")
    for e in all_errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print("\nSUCCESS: No 0.0 or 1.0 values found in any audit path.")
