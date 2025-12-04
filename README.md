# Mini-Pacman avec Q-Learning

Agent intelligent apprenant à jouer à Pacman via Q-Learning.

## Description

Pacman apprend de manière autonome à collecter des pièces dans un labyrinthe 10×10 tout en évitant 3 fantômes mobiles. L'agent utilise l'algorithme Q-Learning avec un espace d'états réduit à 1600 configurations pour un apprentissage rapide.

L'environnement inclut des power-ups permettant à Pacman de devenir invincible et de manger les fantômes. Un système de récompenses progressif guide l'apprentissage vers des stratégies efficaces.

## Installation

### Prérequis

- Python 3.8+
- Node.js 16+
- npm

### Backend

```bash
cd backend
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Lancement

Ouvrir deux terminaux :

**Terminal 1 - Backend :**
```bash
cd backend
python api.py
```
Le serveur démarre sur http://localhost:5000

**Terminal 2 - Frontend :**
```bash
cd frontend
npm run dev
```
L'interface s'ouvre sur http://localhost:5173

## Structure

```
backend/
  environment.py    Environnement de jeu
  agent.py          Agent Q-Learning
  training.py       Entraînement
  api.py            API Flask

frontend/
  src/
    components/     Composants Vue
    App.vue         Application principale
```

## Apprentissage

L'agent réduit la complexité en utilisant :
- 16 zones au lieu de 100 cases exactes
- Danger binaire (fantôme proche ou non)
- Direction vers objectif (5 valeurs)
- Progression par tranches de 25%

Espace d'états : 1600 (au lieu de millions)
Taille Q-table : ~6000 entrées

Récompenses :
- +10-15 par pièce collectée
- +50 pour manger un fantôme
- -10 pour perdre une vie
