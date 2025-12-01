<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import RightSidebar from '../components/RightSidebar.vue'
import ThemeToggle from '../components/ThemeToggle.vue'
import { API_BASE_URL } from '@/config.js'
import Cookies from 'js-cookie'

const route = useRoute()
const router = useRouter()
const isRightSidebarOpen = ref(false)
const bailHtml = ref('')
const isAiLoading = ref(false)

const rightSidebarWidth = ref(600)
const isResizingRight = ref(false)

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
}

const handleLoading = (loading) => {
  isAiLoading.value = loading
  if (loading) {
    isRightSidebarOpen.value = true
  }
}

const startNewConversation = () => {
  const newUuid = crypto.randomUUID()
  Cookies.set('session_uuid', newUuid, { expires: 7 })
  router.push(`/chat/${newUuid}`)
}

onMounted(() => {
  const sessionUuid = Cookies.get('session_uuid')
  if (!sessionUuid) {
    startNewConversation()
  } else if (!route.params.id) {
     router.push(`/chat/${sessionUuid}`)
  } else {
    fetchBail(route.params.id)
  }
})
</script>

<template>
  <div class="public-container">
    <div class="main-content">
      <!-- Header -->
      <header class="header">
        <a href="/" class="logo">
          <div class="logo-icon">
            <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <path d="M14 2v6h6"/>
              <path d="M16 13H8"/>
              <path d="M16 17H8"/>
            </svg>
          </div>
          <span class="logo-text">BailAssist</span>
        </a>
        
        <div class="header-actions">
          <ThemeToggle />
          <button @click="startNewConversation" class="new-conv-btn">
            <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path d="M12 5v14M5 12h14"/>
            </svg>
            Nouveau bail
          </button>
        </div>
      </header>

      <!-- Chat Content -->
      <div class="chat-wrapper">
        <router-view @message-received="onMessageReceived" @is-loading="handleLoading"></router-view>
      </div>
    </div>

    <!-- Resizer -->
    <div 
      v-if="isRightSidebarOpen"
      class="resizer" 
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
.public-container {
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
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  z-index: 10;
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--color-accent), var(--color-accent-dark));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.logo-text {
  font-family: 'Fraunces', Georgia, serif;
  font-size: 1.35rem;
  font-weight: 600;
  color: var(--color-ink);
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.new-conv-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: linear-gradient(135deg, var(--color-accent), var(--color-accent-dark));
  color: white;
  border: none;
  border-radius: 100px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
}

.new-conv-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.35);
}

.chat-wrapper {
  flex: 1;
  overflow: hidden;
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

/* Mobile responsive */
@media (max-width: 768px) {
  .header {
    padding: 12px 16px;
  }

  .logo-text {
    font-size: 1.1rem;
  }

  .new-conv-btn span {
    display: none;
  }

  .new-conv-btn {
    padding: 10px;
    border-radius: 10px;
  }
}
</style>