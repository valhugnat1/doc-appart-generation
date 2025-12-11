<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ConvSidebar from '../components/ConvSidebar.vue'
import DocumentSidebar from '../components/DocumentSidebar.vue'
import ThemeToggle from '../components/ThemeToggle.vue'
import { API_BASE_URL } from '@/config.js'

const route = useRoute()
const isSidebarOpen = ref(true)
const isDocumentSidebarOpen = ref(false)
const bailHtml = ref('')
const isAiLoading = ref(false)
const sidebarRef = ref(null)

const leftSidebarWidth = ref(280)
const documentSidebarWidth = ref(600)
const isResizingLeft = ref(false)
const isResizingRight = ref(false)

const startResizeLeft = () => {
  isResizingLeft.value = true
  document.addEventListener('mousemove', handleResizeLeft)
  document.addEventListener('mouseup', stopResizeLeft)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

const handleResizeLeft = (e) => {
  if (isResizingLeft.value) {
    const newWidth = e.clientX
    if (newWidth > 200 && newWidth < 500) {
      leftSidebarWidth.value = newWidth
    }
  }
}

const stopResizeLeft = () => {
  isResizingLeft.value = false
  document.removeEventListener('mousemove', handleResizeLeft)
  document.removeEventListener('mouseup', stopResizeLeft)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

const startResizeRight = () => {
  isResizingRight.value = true
  document.addEventListener('mousemove', handleResizeRight)
  document.addEventListener('mouseup', stopResizeRight)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

const handleResizeRight = (e) => {
  if (isResizingRight.value) {
    const newWidth = window.innerWidth - e.clientX
    if (newWidth > 300 && newWidth < 1200) {
      documentSidebarWidth.value = newWidth
    }
  }
}

const stopResizeRight = () => {
  isResizingRight.value = false
  document.removeEventListener('mousemove', handleResizeRight)
  document.removeEventListener('mouseup', stopResizeRight)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value
}

const fetchBail = async (conversationId) => {
  if (!conversationId) return

  try {
    const response = await fetch(`${API_BASE_URL}/bail/${conversationId}`)
    if (response.ok) {
      const data = await response.json()
      bailHtml.value = data.html
      if (bailHtml.value) {
        isDocumentSidebarOpen.value = true
      }
    } else {
      isDocumentSidebarOpen.value = false
      bailHtml.value = ''
    }
  } catch (error) {
    console.error('Error fetching bail:', error)
    isDocumentSidebarOpen.value = false
    bailHtml.value = ''
  }
}

onMounted(() => {
  if (route.params.id) {
    fetchBail(route.params.id)
  }
})

watch(() => route.params.id, (newId) => {
  if (newId) {
    fetchBail(newId)
  } else {
    isDocumentSidebarOpen.value = false
    bailHtml.value = ''
  }
})

const onMessageReceived = (conversationId) => {
  fetchBail(conversationId)
  if (sidebarRef.value) {
    sidebarRef.value.fetchConversations()
  }
}

const handleLoading = (loading) => {
  isAiLoading.value = loading
  if (loading) {
    isDocumentSidebarOpen.value = true
  }
}
  const showMonitoring = ref(false)
  const monitoringStats = ref(null)
  let monitoringInterval = null

  const fetchMonitoringStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/monitoring/stats`)
      if (response.ok) {
        monitoringStats.value = await response.json()
      }
    } catch (e) {
      console.error(e)
    }
  }

  const toggleMonitoring = () => {
    showMonitoring.value = !showMonitoring.value
    if (showMonitoring.value) {
      fetchMonitoringStats()
      monitoringInterval = setInterval(fetchMonitoringStats, 5000)
    } else {
      if (monitoringInterval) clearInterval(monitoringInterval)
    }
  }

  // Clean up interval
  watch(showMonitoring, (val) => {
    if (!val && monitoringInterval) {
      clearInterval(monitoringInterval)
    }
  })
</script>

<template>
  <div class="admin-container">
    <!-- Left Sidebar -->
    <ConvSidebar 
      ref="sidebarRef" 
      :is-open="isSidebarOpen" 
      :width="leftSidebarWidth" 
      @toggle="toggleSidebar" 
    />

    <!-- Left Resizer -->
    <div 
      v-if="isSidebarOpen"
      class="resizer left-resizer" 
      @mousedown="startResizeLeft"
    ></div>

    <!-- Main Content -->
    <div class="main-content">
      <!-- Top Controls (when sidebar closed) -->
      <div v-if="!isSidebarOpen" class="top-controls">
        <button
          class="open-sidebar-btn"
          @click="toggleSidebar"
          title="Ouvrir le menu"
        >
          <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path d="M3 12h18M3 6h18M3 18h18"/>
          </svg>
        </button>
        <ThemeToggle />
      </div>

       <!-- Monitoring Button (Always visible on top right or somewhere accessible) -->
       <!-- Since TopControls is only when sidebar closed, we might want it elsewhere or duplicate/move. 
            For now, let's put it absolute top-right of main content. -->
       <div class="monitoring-control">
          <button @click="toggleMonitoring" class="icon-btn" title="Monitoring backend">
             <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
               <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
             </svg>
          </button>
       </div>

      <!-- Monitoring Modal -->
      <div v-if="showMonitoring" class="monitoring-modal">
        <div class="monitoring-content">
          <div class="monitoring-header">
            <h3>Backend Status</h3>
            <button @click="toggleMonitoring" class="close-btn">&times;</button>
          </div>
          <div v-if="monitoringStats" class="stats-grid">
             <div class="stat-card">
               <div class="stat-label">Uptime</div>
               <div class="stat-value">{{ monitoringStats.uptime }}</div>
             </div>
             <div class="stat-card">
               <div class="stat-label">Total Requests</div>
               <div class="stat-value">{{ monitoringStats.total_requests }}</div>
             </div>
             <div class="stat-card">
               <div class="stat-label">Avg Latency</div>
               <div class="stat-value">{{ monitoringStats.avg_response_time_ms }} ms</div>
             </div>
             <div class="stat-card error-card">
               <div class="stat-label">Errors (5xx)</div>
               <div class="stat-value">{{ monitoringStats.error_rate_5xx }}</div>
             </div>
          </div>
          <div v-if="monitoringStats" class="endpoints-list">
             <h4>Active Endpoints</h4>
             <div v-for="(count, endpoint) in monitoringStats.requests_by_endpoint" :key="endpoint" class="endpoint-row">
                <span class="endpoint-name">{{ endpoint }}</span>
                <span class="endpoint-count">{{ count }}</span>
             </div>
          </div>
          <div v-else class="loading-stats">Loading...</div>
        </div>
      </div>

      <!-- Chat Content -->
      <router-view
        @message-received="onMessageReceived"
        @is-loading="handleLoading"
      ></router-view>
    </div>

    <!-- Right Resizer -->
    <div 
      v-if="isDocumentSidebarOpen"
      class="resizer right-resizer" 
      @mousedown="startResizeRight"
    ></div>

    <!-- Right Sidebar -->
    <DocumentSidebar 
      :is-open="isDocumentSidebarOpen" 
      :width="documentSidebarWidth" 
      :html-content="bailHtml" 
      :is-loading="isAiLoading" 
    />
  </div>
</template>

<style scoped>
.admin-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background-color: var(--color-background);
  font-family: 'DM Sans', -apple-system, sans-serif;
  transition: background-color 0.3s ease;
}

.main-content {
  flex: 1;
  height: 100%;
  position: relative;
  min-width: 0;
}

.top-controls {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 100;
  display: flex;
  gap: 8px;
  align-items: center;
}

.monitoring-control {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 100;
}

.icon-btn {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  color: var(--color-ink);
  cursor: pointer;
  padding: 8px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.icon-btn:hover {
  background-color: var(--color-cream);
  color: var(--color-accent);
}

.monitoring-modal {
  position: absolute;
  top: 60px;
  right: 16px;
  width: 350px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  z-index: 200;
  padding: 16px;
  max-height: 80vh;
  overflow-y: auto;
}

.monitoring-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 8px;
}
.monitoring-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}
.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--color-ink-light);
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  background: var(--color-background);
  padding: 10px;
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.stat-label {
  font-size: 12px;
  color: var(--color-ink-light);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-accent);
}

.endpoints-list h4 {
  font-size: 14px;
  margin: 0 0 8px 0;
}

.endpoint-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  padding: 4px 0;
  border-bottom: 1px solid var(--color-border-light);
}
.endpoint-name {
  color: var(--color-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}
.endpoint-count {
  font-weight: 600;
}

.open-sidebar-btn {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  color: var(--color-ink);
  cursor: pointer;
  padding: 10px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(26, 26, 46, 0.08);
}

.open-sidebar-btn:hover {
  background-color: var(--color-cream);
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.resizer {
  width: 6px;
  background-color: transparent;
  cursor: col-resize;
  height: 100%;
  z-index: 10;
  transition: background-color 0.2s;
  position: relative;
}

.resizer::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 4px;
  height: 48px;
  background: var(--color-cream-dark);
  border-radius: 2px;
  transition: background-color 0.2s;
}

.resizer:hover::before,
.resizer:active::before {
  background-color: var(--color-accent);
}

.left-resizer {
  margin-left: -3px;
}

.right-resizer {
  margin-right: -3px;
}

/* Mobile responsive */
@media (max-width: 1024px) {
  .admin-container {
    flex-direction: column;
  }
}
</style>