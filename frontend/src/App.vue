<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import RightSidebar from './components/RightSidebar.vue'
import { API_BASE_URL } from '@/config.js'

const route = useRoute()
const isSidebarOpen = ref(true)
const isRightSidebarOpen = ref(false)
const bailHtml = ref('')
const isAiLoading = ref(false)
const sidebarRef = ref(null)

const leftSidebarWidth = ref(260)
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
    if (newWidth > 150 && newWidth < 600) {
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
  // Refresh the conversation list to show the new conversation
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
  <div class="app-container">
    <Sidebar ref="sidebarRef" :is-open="isSidebarOpen" :width="leftSidebarWidth" @toggle="toggleSidebar" />
    <div 
      v-if="isSidebarOpen"
      class="resizer left-resizer" 
      @mousedown="startResizeLeft"
    ></div>
    <div class="main-content">
      <button 
        v-if="!isSidebarOpen" 
        class="open-sidebar-btn"
        @click="toggleSidebar"
        title="Open sidebar"
      >
        ▶
      </button>
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

<style>
body {
  margin: 0;
  padding: 0;
}

.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.main-content {
  flex: 1;
  height: 100%;
  position: relative;
}

.open-sidebar-btn {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 100;
  background: rgba(32,33,35,0.8);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 5px;
  color: #ececf1;
  cursor: pointer;
  padding: 8px 12px;
  transition: background-color 0.2s;
}

.open-sidebar-btn:hover {
  background-color: rgba(255,255,255,0.1);
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

.left-resizer {
  border-right: 1px solid rgba(255,255,255,0.1);
}

.right-resizer {
  border-left: 1px solid #e5e5e5;
}
</style>
