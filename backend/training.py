"""
Module d'entraînement pour l'agent Mini-Pacman
Inspiré du TP5 (exploration et hyperparamètres)
"""

import time
from typing import Dict, List, Tuple
import numpy as np
from environment import MiniPacmanEnv
from agent import QLearningAgent, RandomAgent


def train_agent(
    env: MiniPacmanEnv,
    agent: QLearningAgent,
    num_episodes: int = 100,
    max_steps: int = 500,
    verbose: bool = True,
    log_interval: int = 50
) -> Dict:
    """
    Entraîne l'agent sur l'environnement Mini-Pacman.
    
    Args:
        env: Environnement Mini-Pacman
        agent: Agent Q-Learning à entraîner
        num_episodes: Nombre d'épisodes d'entraînement
        max_steps: Nombre maximum de pas par épisode
        verbose: Afficher les logs pendant l'entraînement
        log_interval: Intervalle d'affichage des logs (en épisodes)
        
    Returns:
        Dictionnaire contenant les statistiques d'entraînement
    """
    # Métriques à tracker
    rewards_per_episode = []
    coins_per_episode = []
    steps_per_episode = []
    success_per_episode = []  # 1 si victoire (toutes pièces), 0 sinon
    
    start_time = time.time()
    
    for episode in range(1, num_episodes + 1):
        state = env.reset()
        # Utiliser l'état simplifié pour l'agent
        agent_state = env.get_state_for_agent()
        
        total_reward = 0
        done = False
        
        for step in range(max_steps):
            # Choisir une action
            action = agent.choose_action(agent_state, explore=True)
            
            # Exécuter l'action
            next_state, reward, done, info = env.step(action)
            next_agent_state = env.get_state_for_agent()
            
            # Mettre à jour l'agent
            agent.update(agent_state, action, reward, next_agent_state, done)
            
            # Accumuler la récompense
            total_reward += reward
            
            # Passer à l'état suivant
            agent_state = next_agent_state
            
            if done:
                break
        
        # Experience replay pour renforcer l'apprentissage
        if episode % 5 == 0:  # Replay tous les 5 épisodes
            agent.replay_experience(batch_size=32)
        
        # Décrémenter epsilon et alpha après chaque épisode (avec détection régression)
        agent.decay_epsilon(episode_reward=total_reward)
        
        # Enregistrer les métriques
        rewards_per_episode.append(total_reward)
        coins_per_episode.append(info['coins_collected'])
        steps_per_episode.append(step + 1)
        
        # Succès si toutes les pièces sont ramassées
        success = 1 if info.get('reason') == 'all_coins_collected' else 0
        success_per_episode.append(success)
        
        # Logs périodiques
        if verbose and episode % log_interval == 0:
            avg_reward = np.mean(rewards_per_episode[-log_interval:])
            avg_coins = np.mean(coins_per_episode[-log_interval:])
            avg_steps = np.mean(steps_per_episode[-log_interval:])
            success_rate = np.mean(success_per_episode[-log_interval:]) * 100
            
            print(f"Épisode {episode}/{num_episodes} | "
                  f"Récompense moy: {avg_reward:.2f} | "
                  f"Pièces moy: {avg_coins:.1f} | "
                  f"Steps moy: {avg_steps:.1f} | "
                  f"Succès: {success_rate:.1f}% | "
                  f"ε: {agent.epsilon:.3f}")
    
    training_time = time.time() - start_time
    
    # Calculer les statistiques finales
    final_stats = {
        "num_episodes": num_episodes,
        "max_steps": max_steps,
        "training_time": training_time,
        "rewards_per_episode": rewards_per_episode,
        "coins_per_episode": coins_per_episode,
        "steps_per_episode": steps_per_episode,
        "success_per_episode": success_per_episode,
        "avg_reward": float(np.mean(rewards_per_episode)),
        "avg_coins": float(np.mean(coins_per_episode)),
        "avg_steps": float(np.mean(steps_per_episode)),
        "success_rate": float(np.mean(success_per_episode) * 100),
        "final_epsilon": agent.epsilon,
        "q_table_size": len(agent.Q)
    }
    
    if verbose:
        print(f"\n{'='*60}")
        print("Entraînement terminé !")
        print(f"Temps total: {training_time:.2f}s")
        print(f"Récompense moyenne: {final_stats['avg_reward']:.2f}")
        print(f"Pièces moyennes: {final_stats['avg_coins']:.1f}")
        print(f"Taux de succès: {final_stats['success_rate']:.1f}%")
        print(f"Taille Q-table: {final_stats['q_table_size']}")
        print(f"{'='*60}\n")
    
    return final_stats


def evaluate_agent(
    env: MiniPacmanEnv,
    agent: QLearningAgent,
    num_episodes: int = 10,
    max_steps: int = 500,
    verbose: bool = True
) -> Dict:
    """
    Évalue les performances de l'agent (sans exploration).
    
    Args:
        env: Environnement Mini-Pacman
        agent: Agent à évaluer
        num_episodes: Nombre d'épisodes d'évaluation
        max_steps: Nombre maximum de pas par épisode
        verbose: Afficher les résultats
        
    Returns:
        Dictionnaire contenant les statistiques d'évaluation
    """
    rewards = []
    coins_collected = []
    steps_taken = []
    successes = []
    
    for episode in range(num_episodes):
        state = env.reset()
        agent_state = env.get_state_for_agent()
        
        total_reward = 0
        done = False
        
        for step in range(max_steps):
            # Exploitation pure (pas d'exploration)
            action = agent.choose_action(agent_state, explore=False)
            
            next_state, reward, done, info = env.step(action)
            next_agent_state = env.get_state_for_agent()
            
            total_reward += reward
            agent_state = next_agent_state
            
            if done:
                break
        
        rewards.append(total_reward)
        coins_collected.append(info['coins_collected'])
        steps_taken.append(step + 1)
        successes.append(1 if info.get('reason') == 'all_coins_collected' else 0)
    
    eval_stats = {
        "num_episodes": num_episodes,
        "avg_reward": float(np.mean(rewards)),
        "std_reward": float(np.std(rewards)),
        "avg_coins": float(np.mean(coins_collected)),
        "avg_steps": float(np.mean(steps_taken)),
        "success_rate": float(np.mean(successes) * 100)
    }
    
    if verbose:
        print(f"\n{'='*60}")
        print("Résultats de l'évaluation :")
        print(f"Épisodes: {num_episodes}")
        print(f"Récompense moyenne: {eval_stats['avg_reward']:.2f} ± {eval_stats['std_reward']:.2f}")
        print(f"Pièces moyennes: {eval_stats['avg_coins']:.1f}")
        print(f"Steps moyens: {eval_stats['avg_steps']:.1f}")
        print(f"Taux de succès: {eval_stats['success_rate']:.1f}%")
        print(f"{'='*60}\n")
    
    return eval_stats


def run_episode_with_replay(
    env: MiniPacmanEnv,
    agent: QLearningAgent,
    max_steps: int = 500
) -> List[Dict]:
    """
    Exécute un épisode complet et retourne l'historique pour le replay.
    
    Args:
        env: Environnement Mini-Pacman
        agent: Agent à utiliser
        max_steps: Nombre maximum de pas
        
    Returns:
        Liste de dictionnaires contenant l'historique de l'épisode
    """
    history = []
    
    state = env.reset()
    agent_state = env.get_state_for_agent()
    
    # État initial
    history.append({
        "step": 0,
        "pacman_pos": env.pacman_pos,
        "ghosts_pos": env.ghosts_pos.copy(),
        "coins": list(env.coins),
        "powerups": list(env.powerups),
        "walls": list(env.walls),
        "action": None,
        "reward": 0,
        "done": False,
        "info": {"coins_collected": 0, "steps": 0, "lives_remaining": env.lives}
    })
    
    done = False
    for step in range(1, max_steps + 1):
        # Choisir une action (exploitation)
        action = agent.choose_action(agent_state, explore=False)
        
        # Exécuter l'action
        next_state, reward, done, info = env.step(action)
        next_agent_state = env.get_state_for_agent()
        
        # Enregistrer l'état
        history.append({
            "step": step,
            "pacman_pos": env.pacman_pos,
            "ghosts_pos": env.ghosts_pos.copy(),
            "coins": list(env.coins),
            "powerups": list(env.powerups),  # AJOUT des power-ups
            "walls": list(env.walls),
            "action": action,
            "reward": reward,
            "done": done,
            "info": info.copy()
        })
        
        agent_state = next_agent_state
        
        if done:
            break
    
    return history


if __name__ == "__main__":
    # Test du module d'entraînement
    print("=== Test de l'entraînement ===\n")
    
    # Créer l'environnement
    env = MiniPacmanEnv(
        grid_size=10,
        num_ghosts=3,
        ghost_behavior="random",
        coins_per_row=5,
        seed=42
    )
    
    # Créer l'agent
    agent = QLearningAgent(
        actions=env.ACTIONS,
        alpha=0.1,
        gamma=0.9,
        epsilon=1.0,
        epsilon_min=0.01,
        epsilon_decay=0.995
    )
    
    # Entraîner
    stats = train_agent(
        env=env,
        agent=agent,
        num_episodes=100,
        max_steps=100,
        verbose=True,
        log_interval=20
    )
    
    # Évaluer
    eval_stats = evaluate_agent(
        env=env,
        agent=agent,
        num_episodes=20,
        max_steps=100,
        verbose=True
    )
    
    # Test de replay
    print("=== Test de replay ===\n")
    history = run_episode_with_replay(env, agent, max_steps=50)
    print(f"Épisode enregistré: {len(history)} étapes")
    print(f"Résultat final: {history[-1]['info']}")
