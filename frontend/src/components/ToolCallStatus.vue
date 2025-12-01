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
      <span class="label">Utilisation de l'outil</span>
      <span class="name">{{ toolName }}</span>
    </div>
  </div>
</template>

<style scoped>
.tool-call-status {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  padding: 12px 20px;
  /* Deep dark background (Midnight/Slate) */
  background: #0f172a; 
  /* Subtle border with slight transparency */
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  margin-top: 12px;
  /* Light text for contrast */
  color: #e2e8f0;
  /* Subtle drop shadow for depth */
  box-shadow: 
    0 4px 6px -1px rgba(0, 0, 0, 0.3), 
    0 2px 4px -1px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.spinner {
  width: 18px;
  height: 18px;
  /* Faint white track */
  border: 2px solid rgba(255, 255, 255, 0.15);
  border-radius: 50%;
  /* Bright Neon Purple for the active part */
  border-top-color: #a78bfa;
  animation: spin 1s linear infinite;
  flex-shrink: 0;
  box-shadow: 0 0 8px rgba(167, 139, 250, 0.2);
}

.content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.2;
}

.label {
  font-size: 0.7rem;
  /* Muted silver text */
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 600;
}

.name {
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-weight: 600;
  font-size: 0.85rem;
  /* Bright Violet/White for the function name */
  color: #e9d5ff;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>