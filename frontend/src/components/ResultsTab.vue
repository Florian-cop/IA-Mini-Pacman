<template>
  <div class="results-tab">
    <h2>📊 Résultats de l'entraînement</h2>

    <div v-if="!trainingCompleted" class="no-data">
      <p>⚠️ Aucun entraînement n'a encore été effectué.</p>
      <p>Veuillez d'abord entraîner un agent dans l'onglet "Entraînement".</p>
    </div>

    <div v-else>
      <!-- Configuration utilisée -->
      <section class="config-recap">
        <h3>⚙️ Configuration utilisée</h3>
        <div v-if="results" class="config-grid">
          <div class="config-item">
            <span class="config-label">Grille:</span>
            <span class="config-value">{{ results.config.grid_size }}×{{ results.config.grid_size }}</span>
          </div>
          <div class="config-item">
            <span class="config-label">Fantômes:</span>
            <span class="config-value">{{ results.config.num_ghosts }} ({{ results.config.ghost_behavior }})</span>
          </div>
          <div class="config-item">
            <span class="config-label">Épisodes:</span>
            <span class="config-value">{{ results.config.num_episodes }}</span>
          </div>
          <div class="config-item">
            <span class="config-label">Alpha (α):</span>
            <span class="config-value">{{ results.config.alpha }}</span>
          </div>
          <div class="config-item">
            <span class="config-label">Gamma (γ):</span>
            <span class="config-value">{{ results.config.gamma }}</span>
          </div>
          <div class="config-item">
            <span class="config-label">Epsilon (ε):</span>
            <span class="config-value">{{ results.config.epsilon }} → {{ results.config.epsilon_min }}</span>
          </div>
        </div>
      </section>

      <!-- Statistiques globales -->
      <section class="global-stats">
        <h3>📈 Statistiques globales</h3>
        <div v-if="results" class="stats-grid">
          <div class="stat-card large">
            <div class="stat-icon">🏆</div>
            <div class="stat-label">Taux de succès</div>
            <div class="stat-value">{{ results.stats.success_rate.toFixed(1) }}%</div>
          </div>
          <div class="stat-card large">
            <div class="stat-icon">💰</div>
            <div class="stat-label">Récompense moyenne</div>
            <div class="stat-value">{{ results.stats.avg_reward.toFixed(2) }}</div>
          </div>
          <div class="stat-card large">
            <div class="stat-icon">🪙</div>
            <div class="stat-label">Pièces moyennes</div>
            <div class="stat-value">{{ results.stats.avg_coins.toFixed(1) }}</div>
          </div>
          <div class="stat-card large">
            <div class="stat-icon">👣</div>
            <div class="stat-label">Steps moyens</div>
            <div class="stat-value">{{ results.stats.avg_steps.toFixed(1) }}</div>
          </div>
          <div class="stat-card large">
            <div class="stat-icon">⏱️</div>
            <div class="stat-label">Temps d'entraînement</div>
            <div class="stat-value">{{ results.stats.training_time.toFixed(1) }}s</div>
          </div>
          <div class="stat-card large">
            <div class="stat-icon">🧠</div>
            <div class="stat-label">Taille Q-table</div>
            <div class="stat-value">{{ results.stats.q_table_size }}</div>
          </div>
        </div>
      </section>

      <!-- Graphiques -->
      <section class="graphs-section">
        <h3>📉 Courbes d'apprentissage</h3>
        
        <div v-if="loading" class="loading">
          <p>Chargement des graphiques...</p>
        </div>

        <div v-else-if="results" class="graphs-grid">
          <div class="graph-card">
            <h4>Récompense par épisode</h4>
            <img :src="results.graphs.rewards" alt="Graphique des récompenses" />
          </div>
          
          <div class="graph-card">
            <h4>Pièces collectées par épisode</h4>
            <img :src="results.graphs.coins" alt="Graphique des pièces" />
          </div>
          
          <div class="graph-card">
            <h4>Taux de succès</h4>
            <img :src="results.graphs.success_rate" alt="Graphique du taux de succès" />
          </div>
        </div>
      </section>

      <!-- Rejouer une partie -->
      <section class="replay-section">
        <h3>🎬 Démonstration</h3>
        <p>Visualisez l'agent entraîné en action !</p>
        
        <button 
          class="replay-button"
          @click="startReplay"
          :disabled="isReplaying"
        >
          <span v-if="!isReplaying">▶️ Rejouer une partie</span>
          <span v-else>⏳ Génération en cours...</span>
        </button>

        <GridVisualization 
          v-if="replayHistory"
          :history="replayHistory"
        />
      </section>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import GridVisualization from './GridVisualization.vue'

const API_URL = 'http://localhost:5000/api'

export default {
  name: 'ResultsTab',
  components: {
    GridVisualization
  },
  props: {
    trainingCompleted: {
      type: Boolean,
      default: false
    }
  },
  setup(props) {
    const results = ref(null)
    const loading = ref(false)
    const isReplaying = ref(false)
    const replayHistory = ref(null)

    const loadResults = async () => {
      loading.value = true
      try {
        const response = await axios.get(`${API_URL}/results`)
        if (response.data.success) {
          results.value = response.data
        }
      } catch (error) {
        console.error('Erreur lors du chargement des résultats:', error)
      } finally {
        loading.value = false
      }
    }

    const startReplay = async () => {
      isReplaying.value = true
      replayHistory.value = null
      
      try {
        const response = await axios.post(`${API_URL}/replay`, {
          max_steps: 200
        })
        
        if (response.data.success) {
          replayHistory.value = response.data.history
        }
      } catch (error) {
        console.error('Erreur lors du replay:', error)
      } finally {
        isReplaying.value = false
      }
    }

    // Charger les résultats quand l'entraînement est terminé
    watch(() => props.trainingCompleted, (newValue) => {
      if (newValue) {
        loadResults()
      }
    })

    onMounted(() => {
      if (props.trainingCompleted) {
        loadResults()
      }
    })

    return {
      results,
      loading,
      isReplaying,
      replayHistory,
      startReplay
    }
  }
}
</script>

<style scoped>
.results-tab {
  padding: 20px;
}

h2 {
  color: #1a4e8a;
  margin-bottom: 30px;
  font-size: 2em;
}

h3 {
  color: #1a4e8a;
  margin-bottom: 20px;
  font-size: 1.5em;
}

.no-data {
  text-align: center;
  padding: 60px 20px;
  background: #fff3cd;
  border-radius: 8px;
  border: 2px solid #ffeaa7;
}

.no-data p {
  font-size: 1.2em;
  color: #856404;
  margin: 10px 0;
}

/* Configuration recap */
.config-recap {
  background: #f8fbff;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
  border: 2px solid #e0e7ff;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.config-item {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  background: white;
  border-radius: 5px;
}

.config-label {
  font-weight: 600;
  color: #666;
}

.config-value {
  color: #1a4e8a;
  font-weight: bold;
}

/* Statistiques */
.global-stats {
  margin-bottom: 30px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.stat-card.large {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  border-radius: 10px;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  font-size: 2.5em;
  margin-bottom: 10px;
}

.stat-label {
  font-size: 0.9em;
  opacity: 0.9;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 2em;
  font-weight: bold;
}

/* Graphiques */
.graphs-section {
  margin-bottom: 30px;
}

.loading {
  text-align: center;
  padding: 40px;
  font-size: 1.2em;
  color: #666;
}

.graphs-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 30px;
}

.graph-card {
  background: #f8fbff;
  padding: 20px;
  border-radius: 8px;
  border: 2px solid #e0e7ff;
}

.graph-card h4 {
  color: #1a4e8a;
  margin-bottom: 15px;
  font-size: 1.2em;
}

.graph-card img {
  width: 100%;
  height: auto;
  border-radius: 5px;
}

/* Replay */
.replay-section {
  margin-top: 30px;
}

.replay-section p {
  color: #666;
  margin-bottom: 15px;
}

.replay-button {
  padding: 15px 40px;
  font-size: 1.2em;
  font-weight: 600;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 20px;
}

.replay-button:hover:not(:disabled) {
  background: #218838;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.replay-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>
