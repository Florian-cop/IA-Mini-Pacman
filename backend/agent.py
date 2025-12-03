"""
Agent Q-Learning pour Mini-Pacman
Inspiré du TP4 (Q-Learning dans le labyrinthe)
"""

import random
from typing import Tuple, List, Dict
import json


class QLearningAgent:
    """
    Agent qui apprend à jouer à Mini-Pacman avec l'algorithme Q-Learning.
    
    Q-Learning update rule:
    Q(s,a) = Q(s,a) + α * [r + γ * max_a' Q(s',a') - Q(s,a)]
    
    Politique ε-greedy:
    - Avec probabilité ε: exploration (action aléatoire)
    - Avec probabilité (1-ε): exploitation (meilleure action connue)
    """
    
    def __init__(
        self,
        actions: List[str],
        alpha: float = 0.1,
        gamma: float = 0.9,
        epsilon: float = 0.3,
        epsilon_min: float = 0.01,
        epsilon_decay: float = 0.995
    ):
        """
        Initialise l'agent Q-Learning.
        
        Args:
            actions: Liste des actions possibles
            alpha: Taux d'apprentissage (learning rate) [0, 1]
            gamma: Facteur de discount (importance du futur) [0, 1]
            epsilon: Probabilité d'exploration initiale [0, 1]
            epsilon_min: Valeur minimale d'epsilon
            epsilon_decay: Facteur de décroissance d'epsilon par épisode
        """
        self.actions = actions
        self.alpha = alpha
        self.alpha_initial = alpha  # Sauvegarder alpha initial
        self.alpha_min = 0.05  # Augmenté de 0.01 à 0.05 pour maintenir apprentissage
        self.alpha_decay = 0.9998  # Ralenti de 0.9995 à 0.9998 (décroissance ultra-lente)
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = max(epsilon_min, 0.05)  # Minimum 5% exploration pour éviter blocage
        self.epsilon_decay = epsilon_decay
        
        # Q-table: dictionnaire {(state, action): valeur}
        self.Q = {}
        
        # Experience replay simple (garde les N dernières transitions)
        self.experience_buffer = []
        self.buffer_size = 10000
        
        # Statistiques
        self.episodes_trained = 0
        self.recent_rewards = []  # Buffer des 50 dernières récompenses moyennes
        self.best_avg_reward = float('-inf')  # Meilleure performance moyenne
    
    def get_Q(self, state: Tuple, action: str) -> float:
        """
        Retourne la valeur Q(s,a).
        Si l'état-action n'a jamais été vu, retourne 0.
        
        Args:
            state: État du jeu
            action: Action à évaluer
            
        Returns:
            Valeur Q(s,a)
        """
        return self.Q.get((state, action), 0.0)
    
    def store_experience(self, state: Tuple, action: str, reward: float, next_state: Tuple, done: bool):
        """
        Stocke une expérience dans le buffer pour replay.
        
        Args:
            state: État avant l'action
            action: Action effectuée
            reward: Récompense reçue
            next_state: État après l'action
            done: Si True, l'épisode est terminé
        """
        self.experience_buffer.append((state, action, reward, next_state, done))
        
        # Limiter la taille du buffer
        if len(self.experience_buffer) > self.buffer_size:
            self.experience_buffer.pop(0)
    
    def choose_action(self, state: Tuple, explore: bool = True) -> str:
        """
        Choisit une action selon la politique ε-greedy.
        
        Args:
            state: État actuel du jeu
            explore: Si True, utilise ε-greedy; si False, toujours exploite (pour évaluation)
            
        Returns:
            Action choisie
        """
        if explore and random.random() < self.epsilon:
            # Exploration: action aléatoire
            return random.choice(self.actions)
        else:
            # Exploitation: meilleure action connue
            q_values = [self.get_Q(state, a) for a in self.actions]
            max_q = max(q_values)
            
            # Si plusieurs actions ont la même valeur Q, choisir aléatoirement parmi elles
            best_actions = [
                self.actions[i] 
                for i, q in enumerate(q_values) 
                if q == max_q
            ]
            return random.choice(best_actions)
    
    def update(self, state: Tuple, action: str, reward: float, next_state: Tuple, done: bool):
        """
        Met à jour la Q-table avec la formule du Q-Learning.
        
        Q(s,a) = Q(s,a) + α * [r + γ * max_a' Q(s',a') - Q(s,a)]
        
        Args:
            state: État avant l'action
            action: Action effectuée
            reward: Récompense reçue
            next_state: État après l'action
            done: Si True, l'épisode est terminé
        """
        # Stocker l'expérience
        self.store_experience(state, action, reward, next_state, done)
        
        old_q = self.get_Q(state, action)
        
        if done:
            # Si l'épisode est terminé, pas de futur
            future_q = 0.0
        else:
            # Meilleure valeur Q possible depuis le prochain état
            future_q = max([self.get_Q(next_state, a) for a in self.actions])
        
        # Formule du Q-Learning avec alpha décroissant
        td_error = reward + self.gamma * future_q - old_q
        new_q = old_q + self.alpha * td_error
        
        # Mise à jour de la Q-table
        self.Q[(state, action)] = new_q
    
    def decay_epsilon(self, episode_reward: float = None):
        """
        Réduit epsilon et alpha pour diminuer l'exploration et stabiliser l'apprentissage.
        Avec mécanisme anti-régression : si performances baissent, augmente epsilon.
        
        Args:
            episode_reward: Récompense totale de l'épisode (pour détecter régression)
        """
        # Tracker les performances récentes
        if episode_reward is not None:
            self.recent_rewards.append(episode_reward)
            if len(self.recent_rewards) > 50:
                self.recent_rewards.pop(0)
        
        # Détecter régression : si performances baissent significativement
        if len(self.recent_rewards) >= 50:
            current_avg = sum(self.recent_rewards[-25:]) / 25  # Moyenne des 25 derniers
            previous_avg = sum(self.recent_rewards[-50:-25]) / 25  # Moyenne des 25 d'avant
            
            # Si baisse > 15%, augmenter epsilon pour réexplorer
            if current_avg < previous_avg * 0.85:
                self.epsilon = min(self.epsilon * 1.2, 0.3)  # Boost epsilon jusqu'à 30%
                # print(f"Régression détectée ! Epsilon augmenté à {self.epsilon:.3f}")
            else:
                # Mettre à jour la meilleure performance
                self.best_avg_reward = max(self.best_avg_reward, current_avg)
        
        # Decay epsilon (exploration) - normal
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        
        # Decay alpha (taux d'apprentissage) - ultra-lent
        self.alpha = max(self.alpha_min, self.alpha * self.alpha_decay)
        
        self.episodes_trained += 1
    
    def replay_experience(self, batch_size: int = 32):
        """
        Rejoue des expériences aléatoires du buffer pour renforcer l'apprentissage.
        Priorise les expériences avec récompenses importantes (positives ou négatives).
        
        Args:
            batch_size: Nombre d'expériences à rejouer
        """
        if len(self.experience_buffer) < batch_size:
            return
        
        # Priorisation : donner plus de poids aux expériences importantes
        # (grandes récompenses positives ou négatives)
        experiences_with_priority = []
        for exp in self.experience_buffer:
            state, action, reward, next_state, done = exp
            # Priorité basée sur la magnitude de la récompense
            priority = abs(reward) + 0.1  # +0.1 pour éviter priorité nulle
            experiences_with_priority.append((exp, priority))
        
        # Normaliser les priorités
        total_priority = sum(p for _, p in experiences_with_priority)
        probabilities = [p / total_priority for _, p in experiences_with_priority]
        
        # Échantillonner selon les probabilités (avec remplacement)
        indices = random.choices(range(len(experiences_with_priority)), 
                                weights=probabilities, k=batch_size)
        batch = [experiences_with_priority[i][0] for i in indices]
        
        for state, action, reward, next_state, done in batch:
            old_q = self.get_Q(state, action)
            
            if done:
                future_q = 0.0
            else:
                future_q = max([self.get_Q(next_state, a) for a in self.actions])
            
            # Alpha adaptatif : plus conservateur en fin d'apprentissage
            # mais pas trop faible pour corriger les erreurs
            replay_alpha = max(self.alpha * 0.7, 0.02)  # Minimum 0.02
            td_error = reward + self.gamma * future_q - old_q
            new_q = old_q + replay_alpha * td_error
            
            self.Q[(state, action)] = new_q
    
    def save(self, filepath: str):
        """
        Sauvegarde la Q-table et les paramètres de l'agent.
        
        Args:
            filepath: Chemin du fichier JSON de sauvegarde
        """
        data = {
            "actions": self.actions,
            "alpha": self.alpha,
            "alpha_initial": self.alpha_initial,
            "alpha_min": self.alpha_min,
            "alpha_decay": self.alpha_decay,
            "gamma": self.gamma,
            "epsilon": self.epsilon,
            "epsilon_min": self.epsilon_min,
            "epsilon_decay": self.epsilon_decay,
            "episodes_trained": self.episodes_trained,
            "recent_rewards": self.recent_rewards,
            "best_avg_reward": self.best_avg_reward,
            "Q": {str(k): v for k, v in self.Q.items()}  # Convertir les tuples en strings
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, filepath: str):
        """
        Charge la Q-table et les paramètres depuis un fichier.
        
        Args:
            filepath: Chemin du fichier JSON de sauvegarde
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.actions = data["actions"]
        self.alpha = data["alpha"]
        self.alpha_initial = data.get("alpha_initial", self.alpha)
        self.alpha_min = data.get("alpha_min", 0.05)  # Nouvelle valeur par défaut
        self.alpha_decay = data.get("alpha_decay", 0.9998)  # Nouvelle valeur par défaut
        self.gamma = data["gamma"]
        self.epsilon = data["epsilon"]
        self.epsilon_min = max(data.get("epsilon_min", 0.01), 0.05)  # Minimum 5%
        self.epsilon_decay = data["epsilon_decay"]
        self.episodes_trained = data["episodes_trained"]
        self.recent_rewards = data.get("recent_rewards", [])
        self.best_avg_reward = data.get("best_avg_reward", float('-inf'))
        
        # Reconvertir les strings en tuples pour les clés
        self.Q = {}
        for k_str, v in data["Q"].items():
            # Format: "((x, y, ...), 'action')"
            k = eval(k_str)  # Attention: eval est dangereux en production
            self.Q[k] = v
    
    def get_policy(self, states: List[Tuple]) -> Dict[Tuple, str]:
        """
        Retourne la politique (meilleure action) pour une liste d'états.
        
        Args:
            states: Liste d'états
            
        Returns:
            Dictionnaire {état: meilleure_action}
        """
        policy = {}
        for state in states:
            q_values = [self.get_Q(state, a) for a in self.actions]
            best_action_idx = q_values.index(max(q_values))
            policy[state] = self.actions[best_action_idx]
        return policy
    
    def get_stats(self) -> Dict:
        """
        Retourne des statistiques sur l'agent.
        
        Returns:
            Dictionnaire de statistiques
        """
        return {
            "q_table_size": len(self.Q),
            "episodes_trained": self.episodes_trained,
            "epsilon": self.epsilon,
            "alpha": self.alpha,
            "gamma": self.gamma
        }


class RandomAgent:
    """
    Agent de base qui choisit des actions aléatoires.
    Utile pour comparer les performances.
    """
    
    def __init__(self, actions: List[str]):
        self.actions = actions
    
    def choose_action(self, state: Tuple, explore: bool = True) -> str:
        """
        Choisit une action aléatoire.
        
        Args:
            state: État actuel (non utilisé)
            explore: Non utilisé (pour compatibilité avec QLearningAgent)
            
        Returns:
            Action aléatoire
        """
        return random.choice(self.actions)
    
    def update(self, state: Tuple, action: str, reward: float, next_state: Tuple, done: bool):
        """
        Ne fait rien (l'agent aléatoire n'apprend pas).
        """
        pass
    
    def decay_epsilon(self):
        """
        Ne fait rien (pas d'epsilon pour l'agent aléatoire).
        """
        pass


if __name__ == "__main__":
    # Test de l'agent Q-Learning
    print("=== Test de l'agent Q-Learning ===\n")
    
    actions = ["up", "down", "left", "right"]
    agent = QLearningAgent(actions, alpha=0.1, gamma=0.9, epsilon=0.3)
    
    # État fictif pour le test
    state = (5, 5, 0, 1, 2)  # (px, py, rel_x, rel_y, coins_bucket)
    
    print(f"État initial: {state}")
    print(f"Epsilon: {agent.epsilon}")
    
    # Choisir quelques actions
    for i in range(5):
        action = agent.choose_action(state)
        print(f"Action {i+1}: {action}")
    
    # Simuler une mise à jour
    next_state = (5, 4, 0, 1, 2)
    reward = 5.0
    agent.update(state, "up", reward, next_state, done=False)
    
    print(f"\nAprès update, Q({state}, 'up') = {agent.get_Q(state, 'up'):.2f}")
    
    # Statistiques
    print(f"\nStatistiques: {agent.get_stats()}")
