<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import RightSidebar from '../components/RightSidebar.vue'
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
      // Open the right sidebar if we have content
      if (bailHtml.value) {
        isRightSidebarOpen.value = true
      }
    } else {
      // If 404 or other error, close the sidebar
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
  Cookies.set('session_uuid', newUuid, { expires: 7 }) // Expires in 7 days
  router.push(`/chat/${newUuid}`)
}

onMounted(() => {
  // Check for existing session
  const sessionUuid = Cookies.get('session_uuid')
  if (!sessionUuid) {
    startNewConversation()
  } else if (!route.params.id) {
     router.push(`/chat/${sessionUuid}`)
  } else {
    // If we have an ID in the URL, fetch the bail
    fetchBail(route.params.id)
  }
})
</script>

<template>
  <div class="public-container">
    <div class="main-content">
      <div class="header">
        <button @click="startNewConversation" class="new-conv-btn">
          + Nouveau bail
        </button>
      </div>
      <router-view @message-received="onMessageReceived" @is-loading="handleLoading"></router-view>
    </div>
    <div 
      v-if="isRightSidebarOpen"
      class="resizer right-resizer" 
      @mousedown="startResizeRight"
    ></div>
    <RightSidebar :is-open="isRightSidebarOpen" :width="rightSidebarWidth" :html-content="bailHtml" :is-loading="isAiLoading" />
  </div>
</template>

<style scoped>
.public-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background-color: #343541; /* Match main background */
}

.main-content {
  flex: 1;
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
}

.header {
  padding: 10px;
  display: flex;
  justify-content: flex-start;
  background-color: #202123;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.new-conv-btn {
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 5px;
  color: #ececf1;
  cursor: pointer;
  padding: 8px 12px;
  transition: background-color 0.2s;
}

.new-conv-btn:hover {
  background-color: rgba(255,255,255,0.2);
}

.resizer {
  width: 5px;
  background-color: transparent;
  cursor: col-resize;
  height: 100%;
  z-index: 10;
  transition: background-color 0.2s;
}

.resizer:hover, .resizer:active {
  background-color: rgba(52, 152, 219, 0.5);
}

.right-resizer {
  border-left: 1px solid #e5e5e5;
}
</style>
