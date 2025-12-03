<template>
  <div class="grid-visualization">
    <h4>🎮 Visualisation de la partie</h4>
    
    <!-- Informations de l'épisode -->
      <div class="episode-info">
      <div class="info-item">
        <strong>Step:</strong> {{ currentStep }} / {{ history.length - 1 }}
      </div>
      <div class="info-item">
        <strong>Pièces collectées:</strong> 🪙 {{ currentState.info.coins_collected }}
      </div>
      <div v-if="currentState.info.powerups_collected !== undefined" class="info-item">
        <strong>Power-ups:</strong> 💊 {{ currentState.info.powerups_collected }}
      </div>
      <div v-if="currentState.info.invincible" class="info-item invincible-status">
        <strong>⭐ INVINCIBLE</strong> ({{ currentState.info.invincible_timer }} pas restants)
      </div>
      <div v-if="currentState.info.ghosts_eaten !== undefined && currentState.info.ghosts_eaten > 0" class="info-item">
        <strong>Fantômes mangés:</strong> 👻 {{ currentState.info.ghosts_eaten }}
      </div>
      <div v-if="currentState.info.lives_remaining !== undefined" class="info-item">
        <strong>Vies:</strong> ❤️ {{ currentState.info.lives_remaining }}
      </div>
      <div class="info-item">
        <strong>Récompense:</strong> {{ currentState.reward.toFixed(1) }}
      </div>
      <div v-if="currentState.action" class="info-item">
        <strong>Action:</strong> {{ getActionEmoji(currentState.action) }} {{ currentState.action }}
      </div>
    </div>    <!-- Grille de jeu -->
    <div class="game-grid" :style="gridStyle">
      <div 
        v-for="(cell, index) in gridCells" 
        :key="index"
        class="grid-cell"
        :class="cell.class"
      >
        {{ cell.content }}
      </div>
    </div>

    <!-- Contrôles de lecture -->
    <div class="playback-controls">
      <button @click="firstStep" :disabled="currentStep === 0">
        ⏮️ Début
      </button>
      <button @click="previousStep" :disabled="currentStep === 0">
        ◀️ Précédent
      </button>
      <button @click="togglePlay">
        {{ isPlaying ? '⏸️ Pause' : '▶️ Play' }}
      </button>
      <button @click="nextStep" :disabled="currentStep === history.length - 1">
        ▶️ Suivant
      </button>
      <button @click="lastStep" :disabled="currentStep === history.length - 1">
        ⏭️ Fin
      </button>
    </div>

    <!-- Slider de vitesse -->
    <div class="speed-control">
      <label>Vitesse: {{ playbackSpeed }}ms</label>
      <input 
        type="range" 
        v-model.number="playbackSpeed" 
        min="100" 
        max="1000" 
        step="100"
      />
    </div>

    <!-- Résultat final -->
    <div v-if="currentStep === history.length - 1" class="final-result">
      <div v-if="currentState.done" :class="['result-badge', resultClass]">
        {{ resultMessage }}
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onUnmounted } from 'vue'

export default {
  name: 'GridVisualization',
  props: {
    history: {
      type: Array,
      required: true
    }
  },
  setup(props) {
    const currentStep = ref(0)
    const isPlaying = ref(false)
    const playbackSpeed = ref(500)
    let playInterval = null

    const currentState = computed(() => props.history[currentStep.value])

    const gridSize = computed(() => {
      // Déduire la taille de la grille à partir des positions
      const allPositions = props.history.flatMap(state => {
        const positions = [
          state.pacman_pos,
          ...state.ghosts_pos,
          ...state.coins
        ]
        // Ajouter les power-ups s'ils existent
        if (state.powerups && state.powerups.length > 0) {
          positions.push(...state.powerups)
        }
        return positions
      })
      const maxX = Math.max(...allPositions.map(pos => pos[0]))
      const maxY = Math.max(...allPositions.map(pos => pos[1]))
      return Math.max(maxX, maxY) + 1
    })

    const gridStyle = computed(() => ({
      gridTemplateColumns: `repeat(${gridSize.value}, 1fr)`
    }))

    const gridCells = computed(() => {
      const cells = []
      const state = currentState.value
      
      for (let y = 0; y < gridSize.value; y++) {
        for (let x = 0; x < gridSize.value; x++) {
          const pos = [x, y]
          let content = ''
          let cellClass = ''

          // Vérifier murs (ajouté)
          if (state.walls && state.walls.some(w => w[0] === x && w[1] === y)) {
            content = '🧱'
            cellClass = 'wall'
          }
          // Vérifier Pacman
          else if (state.pacman_pos[0] === x && state.pacman_pos[1] === y) {
            // Afficher différemment si invincible
            const isInvincible = state.info && state.info.invincible
            content = isInvincible ? '⭐' : '🟡'
            cellClass = isInvincible ? 'pacman invincible' : 'pacman'
          }
          // Vérifier fantômes
          else if (state.ghosts_pos.some(g => g[0] === x && g[1] === y)) {
            content = '👻'
            cellClass = 'ghost'
          }
          // Vérifier power-ups (NOUVEAU)
          else if (state.powerups && Array.isArray(state.powerups) && state.powerups.some(p => p[0] === x && p[1] === y)) {
            content = '💊'
            cellClass = 'powerup'
          }
          // Vérifier pièces
          else if (state.coins && state.coins.some(c => c[0] === x && c[1] === y)) {
            content = '🪙'
            cellClass = 'coin'
          }
          // Case vide
          else {
            content = ''
            cellClass = 'empty'
          }

          cells.push({ content, class: cellClass })
        }
      }
      
      return cells
    })

    const resultClass = computed(() => {
      if (!currentState.value.done) return ''
      return currentState.value.info.reason === 'all_coins_collected' ? 'success' : 'failure'
    })

    const resultMessage = computed(() => {
      if (!currentState.value.done) return ''
      if (currentState.value.info.reason === 'all_coins_collected') {
        return '🎉 VICTOIRE ! Toutes les pièces collectées !'
      } else {
        return '💀 DÉFAITE ! Attrapé par un fantôme !'
      }
    })

    const getActionEmoji = (action) => {
      const emojis = {
        'up': '⬆️',
        'down': '⬇️',
        'left': '⬅️',
        'right': '➡️'
      }
      return emojis[action] || '❓'
    }

    const firstStep = () => {
      currentStep.value = 0
      stopPlay()
    }

    const lastStep = () => {
      currentStep.value = props.history.length - 1
      stopPlay()
    }

    const previousStep = () => {
      if (currentStep.value > 0) {
        currentStep.value--
      }
    }

    const nextStep = () => {
      if (currentStep.value < props.history.length - 1) {
        currentStep.value++
      } else {
        stopPlay()
      }
    }

    const togglePlay = () => {
      if (isPlaying.value) {
        stopPlay()
      } else {
        startPlay()
      }
    }

    const startPlay = () => {
      isPlaying.value = true
      playInterval = setInterval(() => {
        if (currentStep.value < props.history.length - 1) {
          currentStep.value++
        } else {
          stopPlay()
        }
      }, playbackSpeed.value)
    }

    const stopPlay = () => {
      isPlaying.value = false
      if (playInterval) {
        clearInterval(playInterval)
        playInterval = null
      }
    }

    // Arrêter la lecture quand le composant est détruit
    onUnmounted(() => {
      stopPlay()
    })

    // Réinitialiser quand l'historique change
    watch(() => props.history, () => {
      currentStep.value = 0
      stopPlay()
    })

    return {
      currentStep,
      currentState,
      isPlaying,
      playbackSpeed,
      gridSize,
      gridStyle,
      gridCells,
      resultClass,
      resultMessage,
      getActionEmoji,
      firstStep,
      lastStep,
      previousStep,
      nextStep,
      togglePlay
    }
  }
}
</script>

<style scoped>
.grid-visualization {
  background: #f8fbff;
  padding: 25px;
  border-radius: 10px;
  border: 2px solid #e0e7ff;
  margin-top: 20px;
}

h4 {
  color: #1a4e8a;
  margin-bottom: 20px;
  font-size: 1.3em;
}

.episode-info {
  display: flex;
  justify-content: space-around;
  background: white;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.info-item {
  font-size: 1.1em;
}

.info-item strong {
  color: #1a4e8a;
}

.game-grid {
  display: grid;
  gap: 2px;
  background: #ddd;
  padding: 2px;
  border-radius: 8px;
  margin: 20px auto;
  max-width: 600px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.grid-cell {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2em;
  background: #2c3e50;
  transition: all 0.3s ease;
}

.grid-cell.empty {
  background: #2c3e50;
}

.grid-cell.pacman {
  background: #3498db;
  animation: pulse 0.5s ease-in-out infinite;
}

.grid-cell.ghost {
  background: #e74c3c;
}

.grid-cell.coin {
  background: #2c3e50;
  animation: sparkle 1s ease-in-out infinite;
}

.grid-cell.powerup {
  background: #8e44ad;
  animation: glow 1s ease-in-out infinite;
  box-shadow: 0 0 10px #8e44ad;
}

.grid-cell.invincible {
  background: #f39c12;
  animation: rainbow 1s linear infinite;
  box-shadow: 0 0 15px #f39c12;
}

.grid-cell.wall {
  background: #34495e;
  border: 1px solid #1a1a1a;
}

.invincible-status {
  color: #f39c12;
  font-weight: bold;
  animation: pulse-text 0.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

@keyframes sparkle {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

@keyframes glow {
  0%, 100% { 
    opacity: 1;
    box-shadow: 0 0 10px #8e44ad;
  }
  50% { 
    opacity: 0.8;
    box-shadow: 0 0 20px #8e44ad, 0 0 30px #8e44ad;
  }
}

@keyframes rainbow {
  0% { background: #f39c12; }
  25% { background: #e74c3c; }
  50% { background: #9b59b6; }
  75% { background: #3498db; }
  100% { background: #f39c12; }
}

@keyframes pulse-text {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.playback-controls {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin: 20px 0;
}

.playback-controls button {
  padding: 10px 20px;
  font-size: 1em;
  font-weight: 600;
  background: #1a4e8a;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.playback-controls button:hover:not(:disabled) {
  background: #15416f;
  transform: translateY(-2px);
}

.playback-controls button:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
}

.speed-control {
  text-align: center;
  margin: 20px 0;
}

.speed-control label {
  display: block;
  margin-bottom: 10px;
  font-weight: 600;
  color: #1a4e8a;
}

.speed-control input[type="range"] {
  width: 300px;
  max-width: 100%;
}

.final-result {
  margin-top: 20px;
  text-align: center;
}

.result-badge {
  display: inline-block;
  padding: 15px 30px;
  font-size: 1.3em;
  font-weight: bold;
  border-radius: 8px;
  animation: bounce 0.5s ease-in-out;
}

.result-badge.success {
  background: #d4edda;
  color: #155724;
  border: 2px solid #c3e6cb;
}

.result-badge.failure {
  background: #f8d7da;
  color: #721c24;
  border: 2px solid #f5c6cb;
}

@keyframes bounce {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}
</style>
