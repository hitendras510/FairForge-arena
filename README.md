 ---
Title: SafetyForge Arena v3.0 (SafetyGuard X)     
emoji: 🛡️🔥   
colorFrom: red   
colorTo: blue  
sdk: docker   
pinned: true    
tags:
  - openenv
  - ai-safety
  - adversarial
  - reinforcement-learning
  - stables-baselines3
  - basilisk-redteamer
---

 # 🛡️ SafetyForge Arena v3.0 — The RL Safety Gym


I upgraded SafetyGuard X into **SafetyForge Arena v3.0** — a complete RL safety stress testing gym.
It now features the **Basilisk Red-Teamer** for dynamic attack generation and a built-in **Stable-Baselines3** training pipeline.

🛡️ **What's New in v3.0**
├── ⚔️ **Basilisk Red-Teamer**: Adaptive adversarial attacks (Template + LiteLLM)
├── 🏋️ **RL Training Loop**: Stable-Baselines3 (PPO) integration
├── 📦 **Dataset Exporter**: Direct export to Hugging Face fine-tuning format
├── 📊 **Live Analytics**: Plotly-powered training curve dashboard
└── 🔄 **OpenEnv Phase 2**: Fully compliant with current submission standards

🛡️ **Core Specs**
├── 4 tasks: easy → medium → hard → expert                           
├── 5 attack types: direct, encoded, roleplay, emotional, semantic   
├── 6-metric reward function (now RL-shaped)
├── Full OpenEnv spec: reset/step/state                             
├── Deployed and live on HuggingFace                                 
   

## 🔗 Links

| Resource | URL |
|----------|-----|
| 🤗 HuggingFace Space | [https://huggingface.co/spaces/abhishek0164/safetyguard-x](https://huggingface.co/spaces/abhishek0164/safetyguard-x) |
| 🎮 Live Dashboard UI | [https://abhishek0164-safetyguard-x.hf.space/ui](https://abhishek0164-safetyguard-x.hf.space/ui) |
| 📖 API Documentation | [https://abhishek0164-safetyguard-x.hf.space/docs](https://abhishek0164-safetyguard-x.hf.space/docs) |
| 💻 GitHub Repo | [https://github.com/AbhishekGupta0164/Meta-AI-OpenEnv-SST-Project.git](https://github.com/AbhishekGupta0164/Meta-AI-OpenEnv-SST-Project.git) |

---

## 🏗️ Architecture — 5 Engines
```
┌─────────────────────────────────────────────────────┐
│                 SafetyForge Arena v3.0               │
├──────────────┬──────────────┬───────────────────────┤
│   Policy     │   Adversary  │      Memory           │
│   Engine     │   Engine     │      Engine           │
│              │ (Basilisk)   │                       │
│ 8 rules      │ Adaptive     │ History tracking      │
│ Conflict     │ Attack Gen   │ Risk trajectory       │
│ detection    │ (LiteLLM)    │ Escalation patterns   │
├──────────────┴──────────────┴───────────────────────┤
│              Grader Engine                          │
│   6-metric weighted score (0.01 – 0.99)              │
├─────────────────────────────────────────────────────┤
│              Environment Engine                     │
│         reset() / step() / state()                  │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 Tasks

| Task | Difficulty | Max Turns | Expected Score | Adversary Mode |
|------|-----------|-----------|----------------|----------------|
| `easy` | 🟢 Easy | 3 | 0.90 | Static |
| `medium` | 🟡 Medium | 5 | 0.75 | Static |
| `hard` | 🔴 Hard | 7 | 0.55 | Dynamic |
| `expert` | ⚫ Expert | 10 | 0.45 | **Basilisk Adaptive** |

---

## ⚔️ Attack Types

| Type | Description |
|------|-------------|
| `DIRECT` | Straightforward harmful request |
| `SEMANTIC_DISGUISE` | Harmful intent in safe framing |
| `ROLEPLAY_JAILBREAK` | Jailbreak via fiction/roleplay |
| `EMOTIONAL_MANIP` | Guilt, urgency, sympathy attacks |
| `ENCODED` | Base64/leet-speak obfuscation |

---

## 🚀 Quick Start (v3.0 Training)

### 1. Training a Policy
To train a safety policy locally using Stable-Baselines3:
```bash
# Install v3.0 dependencies
pip install -r requirements.txt

# Run the training pipeline
python app/trainer.py --episodes 500 --task expert
```

### 2. Exporting a Dataset
After training, export the data for fine-tuning:
```bash
# Export the memory buffer to JSONL
curl http://localhost:7860/export_dataset --output training_data.jsonl
```

### 3. Running with Basilisk (Real LLMs)
Update your `.env` file to enable real adversarial models:
```env
REDTEAMER_MODEL=claude-3-5-sonnet-20240620
ANTHROPIC_API_KEY=sk-...
```

---

## 🔌 API Usage

### Reset Episode
```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy", "scenario_index": 0}'
```

### Take a Step
```bash
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "<sid>",
    "action": {
      "decision": "block",
      "reason": "violates policy",
      "confidence": 0.95
    }
  }'
```

## 📁 Project Structure
```
safetyguard-x/
├── app/
│   ├── trainer.py        ← PPO Training Pipeline
│   ├── gym_wrapper.py    ← Gymnasium Interface
│   ├── exporter.py       ← HF Dataset Export
│   ├── redteamer.py      ← Basilisk Adaptive Adversary
│   ├── adversary.py      ← Integrated Dynamic Gen
│   ├── env.py            ← Environment Engine
│   └── static/index.html ← Plotly Analytics Dashboard
├── openenv.yaml          ← OpenEnv spec
└── README.md
```

## 📜 License

MIT