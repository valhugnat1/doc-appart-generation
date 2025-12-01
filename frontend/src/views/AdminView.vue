<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from '../components/Sidebar.vue'
import RightSidebar from '../components/RightSidebar.vue'
import ThemeToggle from '../components/ThemeToggle.vue'
import { API_BASE_URL } from '@/config.js'

const route = useRoute()
const isSidebarOpen = ref(true)
const isRightSidebarOpen = ref(false)
const bailHtml = ref('')
const isAiLoading = ref(false)
const sidebarRef = ref(null)

const leftSidebarWidth = ref(280)
const rightSidebarWidth = ref(600)
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
      rightSidebarWidth.value = newWidth
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
        isRightSidebarOpen.value = true
      }
    } else {
      isRightSidebarOpen.value = false
      bailHtml.value = ''
    }
  } catch (error) {
    console.error('Error fetching bail:', error)
    isRightSidebarOpen.value = false
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
    isRightSidebarOpen.value = false
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
    isRightSidebarOpen.value = true
  }
}
</script>

<template>
  <div class="admin-container">
    <!-- Left Sidebar -->
    <Sidebar 
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

      <!-- Chat Content -->
      <router-view
        @message-received="onMessageReceived"
        @is-loading="handleLoading"
      ></router-view>
    </div>

    <!-- Right Resizer -->
    <div 
      v-if="isRightSidebarOpen"
      class="resizer right-resizer" 
      @mousedown="startResizeRight"
    ></div>

    <!-- Right Sidebar -->
    <RightSidebar 
      :is-open="isRightSidebarOpen" 
      :width="rightSidebarWidth" 
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