<template>
  <div class="training-tab">
    <h2>⚙️ Configuration de l'entraînement</h2>

    <div class="config-sections">
      <!-- Configuration de l'environnement -->
      <section class="config-section">
        <h3>🎮 Environnement</h3>
        <div class="form-group">
          <label>Taille de la grille:</label>
          <input 
            v-model.number="config.grid_size" 
            type="number" 
            min="5" 
            max="15"
          />
          <span class="help-text">Taille NxN (5-15)</span>
        </div>

        <div class="form-group">
          <label>Nombre de fantômes:</label>
          <input 
            v-model.number="config.num_ghosts" 
            type="number" 
            min="1" 
            max="5"
          />
          <span class="help-text">1 à 5 fantômes</span>
        </div>

        <div class="form-group">
          <label>Comportement des fantômes:</label>
          <select v-model="config.ghost_behavior">
            <option value="random">Aléatoire</option>
            <option value="chase">Poursuite</option>
          </select>
          <span class="help-text">Random ou Chase</span>
        </div>

        <div class="form-group">
          <label>Pièces par ligne:</label>
          <input 
            v-model.number="config.coins_per_row" 
            type="number" 
            min="1" 
            max="15"
          />
          <span class="help-text">Nombre de pièces</span>
        </div>

        <div class="form-group">
          <label>Nombre de vies:</label>
          <input 
            v-model.number="config.num_lives" 
            type="number" 
            min="1" 
            max="10"
          />
          <span class="help-text">1 à 10 vies</span>
        </div>

        <div class="form-group checkbox-group">
          <label class="checkbox-label">
            <input 
              v-model="config.enable_powerups" 
              type="checkbox"
            />
            <span>Activer les Power-ups 💊</span>
          </label>
          <span class="help-text">Active les super-pièces qui rendent Pacman invincible</span>
        </div>
      </section>

      <!-- Configuration de l'entraînement -->
      <section class="config-section">
        <h3>🎓 Paramètres d'entraînement</h3>
        <div class="form-group">
          <label>Nombre d'épisodes:</label>
          <input 
            v-model.number="config.num_episodes" 
            type="number" 
            min="10" 
            max="2000"
          />
          <span class="help-text">10-2000 épisodes</span>
        </div>

        <div class="form-group">
          <label>Pas maximum par épisode:</label>
          <input 
            v-model.number="config.max_steps" 
            type="number" 
            min="50" 
            max="2000"
          />
          <span class="help-text">50-2000 pas</span>
        </div>
      </section>

      <!-- Hyperparamètres -->
      <section class="config-section">
        <h3>🧠 Hyperparamètres Q-Learning</h3>
        <div class="form-group">
          <label>Alpha (α) - Taux d'apprentissage:</label>
          <input 
            v-model.number="config.alpha" 
            type="number" 
            step="0.01" 
            min="0.01" 
            max="1"
          />
          <span class="help-text">0.01-1.0 (recommandé: 0.1)</span>
        </div>

        <div class="form-group">
          <label>Gamma (γ) - Discount factor:</label>
          <input 
            v-model.number="config.gamma" 
            type="number" 
            step="0.01" 
            min="0" 
            max="1"
          />
          <span class="help-text">0-1.0 (recommandé: 0.9)</span>
        </div>

        <div class="form-group">
          <label>Epsilon (ε) initial - Exploration:</label>
          <input 
            v-model.number="config.epsilon" 
            type="number" 
            step="0.01" 
            min="0" 
            max="1"
          />
          <span class="help-text">0-1.0 (recommandé: 1.0)</span>
        </div>

        <div class="form-group">
          <label>Epsilon minimum:</label>
          <input 
            v-model.number="config.epsilon_min" 
            type="number" 
            step="0.01" 
            min="0" 
            max="0.5"
          />
          <span class="help-text">0-0.5 (recommandé: 0.01)</span>
        </div>

        <div class="form-group">
          <label>Epsilon decay:</label>
          <input 
            v-model.number="config.epsilon_decay" 
            type="number" 
            step="0.001" 
            min="0.9" 
            max="1"
          />
          <span class="help-text">0.9-1.0 (recommandé: 0.995)</span>
        </div>
      </section>
    </div>

    <!-- Barre de progression -->
    <div v-if="isTraining" class="progress-section">
      <h3>📊 Progression de l'entraînement</h3>
      <div class="progress-bar-container">
        <div class="progress-bar" :style="{ width: trainingProgress + '%' }">
          <span class="progress-text">{{ trainingProgress }}%</span>
        </div>
      </div>
      <div class="progress-info">
        <div class="info-badge">
          <strong>Épisode:</strong> {{ currentEpisode }} / {{ config.num_episodes }}
        </div>
        <div class="info-badge">
          <strong>Temps écoulé:</strong> {{ elapsedTime }}s
        </div>
        <div class="info-badge">
          <strong>Vitesse:</strong> {{ episodesPerSecond }} eps/s
        </div>
      </div>
    </div>

    <!-- Bouton de lancement -->
    <div class="action-section">
      <button 
        class="train-button" 
        @click="startTraining"
        :disabled="isTraining"
      >
        <span v-if="!isTraining">🚀 Lancer l'entraînement</span>
        <span v-else>⏳ Entraînement en cours...</span>
      </button>

      <button 
        class="reset-button" 
        @click="resetConfig"
        :disabled="isTraining"
      >
        🔄 Réinitialiser
      </button>
    </div>

    <!-- Message de statut -->
    <div v-if="statusMessage" :class="['status-message', statusType]">
      {{ statusMessage }}
    </div>

    <!-- Résumé des résultats -->
    <div v-if="trainingResults" class="results-summary">
      <h3>✅ Entraînement terminé !</h3>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Récompense moyenne</div>
          <div class="stat-value">{{ trainingResults.avg_reward.toFixed(2) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Pièces moyennes</div>
          <div class="stat-value">{{ trainingResults.avg_coins.toFixed(1) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Taux de succès</div>
          <div class="stat-value">{{ trainingResults.success_rate.toFixed(1) }}%</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Temps d'entraînement</div>
          <div class="stat-value">{{ trainingResults.training_time.toFixed(1) }}s</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Taille Q-table</div>
          <div class="stat-value">{{ trainingResults.q_table_size }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import axios from 'axios'

const API_URL = 'http://localhost:5000/api'

export default {
  name: 'TrainingTab',
  emits: ['training-complete'],
  setup(props, { emit }) {
    const config = reactive({
      grid_size: 10,
      num_ghosts: 3,
      ghost_behavior: 'random',
      coins_per_row: 10,
      num_lives: 3,
      enable_powerups: true,
      num_episodes: 500,
      max_steps: 500,
      alpha: 0.1,
      gamma: 0.9,
      epsilon: 1.0,
      epsilon_min: 0.01,
      epsilon_decay: 0.995
    })

    const isTraining = ref(false)
    const statusMessage = ref('')
    const statusType = ref('info')
    const trainingResults = ref(null)
    
    // Variables de progression
    const trainingProgress = ref(0)
    const currentEpisode = ref(0)
    const elapsedTime = ref(0)
    const episodesPerSecond = ref(0)
    let trainingStartTime = 0
    let progressInterval = null

    const resetConfig = async () => {
      try {
        const response = await axios.get(`${API_URL}/config`)
        Object.assign(config, response.data)
        statusMessage.value = 'Configuration réinitialisée'
        statusType.value = 'info'
        trainingResults.value = null
      } catch (error) {
        statusMessage.value = 'Erreur lors de la réinitialisation'
        statusType.value = 'error'
      }
    }

    const startTraining = async () => {
      isTraining.value = true
      statusMessage.value = 'Entraînement en cours... Cela peut prendre quelques minutes.'
      statusType.value = 'info'
      trainingResults.value = null
      
      // Initialiser la progression
      trainingProgress.value = 0
      currentEpisode.value = 0
      elapsedTime.value = 0
      episodesPerSecond.value = 0
      trainingStartTime = Date.now()
      
      // Simuler la progression (approximation)
      progressInterval = setInterval(() => {
        const elapsed = (Date.now() - trainingStartTime) / 1000
        elapsedTime.value = Math.floor(elapsed)
        
        // Estimer la progression basée sur le temps
        // Approximation: 1 épisode ≈ 0.1-0.5s selon complexité
        const estimatedTimePerEpisode = 0.3
        const estimatedEpisodes = Math.min(
          Math.floor(elapsed / estimatedTimePerEpisode),
          config.num_episodes
        )
        
        currentEpisode.value = estimatedEpisodes
        trainingProgress.value = Math.min(
          Math.floor((estimatedEpisodes / config.num_episodes) * 100),
          99
        )
        
        episodesPerSecond.value = (estimatedEpisodes / elapsed).toFixed(1)
      }, 500)

      try {
        const response = await axios.post(`${API_URL}/train`, config)
        
        // Arrêter la simulation
        if (progressInterval) {
          clearInterval(progressInterval)
          progressInterval = null
        }
        
        if (response.data.success) {
          trainingProgress.value = 100
          currentEpisode.value = config.num_episodes
          trainingResults.value = response.data.stats
          statusMessage.value = response.data.message
          statusType.value = 'success'
          
          // Notifier le parent que l'entraînement est terminé
          setTimeout(() => {
            emit('training-complete')
          }, 2000)
        } else {
          statusMessage.value = response.data.message
          statusType.value = 'error'
        }
      } catch (error) {
        if (progressInterval) {
          clearInterval(progressInterval)
          progressInterval = null
        }
        statusMessage.value = `Erreur: ${error.message}`
        statusType.value = 'error'
      } finally {
        isTraining.value = false
      }
    }

    return {
      config,
      isTraining,
      statusMessage,
      statusType,
      trainingResults,
      trainingProgress,
      currentEpisode,
      elapsedTime,
      episodesPerSecond,
      resetConfig,
      startTraining
    }
  }
}
</script>

<style scoped>
.training-tab {
  padding: 20px;
}

h2 {
  color: #1a4e8a;
  margin-bottom: 30px;
  font-size: 2em;
}

.config-sections {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.config-section {
  background: #f8fbff;
  padding: 20px;
  border-radius: 8px;
  border: 2px solid #e0e7ff;
}

.config-section h3 {
  color: #1a4e8a;
  margin-bottom: 15px;
  font-size: 1.3em;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
  color: #333;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px;
  border: 2px solid #ddd;
  border-radius: 5px;
  font-size: 1em;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #1a4e8a;
}

.help-text {
  display: block;
  margin-top: 5px;
  font-size: 0.85em;
  color: #666;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-weight: 600;
  color: #333;
}

.checkbox-label input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.checkbox-label span {
  font-size: 1.1em;
}

.progress-section {
  background: #f0f7ff;
  padding: 20px;
  border-radius: 8px;
  border: 2px solid #1a4e8a;
  margin-bottom: 20px;
}

.progress-section h3 {
  color: #1a4e8a;
  margin-bottom: 15px;
}

.progress-bar-container {
  background: #e0e7ff;
  border-radius: 10px;
  height: 40px;
  overflow: hidden;
  margin-bottom: 15px;
  position: relative;
}

.progress-bar {
  background: linear-gradient(90deg, #1a4e8a 0%, #2563eb 100%);
  height: 100%;
  transition: width 0.5s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 60px;
}

.progress-text {
  color: white;
  font-weight: bold;
  font-size: 1.1em;
}

.progress-info {
  display: flex;
  gap: 15px;
  justify-content: space-around;
  flex-wrap: wrap;
}

.info-badge {
  background: white;
  padding: 10px 15px;
  border-radius: 5px;
  border: 1px solid #ddd;
  flex: 1;
  min-width: 150px;
  text-align: center;
}

.info-badge strong {
  display: block;
  color: #1a4e8a;
  margin-bottom: 5px;
}

.action-section {
  display: flex;
  gap: 15px;
  margin: 30px 0;
}

.train-button,
.reset-button {
  flex: 1;
  padding: 15px 30px;
  font-size: 1.2em;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.train-button {
  background: #1a4e8a;
  color: white;
}

.train-button:hover:not(:disabled) {
  background: #15416f;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.train-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.reset-button {
  background: #6c757d;
  color: white;
}

.reset-button:hover:not(:disabled) {
  background: #5a6268;
}

.status-message {
  padding: 15px;
  border-radius: 8px;
  margin: 20px 0;
  font-weight: 500;
}

.status-message.info {
  background: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

.status-message.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status-message.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.results-summary {
  background: #d4edda;
  padding: 25px;
  border-radius: 8px;
  border: 2px solid #c3e6cb;
  margin-top: 20px;
}

.results-summary h3 {
  color: #155724;
  margin-bottom: 20px;
  font-size: 1.5em;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 15px;
}

.stat-card {
  background: white;
  padding: 15px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-label {
  font-size: 0.9em;
  color: #666;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 1.8em;
  font-weight: bold;
  color: #1a4e8a;
}
</style>
