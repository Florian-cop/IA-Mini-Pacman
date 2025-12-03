"""
Environnement Mini-Pacman pour apprentissage par renforcement
Inspiré du TP3 (Labyrinthe) et TP6 (Coin Collector)
"""

import random
from typing import Tuple, List, Dict, Set


class MiniPacmanEnv:
    """
    Environnement Mini-Pacman sur grille.
    
    Caractéristiques:
    - Grille carrée (par défaut 10x10)
    - Pacman se déplace et ramasse des pièces
    - Fantômes se déplacent (aléatoire ou poursuite)
    - Épisode termine si: attrapé par fantôme, toutes pièces ramassées, ou max_steps atteint
    
    Récompenses:
    - +5 : ramasse une pièce
    - +20 : ramasse toutes les pièces (victoire)
    - -20 : attrapé par un fantôme (défaite)
    - -0.1 : coût de déplacement (encourage efficacité)
    """
    
    ACTIONS = ["up", "down", "left", "right"]
    
    def __init__(
        self, 
        grid_size: int = 10,
        num_ghosts: int = 3,
        ghost_behavior: str = "random",  # "random" ou "chase"
        coins_per_row: int = 10,
        num_lives: int = 3,
        enable_powerups: bool = True,
        seed: int = None
    ):
        """
        Initialise l'environnement.
        
        Args:
            grid_size: Taille de la grille (NxN)
            num_ghosts: Nombre de fantômes (1-5)
            ghost_behavior: "random" ou "chase" (poursuite)
            coins_per_row: Nombre de pièces par ligne (total = coins_per_row * grid_size)
            num_lives: Nombre de vies de Pacman (1-10)
            enable_powerups: Activer les power-ups (True/False)
            seed: Graine pour reproductibilité
        """
        self.grid_size = grid_size
        self.num_ghosts = max(1, min(5, num_ghosts))  # Entre 1 et 5
        self.ghost_behavior = ghost_behavior
        self.coins_per_row = coins_per_row
        self.num_lives = max(1, min(10, num_lives))  # Entre 1 et 10
        self.enable_powerups = enable_powerups
        
        if seed is not None:
            random.seed(seed)
        
        # Initialisation des positions
        self.pacman_pos = None
        self.pacman_start_pos = None  # Position de départ de Pacman
        self.ghosts_pos = []
        self.ghosts_start_pos = []  # Positions de départ des fantômes
        self.coins = set()
        self.initial_coins_count = 0
        self.walls = set()
        self.powerups = set()  # Positions des power-ups
        self.initial_powerups_count = 0
        
        # Stats de l'épisode
        self.coins_collected = 0
        self.steps = 0
        self.lives = self.num_lives
        self.lives_lost = 0
        self.visited_positions = {}  # {position: nombre_de_visites}
        self.powerups_collected = 0
        self.invincible_timer = 0  # Nombre de pas restants en mode invincible
        self.ghosts_eaten = 0  # Nombre de fantômes mangés durant l'épisode
        self.last_action = None  # Dernière action effectuée
        self.action_history = []  # Historique des 4 dernières actions pour détecter les boucles
        
        # Définir les murs de manière prédéfinie
        self._create_walls()
        
        self.reset()
    
    def _create_walls(self):
        """
        Génère des murs procéduralement pour créer un labyrinthe.
        Utilise un algorithme de division récursive pour créer des chambres et couloirs.
        """
        self.walls = set()
        
        # Calculer le nombre de murs en fonction de la taille de la grille
        # Environ 10-15% des cases seront des murs
        wall_density = 0.12
        max_walls = int(self.grid_size * self.grid_size * wall_density)
        
        # Créer des "chambres" avec des murs en forme de croix
        self._create_room_walls()
        
        # Ajouter des obstacles aléatoires supplémentaires
        self._add_random_obstacles(max_walls)
        
        # S'assurer qu'il y a toujours un chemin (enlever des murs si nécessaire)
        self._ensure_connectivity()
    
    def _create_room_walls(self):
        """
        Crée des murs en divisant la grille en chambres.
        """
        # Division horizontale et verticale
        mid_x = self.grid_size // 2
        mid_y = self.grid_size // 2
        
        # Mur vertical au milieu (avec ouvertures)
        gap_y = random.randint(1, self.grid_size - 2)
        for y in range(1, self.grid_size - 1):
            if y != gap_y and y != gap_y + 1:  # Deux ouvertures pour plus de fluidité
                self.walls.add((mid_x, y))
        
        # Mur horizontal au milieu (avec ouvertures)
        gap_x = random.randint(1, self.grid_size - 2)
        for x in range(1, self.grid_size - 1):
            if x != gap_x and x != gap_x + 1:
                self.walls.add((x, mid_y))
        
        # Créer des sous-divisions dans les quadrants
        if self.grid_size >= 10:
            self._create_quadrant_walls(0, mid_x, 0, mid_y)  # Haut-gauche
            self._create_quadrant_walls(mid_x + 1, self.grid_size, 0, mid_y)  # Haut-droite
            self._create_quadrant_walls(0, mid_x, mid_y + 1, self.grid_size)  # Bas-gauche
            self._create_quadrant_walls(mid_x + 1, self.grid_size, mid_y + 1, self.grid_size)  # Bas-droite
    
    def _create_quadrant_walls(self, x_start, x_end, y_start, y_end):
        """
        Crée des petits murs dans un quadrant.
        """
        width = x_end - x_start
        height = y_end - y_start
        
        # Besoin d'au moins 5x5 pour créer des murs intéressants
        if width < 5 or height < 5:
            return
        
        # Ajouter quelques petits murs aléatoires
        num_small_walls = random.randint(1, 2)
        for _ in range(num_small_walls):
            # Mur de 2-3 cases (en fonction de l'espace disponible)
            max_length = min(3, width - 3, height - 3)
            if max_length < 2:
                continue
            
            length = random.randint(2, max_length)
            orientation = random.choice(['horizontal', 'vertical'])
            
            if orientation == 'horizontal':
                # Vérifier qu'il y a assez d'espace
                max_x = x_end - length - 1
                min_x = x_start + 1
                max_y = y_end - 2
                min_y = y_start + 1
                
                if max_x >= min_x and max_y >= min_y:
                    x = random.randint(min_x, max_x)
                    y = random.randint(min_y, max_y)
                    for i in range(length):
                        self.walls.add((x + i, y))
            else:
                # Vérifier qu'il y a assez d'espace
                max_x = x_end - 2
                min_x = x_start + 1
                max_y = y_end - length - 1
                min_y = y_start + 1
                
                if max_x >= min_x and max_y >= min_y:
                    x = random.randint(min_x, max_x)
                    y = random.randint(min_y, max_y)
                    for i in range(length):
                        self.walls.add((x, y + i))
    
    def _add_random_obstacles(self, max_walls):
        """
        Ajoute des obstacles aléatoires pour atteindre la densité souhaitée.
        """
        attempts = 0
        max_attempts = max_walls * 3
        
        while len(self.walls) < max_walls and attempts < max_attempts:
            x = random.randint(1, self.grid_size - 2)
            y = random.randint(1, self.grid_size - 2)
            pos = (x, y)
            
            # Ne pas mettre de mur sur les bords pour laisser de l'espace
            if pos not in self.walls:
                # Éviter de créer des blocs 2x2 complets
                adjacent_walls = sum([
                    (x+1, y) in self.walls,
                    (x-1, y) in self.walls,
                    (x, y+1) in self.walls,
                    (x, y-1) in self.walls
                ])
                
                if adjacent_walls < 3:  # Maximum 2 murs adjacents
                    self.walls.add(pos)
            
            attempts += 1
    
    def _ensure_connectivity(self):
        """
        S'assure qu'il existe au moins un chemin entre les coins de la grille.
        Utilise un BFS simple pour vérifier la connectivité.
        """
        start = (0, 0)
        end = (self.grid_size - 1, self.grid_size - 1)
        
        # Si pas de chemin, enlever quelques murs aléatoires
        max_removals = 5
        removals = 0
        
        while not self._has_path(start, end) and removals < max_removals and self.walls:
            # Enlever un mur aléatoire
            wall_to_remove = random.choice(list(self.walls))
            self.walls.remove(wall_to_remove)
            removals += 1
    
    def _has_path(self, start, end):
        """
        Vérifie s'il existe un chemin entre deux positions (BFS).
        """
        if start in self.walls or end in self.walls:
            return False
        
        visited = set()
        queue = [start]
        visited.add(start)
        
        while queue:
            x, y = queue.pop(0)
            
            if (x, y) == end:
                return True
            
            # Explorer les voisins
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (0 <= nx < self.grid_size and 
                    0 <= ny < self.grid_size and 
                    (nx, ny) not in visited and 
                    (nx, ny) not in self.walls):
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        
        return False
    
    def reset(self) -> Tuple[Tuple[int, int], List[Tuple[int, int]], int]:
        """
        Réinitialise l'environnement pour un nouvel épisode.
        
        Returns:
            Tuple contenant (pacman_pos, ghosts_pos, coins_remaining)
        """
        # Position de départ de Pacman (coin inférieur gauche)
        self.pacman_pos = (0, self.grid_size - 1)
        self.pacman_start_pos = self.pacman_pos  # Sauvegarder la position de départ
        
        # Placement des fantômes (aléatoire, pas sur Pacman ou murs)
        self.ghosts_pos = []
        for _ in range(self.num_ghosts):
            while True:
                ghost_pos = (
                    random.randint(0, self.grid_size - 1),
                    random.randint(0, self.grid_size - 1)
                )
                # Éviter Pacman, autres fantômes et murs
                if (ghost_pos != self.pacman_pos and 
                    ghost_pos not in self.ghosts_pos and 
                    ghost_pos not in self.walls):
                    # Éviter de spawner trop près de Pacman
                    distance = abs(ghost_pos[0] - self.pacman_pos[0]) + abs(ghost_pos[1] - self.pacman_pos[1])
                    if distance >= 3:
                        self.ghosts_pos.append(ghost_pos)
                        break
        
        # Sauvegarder les positions de départ des fantômes
        self.ghosts_start_pos = self.ghosts_pos.copy()
        
        # Placement des pièces (une par case sauf Pacman, fantômes et murs)
        self.coins = set()
        
        all_positions = [
            (x, y) 
            for x in range(self.grid_size) 
            for y in range(self.grid_size)
        ]
        
        # Retirer Pacman, fantômes et murs des positions disponibles
        available_positions = [
            pos for pos in all_positions 
            if pos != self.pacman_pos and pos not in self.ghosts_pos and pos not in self.walls
        ]
        
        # Réserver des emplacements pour les power-ups (2-3)
        num_powerups_to_reserve = random.randint(2, 3) if self.enable_powerups else 0
        num_positions_for_powerups = min(num_powerups_to_reserve, len(available_positions))
        
        # Calculer le nombre de pièces en fonction de l'espace disponible APRÈS réservation
        max_possible_coins = len(available_positions) - num_positions_for_powerups
        desired_coins = self.coins_per_row * self.grid_size
        total_coins = min(desired_coins, max_possible_coins)
        
        # Sélectionner aléatoirement les positions des pièces
        if total_coins > 0 and len(available_positions) > 0:
            coin_positions = random.sample(available_positions, total_coins)
            self.coins = set(coin_positions)
            
            # Retirer les positions des pièces pour les power-ups
            available_positions = [pos for pos in available_positions if pos not in self.coins]
        else:
            self.coins = set()
        
        self.initial_coins_count = len(self.coins)
        
        # Placement des power-ups (2-3 maximum pour l'équilibre)
        # Limité à 2-3 power-ups quelque soit la taille de la grille
        self.powerups = set()
        
        if self.enable_powerups:
            num_powerups = min(random.randint(2, 3), len(available_positions))
            
            if num_powerups > 0 and len(available_positions) > 0:
                # Placer les power-ups stratégiquement (loin de Pacman, dans des zones intéressantes)
                # Trier par distance à Pacman (placer loin)
                available_positions.sort(key=lambda pos: abs(pos[0] - self.pacman_pos[0]) + abs(pos[1] - self.pacman_pos[1]), reverse=True)
                
                # Prendre les positions les plus éloignées
                powerup_positions = available_positions[:num_powerups]
                self.powerups = set(powerup_positions)
        
        self.initial_powerups_count = len(self.powerups)
        
        # Reset stats
        self.coins_collected = 0
        self.steps = 0
        self.lives = self.num_lives
        self.lives_lost = 0
        self.visited_positions = {}
        self.powerups_collected = 0
        self.invincible_timer = 0
        self.ghosts_eaten = 0
        self.last_action = None
        self.action_history = []
        self._last_min_coin_dist = float('inf')  # Pour calcul de progression
        
        # Reset milestones de progression
        if hasattr(self, '_milestone_25'):
            del self._milestone_25
        if hasattr(self, '_milestone_50'):
            del self._milestone_50
        if hasattr(self, '_milestone_75'):
            del self._milestone_75
        self._last_min_coin_dist = float('inf')  # Pour calcul de progression
        
        # Reset milestones de progression
        if hasattr(self, '_milestone_25'):
            del self._milestone_25
        if hasattr(self, '_milestone_50'):
            del self._milestone_50
        if hasattr(self, '_milestone_75'):
            del self._milestone_75
        
        return self._get_state()
    
    def _get_state(self) -> Tuple[Tuple[int, int], List[Tuple[int, int]], int]:
        """
        Retourne l'état actuel.
        
        Returns:
            Tuple (pacman_pos, ghosts_pos, coins_remaining)
        """
        return (self.pacman_pos, self.ghosts_pos.copy(), len(self.coins))
    
    def _get_closest_ghost_direction(self) -> str:
        """
        Retourne la direction du fantôme le plus proche.
        
        Returns:
            Direction: "up", "down", "left", "right", ou "none"
        """
        if not self.ghosts_pos:
            return "none"
        
        px, py = self.pacman_pos
        
        # Trouver le fantôme le plus proche (distance Manhattan)
        closest_ghost = min(self.ghosts_pos, 
                           key=lambda g: abs(g[0] - px) + abs(g[1] - py))
        
        gx, gy = closest_ghost
        
        # Déterminer la direction principale
        dx = gx - px
        dy = gy - py
        
        # Prioriser la plus grande différence
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        elif abs(dy) > abs(dx):
            return "down" if dy > 0 else "up"
        else:
            # Si égal, choisir horizontal
            return "right" if dx > 0 else "left" if dx < 0 else "none"
    
    def _get_closest_coin_direction(self) -> str:
        """
        Retourne la direction de la pièce la plus proche.
        
        Returns:
            Direction: "up", "down", "left", "right", ou "none"
        """
        if not self.coins:
            return "none"
        
        px, py = self.pacman_pos
        
        # Trouver la pièce la plus proche (distance Manhattan)
        closest_coin = min(self.coins, 
                          key=lambda c: abs(c[0] - px) + abs(c[1] - py))
        
        cx, cy = closest_coin
        
        # Déterminer la direction principale
        dx = cx - px
        dy = cy - py
        
        # Prioriser la plus grande différence
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        elif abs(dy) > abs(dx):
            return "down" if dy > 0 else "up"
        else:
            # Si égal, choisir horizontal
            return "right" if dx > 0 else "left" if dx < 0 else "none"
    
    def _get_closest_powerup_direction(self) -> str:
        """
        Retourne la direction du power-up le plus proche.
        
        Returns:
            Direction: "up", "down", "left", "right", ou "none"
        """
        if not self.powerups:
            return "none"
        
        px, py = self.pacman_pos
        
        # Trouver le power-up le plus proche (distance Manhattan)
        closest_powerup = min(self.powerups, 
                             key=lambda p: abs(p[0] - px) + abs(p[1] - py))
        
        ppx, ppy = closest_powerup
        
        # Déterminer la direction principale
        dx = ppx - px
        dy = ppy - py
        
        # Prioriser la plus grande différence
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        elif abs(dy) > abs(dx):
            return "down" if dy > 0 else "up"
        else:
            # Si égal, choisir horizontal
            return "right" if dx > 0 else "left" if dx < 0 else "none"
    
    def _move_position(self, pos: Tuple[int, int], action: str) -> Tuple[Tuple[int, int], bool, bool]:
        """
        Calcule la nouvelle position après une action.
        
        Args:
            pos: Position actuelle (x, y)
            action: Action à effectuer
            
        Returns:
            Tuple (nouvelle_position, hit_wall, out_of_bounds)
            - nouvelle_position: nouvelle position (x, y)
            - hit_wall: True si l'action a tenté de traverser un mur
            - out_of_bounds: True si l'action a tenté de sortir de la grille
        """
        x, y = pos
        
        if action == "up":
            y -= 1
        elif action == "down":
            y += 1
        elif action == "left":
            x -= 1
        elif action == "right":
            x += 1
        
        # Vérifier si hors limites
        out_of_bounds = (x < 0 or x >= self.grid_size or y < 0 or y >= self.grid_size)
        
        # Contraindre dans la grille
        x = max(0, min(self.grid_size - 1, x))
        y = max(0, min(self.grid_size - 1, y))
        
        # Vérifier les murs
        new_pos = (x, y)
        hit_wall = new_pos in self.walls
        
        if hit_wall or out_of_bounds:
            return pos, hit_wall, out_of_bounds  # Reste sur place
        
        return new_pos, False, False
    
    def _move_ghosts(self):
        """
        Déplace tous les fantômes selon leur comportement.
        """
        new_ghosts_pos = []
        
        for ghost_pos in self.ghosts_pos:
            if self.ghost_behavior == "chase":
                new_pos = self._move_ghost_chase(ghost_pos)
            else:  # random
                new_pos = self._move_ghost_random(ghost_pos)
            
            new_ghosts_pos.append(new_pos)
        
        self.ghosts_pos = new_ghosts_pos
    
    def _move_ghost_random(self, ghost_pos: Tuple[int, int]) -> Tuple[int, int]:
        """
        Déplace un fantôme aléatoirement.
        
        Args:
            ghost_pos: Position actuelle du fantôme
            
        Returns:
            Nouvelle position du fantôme
        """
        action = random.choice(self.ACTIONS)
        new_pos, _, _ = self._move_position(ghost_pos, action)
        return new_pos
    
    def _move_ghost_chase(self, ghost_pos: Tuple[int, int]) -> Tuple[int, int]:
        """
        Déplace un fantôme en essayant de se rapprocher de Pacman.
        Règle simple: se rapprocher si même ligne ou colonne.
        
        Args:
            ghost_pos: Position actuelle du fantôme
            
        Returns:
            Nouvelle position du fantôme
        """
        gx, gy = ghost_pos
        px, py = self.pacman_pos
        
        # Si même ligne ou colonne, se rapprocher
        if gx == px:
            # Même colonne, bouger verticalement
            if gy < py:
                new_pos, _, _ = self._move_position(ghost_pos, "down")
                return new_pos
            elif gy > py:
                new_pos, _, _ = self._move_position(ghost_pos, "up")
                return new_pos
        elif gy == py:
            # Même ligne, bouger horizontalement
            if gx < px:
                new_pos, _, _ = self._move_position(ghost_pos, "right")
                return new_pos
            elif gx > px:
                new_pos, _, _ = self._move_position(ghost_pos, "left")
                return new_pos
        
        # Sinon, déplacement aléatoire
        return self._move_ghost_random(ghost_pos)
    
    def step(self, action: str) -> Tuple[Tuple, float, bool, Dict]:
        """
        Exécute une action et retourne le résultat.
        
        Args:
            action: Action à effectuer ("up", "down", "left", "right")
            
        Returns:
            Tuple (state, reward, done, info)
        """
        assert action in self.ACTIONS, f"Action invalide: {action}"
        
        self.steps += 1
        
        # Ajouter l'action à l'historique (garder seulement les 4 dernières)
        self.action_history.append(action)
        if len(self.action_history) > 4:
            self.action_history.pop(0)
        
        # 1. Déplacer Pacman
        self.pacman_pos, hit_wall, out_of_bounds = self._move_position(self.pacman_pos, action)
        
        # 2. Tracker les positions visitées
        if self.pacman_pos in self.visited_positions:
            self.visited_positions[self.pacman_pos] += 1
        else:
            self.visited_positions[self.pacman_pos] = 1
        
        # 3. Vérifier si Pacman ramasse une pièce ou un power-up
        reward = 0.0  # Pas de coût de déplacement par défaut
        
        # Pénalité LÉGÈRE pour déplacement invalide (mur ou hors grille)
        if hit_wall or out_of_bounds:
            reward -= 0.5  # Réduit de -2.0 à -0.5
        
        # Gestion des revisites : bonus exploration vs pénalité
        visits = self.visited_positions[self.pacman_pos]
        if visits == 1:
            # BONUS significatif pour visiter une nouvelle case
            reward += 1.0  # Augmenté de 0.5 à 1.0
        elif visits > 1:
            # Pénalité légère et progressive
            revisit_penalty = -0.2 * visits  # Linéaire et plus doux
            reward += revisit_penalty
        
        # Détection de boucles (multiples patterns) - PÉNALITÉS RÉDUITES
        if len(self.action_history) >= 4:
            # Pattern 1: Haut-Bas-Haut-Bas (ou Gauche-Droite-Gauche-Droite)
            if (self.action_history[-1] == self.action_history[-3] and 
                self.action_history[-2] == self.action_history[-4]):
                # Vérifier si c'est une vraie boucle (opposés)
                opposites = [('up', 'down'), ('down', 'up'), ('left', 'right'), ('right', 'left')]
                if (self.action_history[-1], self.action_history[-2]) in opposites:
                    reward -= 1.0  # Réduit de -3.0 à -1.0
            
            # Pattern 2: Même action répétée puis retour (ex: Haut-Haut-Bas-Bas)
            if (self.action_history[-1] == self.action_history[-2] and
                self.action_history[-3] == self.action_history[-4]):
                opposites = [('up', 'down'), ('down', 'up'), ('left', 'right'), ('right', 'left')]
                if (self.action_history[-1], self.action_history[-3]) in opposites:
                    reward -= 0.5  # Réduit de -2.0 à -0.5
        
        # Détecter si Pacman reste dans une petite zone (3x3) trop longtemps
        if len(self.visited_positions) >= 10:
            # Calculer la zone couverte (min/max des positions visitées récemment)
            recent_positions = list(self.visited_positions.keys())[-10:]
            xs = [p[0] for p in recent_positions]
            ys = [p[1] for p in recent_positions]
            zone_width = max(xs) - min(xs) + 1
            zone_height = max(ys) - min(ys) + 1
            
            # Si la zone est petite (3x3 ou moins), pénaliser légèrement
            if zone_width <= 3 and zone_height <= 3:
                reward -= 0.3  # Réduit de -1.5 à -0.3
        
        # NOUVEAU : Récompense pour se rapprocher d'une pièce
        if len(self.coins) > 0:
            # Calculer distance à la pièce la plus proche
            px, py = self.pacman_pos
            min_coin_dist = min([abs(c[0] - px) + abs(c[1] - py) for c in self.coins])
            
            # Petit bonus si on se rapproche (basé sur l'action précédente)
            if hasattr(self, '_last_min_coin_dist'):
                if min_coin_dist < self._last_min_coin_dist:
                    reward += 0.1  # Bonus pour se rapprocher
            self._last_min_coin_dist = min_coin_dist
        
        # Collecter pièce normale - RÉCOMPENSE PROGRESSIVE
        if self.pacman_pos in self.coins:
            self.coins.remove(self.pacman_pos)
            self.coins_collected += 1
            
            # Récompense qui augmente avec la progression (encourage à finir)
            base_reward = 10.0
            if self.initial_coins_count > 0:
                progress = self.coins_collected / self.initial_coins_count
                progress_bonus = 5.0 * progress  # Jusqu'à +5 bonus
                reward += base_reward + progress_bonus
            else:
                reward += base_reward
            
            self._last_min_coin_dist = float('inf')  # Reset distance
        
        # Collecter power-up (FORTE RÉCOMPENSE pour inciter l'agent)
        if self.pacman_pos in self.powerups:
            self.powerups.remove(self.pacman_pos)
            self.powerups_collected += 1
            self.invincible_timer = 10  # Invincible pendant 10 pas
            reward += 20.0  # Augmenté de 15.0 à 20.0
        
        # BONUS DE PROGRESSION (milestones)
        if self.initial_coins_count > 0:
            progress_pct = (self.coins_collected / self.initial_coins_count) * 100
            # 25%, 50%, 75% : bonus progressifs
            if progress_pct >= 25 and not hasattr(self, '_milestone_25'):
                reward += 15.0
                self._milestone_25 = True
            if progress_pct >= 50 and not hasattr(self, '_milestone_50'):
                reward += 25.0
                self._milestone_50 = True
            if progress_pct >= 75 and not hasattr(self, '_milestone_75'):
                reward += 35.0
                self._milestone_75 = True
        
        # Décrémenter le timer d'invincibilité
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        
        # 4. Déplacer les fantômes
        self._move_ghosts()
        
        # 5. Vérifier collision avec fantôme
        if self.pacman_pos in self.ghosts_pos:
            if self.invincible_timer > 0:
                # Mode invincible : Pacman mange le fantôme !
                # Retirer le fantôme touché et le respawn
                ghost_index = self.ghosts_pos.index(self.pacman_pos)
                self.ghosts_pos[ghost_index] = self.ghosts_start_pos[ghost_index]
                self.ghosts_eaten += 1
                reward += 50.0  # ÉNORME récompense pour manger un fantôme
            else:
                # Mode normal : Pacman perd une vie
                self.lives -= 1
                self.lives_lost += 1
                reward = -10.0  # Réduit de -20.0 à -10.0
                
                # Si plus de vies, fin de l'épisode
                if self.lives <= 0:
                    done = True
                    info = {
                        "reason": "game_over", 
                        "coins_collected": self.coins_collected,
                        "lives_lost": self.lives_lost,
                        "powerups_collected": self.powerups_collected,
                        "ghosts_eaten": self.ghosts_eaten
                    }
                    return self._get_state(), reward, done, info
                else:
                    # Respawn: remettre Pacman et les fantômes à leur position de départ
                    self.pacman_pos = self.pacman_start_pos
                    self.ghosts_pos = self.ghosts_start_pos.copy()
                    self.invincible_timer = 0  # Perte d'invincibilité au respawn
                    done = False
                    info = {
                        "reason": "life_lost", 
                        "coins_collected": self.coins_collected,
                        "lives_remaining": self.lives,
                        "lives_lost": self.lives_lost,
                        "powerups_collected": self.powerups_collected,
                        "ghosts_eaten": self.ghosts_eaten
                    }
                    return self._get_state(), reward, done, info
        
        # Sauvegarder la dernière action
        self.last_action = action
        
        # 6. Vérifier victoire (toutes les pièces ramassées)
        if len(self.coins) == 0:
            reward += 100.0  # Augmenté de 20.0 à 100.0 pour forte incitation
            done = True
            info = {
                "reason": "all_coins_collected", 
                "coins_collected": self.coins_collected,
                "powerups_collected": self.powerups_collected,
                "ghosts_eaten": self.ghosts_eaten
            }
            return self._get_state(), reward, done, info
        
        # 7. Continuer
        done = False
        info = {
            "coins_collected": self.coins_collected, 
            "steps": self.steps,
            "powerups_collected": self.powerups_collected,
            "invincible": self.invincible_timer > 0,
            "invincible_timer": self.invincible_timer,
            "ghosts_eaten": self.ghosts_eaten
        }
        
        return self._get_state(), reward, done, info
    
    def render(self) -> str:
        """
        Génère une représentation textuelle de la grille.
        
        Returns:
            String représentant l'état actuel du jeu
        """
        lines = []
        lines.append(f"\nÉpisode - Step {self.steps}")
        invincible_text = f" | INVINCIBLE ({self.invincible_timer})" if self.invincible_timer > 0 else ""
        lines.append(f"Pièces: {self.coins_collected}/{self.initial_coins_count} | Vies: {self.lives}/{self.num_lives} | Power-ups: {self.powerups_collected}/{self.initial_powerups_count}{invincible_text}")
        lines.append("-" * (self.grid_size * 2 + 1))
        
        for y in range(self.grid_size):
            row = []
            for x in range(self.grid_size):
                pos = (x, y)
                if pos == self.pacman_pos:
                    row.append("P" if self.invincible_timer == 0 else "P*")
                elif pos in self.ghosts_pos:
                    row.append("F")
                elif pos in self.powerups:
                    row.append("O")  # Power-up
                elif pos in self.coins:
                    row.append("C")
                elif pos in self.walls:
                    row.append("#")
                else:
                    row.append(".")
            lines.append(" ".join(row))
        
        lines.append("-" * (self.grid_size * 2 + 1))
        return "\n".join(lines)
    
    def get_state_for_agent(self) -> Tuple:
        """
        Retourne une représentation ULTRA-SIMPLIFIÉE de l'état pour l'agent Q-Learning.
        Espace d'états réduit pour apprentissage plus rapide:
        - Position de Pacman (discrétisée par zones)
        - Danger imminent (fantôme proche)
        - Direction vers objectif (pièce/power-up)
        - Progression (% pièces collectées)
        
        Returns:
            Tuple représentant l'état simplifié
        """
        px, py = self.pacman_pos
        
        # 1. Position discrétisée par zones (4x4 zones au lieu de cases exactes)
        zone_x = px // (self.grid_size // 4) if self.grid_size >= 4 else 0
        zone_y = py // (self.grid_size // 4) if self.grid_size >= 4 else 0
        zone_x = min(zone_x, 3)  # Limiter à 0-3
        zone_y = min(zone_y, 3)
        
        # 2. Danger imminent : fantôme très proche (distance <= 2)
        danger_close = 0
        if self.ghosts_pos and self.invincible_timer == 0:
            min_ghost_dist = min([abs(g[0] - px) + abs(g[1] - py) for g in self.ghosts_pos])
            danger_close = 1 if min_ghost_dist <= 2 else 0
        
        # 3. Direction optimale : pièce (ou power-up si fantôme proche)
        if danger_close and len(self.powerups) > 0:
            # Danger : chercher power-up en priorité
            target_direction = self._get_closest_powerup_direction()
        else:
            # Normal : chercher pièce
            target_direction = self._get_closest_coin_direction()
        
        # 4. Progression (par tranches de 25%)
        if self.initial_coins_count > 0:
            progress = self.coins_collected / self.initial_coins_count
            progress_bucket = int(progress * 4)  # 0, 1, 2, 3, 4 (0-25%, 25-50%, etc.)
        else:
            progress_bucket = 4
        
        # 5. Mode invincible (binaire)
        is_invincible = 1 if self.invincible_timer > 0 else 0
        
        # 6. Direction du fantôme le plus proche (pour évitement)
        ghost_direction = "none"
        if self.ghosts_pos and not is_invincible:
            closest_ghost = min(self.ghosts_pos, 
                               key=lambda g: abs(g[0] - px) + abs(g[1] - py))
            gx, gy = closest_ghost
            dx, dy = gx - px, gy - py
            if abs(dx) > abs(dy):
                ghost_direction = "right" if dx > 0 else "left"
            else:
                ghost_direction = "down" if dy > 0 else "up"
        
        # ESPACE D'ÉTATS RÉDUIT : ~4*4*2*5*5*2 = 1600 états (vs ~100k avant)
        return (zone_x, zone_y, danger_close, target_direction, progress_bucket, is_invincible, ghost_direction)


if __name__ == "__main__":
    # Test de l'environnement
    print("=== Test de l'environnement Mini-Pacman ===\n")
    
    env = MiniPacmanEnv(grid_size=10, num_ghosts=3, ghost_behavior="random", seed=42)
    
    print(env.render())
    
    # Simulation de quelques pas aléatoires
    for i in range(5):
        action = random.choice(env.ACTIONS)
        state, reward, done, info = env.step(action)
        print(f"\nAction: {action}, Récompense: {reward:.1f}")
        print(env.render())
        
        if done:
            print(f"\nÉpisode terminé: {info['reason']}")
            break
