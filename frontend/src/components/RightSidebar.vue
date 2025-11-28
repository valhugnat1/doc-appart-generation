<script setup>
import { defineProps } from 'vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  htmlContent: {
    type: String,
    default: ''
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  width: {
    type: Number,
    default: 600
  }
})
</script>

<template>
  <div class="right-sidebar" :class="{ 'is-open': isOpen }">
    <div class="sidebar-content">
      <div v-if="htmlContent || isLoading" class="preview-container">
        <div v-if="htmlContent" :class="{ 'content-blurred': isLoading }" v-html="htmlContent"></div>
        <div v-if="isLoading" class="loading-overlay">
          <div class="refresh-spinner"></div>
        </div>
      </div>
      <div v-else class="empty-state">
        <p>No document generated yet.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.right-sidebar {
  width: 0;
  background-color: #f9f9f9;
  border-left: 1px solid #e5e5e5;
  transition: width 0.3s ease;
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.right-sidebar.is-open {
  width: v-bind(width + 'px');
}

.sidebar-content {
  padding: 20px;
  overflow-y: auto;
  height: 80%;
}

.preview-container {
  background: white;
  padding: 20px;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
  min-height: 100%;
  position: relative;
}

.content-blurred {
  filter: blur(4px);
  pointer-events: none;
  user-select: none;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  /* z-index: 10; */
}

.refresh-spinner {
  width: 50px;
  height: 50px;
  border: 5px solid #f3f3f3;
  border-top: 5px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #888;
}
</style>
