# Mini-Pacman avec Q-Learning

Projet d'apprentissage par renforcement - ESGI 5ème année

## Description

Mini-Pacman est un jeu simplifié sur grille 10×10 où un agent (Pacman) apprend à ramasser des pièces tout en évitant des fantômes, grâce à l'algorithme Q-Learning.

## Architecture du projet

```
PROJECT_MINI_PACMAN/
├── backend/
│   ├── environment.py      # Environnement MiniPacman
│   ├── agent.py            # Agent Q-Learning
│   ├── training.py         # Fonctions d'entraînement
│   ├── api.py              # API Flask
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # Composants Vue.js
│   │   ├── App.vue
│   │   └── main.js
│   └── package.json
├── saved_models/           # Q-tables sauvegardées
├── results/                # Graphiques générés
└── README.md
```

## Installation

### Backend (Python)

```bash
cd backend
pip install -r requirements.txt
```

### Frontend (Vue.js)

```bash
cd frontend
npm install
```

## Utilisation

### Lancer le backend

```bash
cd backend
python api.py
```

### Lancer le frontend

```bash
cd frontend
npm run dev
```

## Fonctionnalités

- ✅ Environnement MiniPacman configurable (taille grille, nombre de fantômes)
- ✅ Apprentissage par Q-Learning
- ✅ Interface web avec Vue.js
- ✅ Visualisation en temps réel
- ✅ Graphiques de performance (Matplotlib)
- ✅ Replay de parties apprises

## Modélisation RL

### États
- Position de Pacman (px, py)
- Position des fantômes
- Pièces restantes

### Actions
- `up`, `down`, `left`, `right`

### Récompenses
- **+5** : ramasser une pièce
- **+20** : ramasser toutes les pièces
- **-20** : attrapé par un fantôme
- **-0.1** : coût de déplacement

## Auteur

Projet réalisé dans le cadre du cours IA pour les Jeux - ESGI 2025
