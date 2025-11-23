<script setup>
import { ref } from 'vue'
import Sidebar from './components/Sidebar.vue'
import RightSidebar from './components/RightSidebar.vue'

const isSidebarOpen = ref(true)
const isRightSidebarOpen = ref(false)
const bailHtml = ref('')

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value
}

const fetchBail = async (conversationId) => {
  if (!conversationId) return
  
  try {
    const response = await fetch(`http://localhost:8000/bail/${conversationId}`)
    if (response.ok) {
      const data = await response.json()
      bailHtml.value = data.html
      // Open the right sidebar if we have content
      if (bailHtml.value) {
        isRightSidebarOpen.value = true
      }
    } else {
      // If 404 or other error, maybe just clear or keep previous?
      // User said: "it's only when the html file is available in the API the side bar display the doc"
      // So if not available, maybe close it or do nothing?
      // Let's keep it simple: if error, assume no bail yet.
      console.log('Bail not found or error fetching')
    }
  } catch (error) {
    console.error('Error fetching bail:', error)
  }
}

const onMessageReceived = (conversationId) => {
  fetchBail(conversationId)
}
</script>

<template>
  <div class="app-container">
    <Sidebar :is-open="isSidebarOpen" @toggle="toggleSidebar" />
    <div class="main-content">
      <button 
        v-if="!isSidebarOpen" 
        class="open-sidebar-btn"
        @click="toggleSidebar"
        title="Open sidebar"
      >
        ▶
      </button>
      <router-view @message-received="onMessageReceived"></router-view>
    </div>
    <RightSidebar :is-open="isRightSidebarOpen" :html-content="bailHtml" />
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
</style>
