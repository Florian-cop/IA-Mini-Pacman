<template>
  <div id="app">
    <header class="app-header">
      <h1>🎮 Mini-Pacman avec Q-Learning</h1>
      <p>Apprentissage par renforcement - ESGI 2025</p>
    </header>

    <nav class="tabs">
      <button 
        :class="['tab', { active: currentTab === 'training' }]"
        @click="currentTab = 'training'"
      >
        🎓 Entraînement
      </button>
      <button 
        :class="['tab', { active: currentTab === 'results' }]"
        @click="currentTab = 'results'"
      >
        📊 Résultats
      </button>
    </nav>

    <main class="main-content">
      <TrainingTab 
        v-if="currentTab === 'training'"
        @training-complete="onTrainingComplete"
      />
      <ResultsTab 
        v-if="currentTab === 'results'"
        :training-completed="trainingCompleted"
      />
    </main>

    <footer class="app-footer">
      <p>Projet Mini-Pacman - Q-Learning | Backend: Flask | Frontend: Vue.js</p>
    </footer>
  </div>
</template>

<script>
import { ref } from 'vue'
import TrainingTab from './components/TrainingTab.vue'
import ResultsTab from './components/ResultsTab.vue'

export default {
  name: 'App',
  components: {
    TrainingTab,
    ResultsTab
  },
  setup() {
    const currentTab = ref('training')
    const trainingCompleted = ref(false)

    const onTrainingComplete = () => {
      trainingCompleted.value = true
      currentTab.value = 'results'
    }

    return {
      currentTab,
      trainingCompleted,
      onTrainingComplete
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

#app {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.app-header {
  background: white;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  text-align: center;
  margin-bottom: 20px;
}

.app-header h1 {
  color: #1a4e8a;
  font-size: 2.5em;
  margin-bottom: 10px;
}

.app-header p {
  color: #666;
  font-size: 1.1em;
}

.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.tab {
  flex: 1;
  padding: 15px 30px;
  font-size: 1.1em;
  font-weight: 600;
  border: none;
  border-radius: 10px;
  background: white;
  color: #666;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.tab:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.tab.active {
  background: #1a4e8a;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.main-content {
  background: white;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  min-height: 500px;
}

.app-footer {
  text-align: center;
  color: white;
  padding: 20px;
  margin-top: 20px;
  font-size: 0.9em;
}
</style>
