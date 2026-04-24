# FairForge Arena

FairForge Arena is a comprehensive fairness auditing, mitigation, and monitoring platform designed to analyze AI models across multiple domains (Hiring, Loan, Medical, Intersectional). It provides a full suite of tools to identify biases, run counterfactual analyses, simulate mitigation strategies using Reinforcement Learning, and maintain cryptographically secure audit trails.

## 🚀 Features

- **Fairness Audit Dashboard**: Run full fairness audits on your datasets to calculate critical metrics like Disparate Impact Ratio, Demographic Parity Difference, Equal Opportunity Difference, and Overall Bias Score.
- **What-If Explorer (Counterfactuals)**: Change protected attributes (like Gender or Race) and see how the model's decision flips in real-time, providing deep insights into disparate treatment.
- **Group Outcomes Heatmap**: Visualize acceptance rates, True Positive Rates (TPR), and False Positive Rates (FPR) across intersecting demographic groups.
- **RL Training (Mitigation)**: Simulate bias mitigation using Proximal Policy Optimization (PPO) to find the optimal balance between model accuracy and fairness.
- **LLM Fairness Benchmark**: Evaluate Generative AI models (GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro, Llama 3.1, Mistral Large) across gender, racial, and age biases.
- **Policy Engine**: Define, enforce, and monitor compliance against established legal and ethical fairness frameworks (e.g., EEOC Four-Fifths Rule, EU AI Act).
- **Shadow AI Scanner**: Detect unauthorized or undisclosed AI usage in text by identifying structural patterns and phraseology unique to LLMs.
- **Integrity Trail**: Cryptographically secure, hash-chained logging of all audit events to detect and prevent tampering.

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla HTML/JS/CSS (Single Page Application)
- **Storage**: MongoDB (via Motor AsyncIO)
- **Charting**: Chart.js

## ⚙️ Setup and Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd GDP-Hack2Skill
   ```

2. **Backend Setup:**
   Ensure you have Python installed. Install dependencies (e.g., `fastapi`, `uvicorn`, `motor`, `pydantic`).
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the FastAPI Server:**
   ```bash
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```
   *(Note: The backend automatically handles serving the frontend.)*

4. **Access the Application:**
   Open your browser and navigate to `http://127.0.0.1:8000`.

## 🐛 Recent Fixes & Improvements

- **Resolved Syntax Errors**: Fixed missing braces in the frontend logic preventing the dashboard from rendering correctly.
- **Counterfactual Bias Correction**: Tuned backend algorithms to accurately simulate and reflect group outcomes instead of rejecting all female profiles.
- **Performance Optimization**: Added timeout configurations to the MongoDB driver to ensure lighting-fast response times even when a local database is unavailable.

## 📝 License
This project was developed for the Google Developer Program - Hack2Skill.