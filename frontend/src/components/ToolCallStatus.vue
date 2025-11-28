<script setup>
defineProps({
  toolName: {
    type: String,
    required: true
  }
})
</script>

<template>
  <div class="tool-call-status">
    <div class="spinner"></div>
    <div class="content">
      <span class="label">Using tool:</span>
      <span class="name">{{ toolName }}</span>
    </div>
  </div>
</template>

<style scoped>
.tool-call-status {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  margin-top: 8px;
  font-size: 14px;
  color: #ececf1;
  width: fit-content;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s linear infinite;
}

.content {
  display: flex;
  gap: 6px;
  align-items: center;
}

.label {
  color: #8e8ea0;
}

.name {
  font-family: 'Menlo', monospace;
  font-weight: 600;
  color: #10a37f;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
