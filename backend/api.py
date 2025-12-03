"""
API Flask pour Mini-Pacman
Fournit les endpoints pour l'interface Vue.js
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # Backend non-interactif pour serveur
import matplotlib.pyplot as plt
import numpy as np

from environment import MiniPacmanEnv
from agent import QLearningAgent
from training import train_agent, evaluate_agent, run_episode_with_replay

app = Flask(__name__)
CORS(app)  # Permettre les requêtes cross-origin depuis Vue.js

# Variables globales pour stocker l'état
current_env = None
current_agent = None
training_stats = None
training_config = None

# Dossiers de sauvegarde
MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'saved_models')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Vérification de l'état de l'API."""
    return jsonify({
        "status": "ok",
        "message": "API Mini-Pacman opérationnelle"
    })


@app.route('/api/config', methods=['GET'])
def get_config():
    """Retourne la configuration par défaut."""
    default_config = {
        "grid_size": 8,  # Réduit de 10 à 8 pour faciliter apprentissage
        "num_ghosts": 2,  # Réduit de 3 à 2 pour moins de danger
        "ghost_behavior": "random",
        "coins_per_row": 6,  # Réduit de 10 à 6 (48 pièces au lieu de 100)
        "num_lives": 3,
        "enable_powerups": True,
        "num_episodes": 1000,  # Augmenté de 500 à 1000 pour plus d'apprentissage
        "max_steps": 300,  # Réduit de 500 à 300 (suffisant pour 8x8)
        "alpha": 0.5,  # Augmenté de 0.3 à 0.5 pour apprendre vite au début
        "gamma": 0.95,  # Maintenu à 0.95 pour valoriser le long terme
        "epsilon": 1.0,
        "epsilon_min": 0.05,  # Maintenu à 0.05 pour garder exploration
        "epsilon_decay": 0.995  # Accéléré de 0.998 à 0.995 pour converger plus vite
    }
    return jsonify(default_config)


@app.route('/api/train', methods=['POST'])
def train():
    """
    Lance l'entraînement de l'agent avec les paramètres fournis.
    
    Body JSON attendu:
    {
        "grid_size": 10,
        "num_ghosts": 3,
        "ghost_behavior": "random" ou "chase",
        "coins_per_row": 10,
        "num_episodes": 500,
        "max_steps": 200,
        "alpha": 0.1,
        "gamma": 0.9,
        "epsilon": 1.0,
        "epsilon_min": 0.01,
        "epsilon_decay": 0.995
    }
    """
    global current_env, current_agent, training_stats, training_config
    
    try:
        config = request.json
        training_config = config.copy()
        
        # Créer l'environnement
        current_env = MiniPacmanEnv(
            grid_size=config.get('grid_size', 10),
            num_ghosts=config.get('num_ghosts', 3),
            ghost_behavior=config.get('ghost_behavior', 'random'),
            coins_per_row=config.get('coins_per_row', 10),
            num_lives=config.get('num_lives', 3),
            enable_powerups=config.get('enable_powerups', True)
        )
        
        # Créer l'agent
        current_agent = QLearningAgent(
            actions=current_env.ACTIONS,
            alpha=config.get('alpha', 0.1),
            gamma=config.get('gamma', 0.9),
            epsilon=config.get('epsilon', 1.0),
            epsilon_min=config.get('epsilon_min', 0.01),
            epsilon_decay=config.get('epsilon_decay', 0.995)
        )
        
        # Entraîner
        training_stats = train_agent(
            env=current_env,
            agent=current_agent,
            num_episodes=config.get('num_episodes', 500),
            max_steps=config.get('max_steps', 500),
            verbose=False
        )
        
        # Sauvegarder le modèle
        model_path = os.path.join(MODELS_DIR, 'latest_model.json')
        current_agent.save(model_path)
        
        return jsonify({
            "success": True,
            "message": "Entraînement terminé avec succès",
            "stats": {
                "avg_reward": training_stats['avg_reward'],
                "avg_coins": training_stats['avg_coins'],
                "success_rate": training_stats['success_rate'],
                "training_time": training_stats['training_time'],
                "q_table_size": training_stats['q_table_size']
            }
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erreur lors de l'entraînement: {str(e)}"
        }), 500


@app.route('/api/results', methods=['GET'])
def get_results():
    """
    Retourne les résultats de l'entraînement et génère les graphiques.
    """
    global training_stats, training_config
    
    if training_stats is None or training_config is None:
        return jsonify({
            "success": False,
            "message": "Aucun entraînement disponible. Veuillez d'abord entraîner un agent."
        }), 200  # 200 au lieu de 404 pour que le frontend gère mieux
    
    try:
        # Générer les graphiques
        graphs = generate_training_graphs(training_stats)
        
        return jsonify({
            "success": True,
            "config": training_config,
            "stats": training_stats,
            "graphs": graphs
        })
    
    except Exception as e:
        import traceback
        print(f"Erreur dans /api/results: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Erreur lors de la récupération des résultats: {str(e)}"
        }), 500


@app.route('/api/replay', methods=['POST'])
def replay_episode():
    """
    Rejoue un épisode avec l'agent entraîné et retourne l'historique.
    """
    global current_env, current_agent
    
    if current_env is None or current_agent is None:
        return jsonify({
            "success": False,
            "message": "Aucun agent entraîné disponible"
        }), 404
    
    try:
        max_steps = request.json.get('max_steps', 500)
        
        # Exécuter un épisode
        history = run_episode_with_replay(current_env, current_agent, max_steps)
        
        return jsonify({
            "success": True,
            "history": history,
            "episode_length": len(history),
            "final_result": history[-1]['info']
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erreur lors du replay: {str(e)}"
        }), 500


def generate_training_graphs(stats: dict) -> dict:
    """
    Génère les graphiques d'entraînement avec Matplotlib.
    
    Args:
        stats: Statistiques d'entraînement
        
    Returns:
        Dictionnaire contenant les graphiques en base64
    """
    graphs = {}
    
    # 1. Graphique des récompenses
    fig, ax = plt.subplots(figsize=(10, 6))
    rewards = stats['rewards_per_episode']
    episodes = range(1, len(rewards) + 1)
    
    # Courbe brute et moyenne glissante
    ax.plot(episodes, rewards, alpha=0.3, label='Récompense par épisode')
    
    # Moyenne glissante sur 50 épisodes
    window = 50
    if len(rewards) >= window:
        moving_avg = np.convolve(rewards, np.ones(window)/window, mode='valid')
        ax.plot(range(window, len(rewards) + 1), moving_avg, 
                linewidth=2, label=f'Moyenne glissante ({window} épisodes)')
    
    ax.set_xlabel('Épisode')
    ax.set_ylabel('Récompense totale')
    ax.set_title('Évolution de la récompense pendant l\'entraînement')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    graphs['rewards'] = fig_to_base64(fig)
    plt.close(fig)
    
    # 2. Graphique des pièces collectées
    fig, ax = plt.subplots(figsize=(10, 6))
    coins = stats['coins_per_episode']
    
    ax.plot(episodes, coins, alpha=0.3, label='Pièces collectées par épisode')
    
    if len(coins) >= window:
        moving_avg = np.convolve(coins, np.ones(window)/window, mode='valid')
        ax.plot(range(window, len(coins) + 1), moving_avg,
                linewidth=2, label=f'Moyenne glissante ({window} épisodes)')
    
    ax.set_xlabel('Épisode')
    ax.set_ylabel('Nombre de pièces')
    ax.set_title('Nombre de pièces collectées pendant l\'entraînement')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    graphs['coins'] = fig_to_base64(fig)
    plt.close(fig)
    
    # 3. Graphique du taux de succès
    fig, ax = plt.subplots(figsize=(10, 6))
    successes = stats['success_per_episode']
    
    if len(successes) >= window:
        success_rate = np.convolve(successes, np.ones(window)/window, mode='valid') * 100
        ax.plot(range(window, len(successes) + 1), success_rate,
                linewidth=2, label=f'Taux de succès ({window} épisodes)')
    
    ax.set_xlabel('Épisode')
    ax.set_ylabel('Taux de succès (%)')
    ax.set_title('Taux de succès pendant l\'entraînement')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 105)
    
    graphs['success_rate'] = fig_to_base64(fig)
    plt.close(fig)
    
    return graphs


def fig_to_base64(fig) -> str:
    """
    Convertit une figure Matplotlib en string base64.
    
    Args:
        fig: Figure Matplotlib
        
    Returns:
        String base64 de l'image
    """
    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    buffer.close()
    return f"data:image/png;base64,{img_base64}"


if __name__ == '__main__':
    print("=" * 60)
    print("Démarrage de l'API Mini-Pacman")
    print("URL: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
