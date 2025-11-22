<script setup>
import { ref } from 'vue'
import Sidebar from './components/Sidebar.vue'

const isSidebarOpen = ref(true)

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value
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
      <router-view></router-view>
    </div>
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
