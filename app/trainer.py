# ============================================================
# SafetyGuard X — RL Training Pipeline (PPO)
# Trains a safety agent via Stable-Baselines3.
# ============================================================

import os
import argparse
import numpy as np

try:
    import plotly.graph_objects as go
except ImportError:
    go = None

try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import BaseCallback
    from stable_baselines3.common.monitor import Monitor
except ImportError:
    PPO = None
    BaseCallback = object # Fallback to prevent inheritance error
    Monitor = None

from app.gym_wrapper import SafetyForgeEnv
from app.exporter import exporter
from app.env import _sessions

class SafetyTrainingCallback(BaseCallback):
    """Logs rewards and generates training curves at intervals."""
    def __init__(self, verbose=0, save_freq=100, on_episode_end=None):
        super(SafetyTrainingCallback, self).__init__(verbose)
        self.save_freq = save_freq
        self.on_episode_end = on_episode_end
        self.rewards = []
        self.avg_rewards = []

    def _on_step(self) -> bool:
        # Check for end of episode
        if self.locals['dones'][0]:
            reward = self.locals['rewards'][0]
            self.rewards.append(reward)
            
            # Trigger custom callback for progress tracking
            if self.on_episode_end:
                self.on_episode_end(len(self.rewards))

            if len(self.rewards) % self.save_freq == 0:
                avg = np.mean(self.rewards[-self.save_freq:])
                self.avg_rewards.append(avg)
                self._generate_curve()
        return True

    def _generate_curve(self):
        """Generates a Plotly training curve and saves as PNG."""
        if go is None:
            return
            
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=self.rewards, 
            mode='lines', 
            name='Episode Reward',
            line=dict(color='rgba(0, 212, 255, 0.2)')
        ))
        if self.avg_rewards:
            # Scale x to match episodes
            x_avg = [i * self.save_freq for i in range(1, len(self.avg_rewards) + 1)]
            fig.add_trace(go.Scatter(
                x=x_avg, 
                y=self.avg_rewards, 
                mode='lines+markers', 
                name=f'Avg Reward (last {self.save_freq})',
                line=dict(color='#00ff88', width=3)
            ))
        
        fig.update_layout(
            title="SafetyForge Arena — Training Progress (PPO)",
            xaxis_title="Episodes",
            yaxis_title="Safety Score",
            template="plotly_dark",
            paper_bgcolor='rgba(10, 22, 40, 1)',
            plot_bgcolor='rgba(10, 22, 40, 1)'
        )
        
        # Save to static directory for dashboard access
        target_path = os.path.join("app", "static", "training_curve.png")
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        try:
            # Check if kaleido is installed for image export
            import kaleido
            fig.write_image(target_path)
            if self.verbose > 0:
                print(f"Training curve updated: {target_path}")
        except ImportError:
            if self.verbose > 0:
                print("Kaleido not installed. Skipping PNG export, using Plotly.js in browser.")
        except Exception as e:
            if self.verbose > 0:
                print(f"Plotly image export failed: {e}")

def run_training(episodes: int = 500, task_id: str = "expert", on_episode_end=None):
    """
    Main training entry point.
    1. Initialize Env
    2. Setup PPO
    3. Train + Log
    4. Export Dataset
    """
    if PPO is None or Monitor is None:
        print("❌ Stable-Baselines3 not installed. Skipping RL training run.")
        return

    print(f"🚀 Starting SafetyForge Arena Training: {episodes} episodes on '{task_id}'")
    
    # Setup environment
    env = SafetyForgeEnv(task_id=task_id)
    env = Monitor(env) # Track stats

    # Setup PPO Model
    # MlpPolicy is fine for our flattened 11-feature observation
    model = PPO(
        "MlpPolicy", 
        env, 
        verbose=1, 
        learning_rate=3e-4, 
        n_steps=256,
        batch_size=64,
        ent_coef=0.01
    )

    # Train
    callback = SafetyTrainingCallback(verbose=1, save_freq=min(50, episodes//5), on_episode_end=on_episode_end)
    model.learn(total_timesteps=episodes * 10, callback=callback) # Assuming avg 10 steps per episode

    # Save Model
    model_path = "exports/models/safety_ppo_expert"
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    model.save(model_path)
    print(f"✅ Model saved: {model_path}")

    # Export Full Dataset from current session buffer
    # Note: In a real run, you'd pull from a persistent DB.
    # Here we pull from the memory engine of all episodes run in this script.
    # SafetyForgeEnv uses internal env_step which updates _sessions.
    all_episodes = []
    for sess in _sessions.values():
        all_episodes.append({
            "session_id": sess.session_id,
            "history": sess.memory.get_history()
        })
    
    if all_episodes:
        ds_path = exporter.export_episodes(all_episodes)
        print(f"📦 Dataset exported: {ds_path} ({len(all_episodes)} episodes)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SafetyForge Arena Trainer")
    parser.add_argument("--episodes", type=int, default=100, help="Number of training episodes")
    parser.add_argument("--task", type=str, default="expert", help="Task ID to train on")
    args = parser.parse_args()
    
    run_training(episodes=args.episodes, task_id=args.task)
