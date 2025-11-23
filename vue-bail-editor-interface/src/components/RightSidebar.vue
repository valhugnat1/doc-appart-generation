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
  }
})
</script>

<template>
  <div class="right-sidebar" :class="{ 'is-open': isOpen }">
    <div class="sidebar-content">
      <div v-if="htmlContent" class="preview-container" v-html="htmlContent"></div>
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
  width: 50%; /* Adjust width as needed */
}

.sidebar-content {
  padding: 20px;
  overflow-y: auto;
  height: 100%;
}

.preview-container {
  background: white;
  padding: 20px;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
  min-height: 100%;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #888;
}
</style>
