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
  padding: 14px 20px;
  background: linear-gradient(135deg, var(--color-accent-light, #dbeafe), #ede9fe);
  border: 1px solid rgba(37, 99, 235, 0.2);
  border-radius: 14px;
  margin-top: 12px;
  font-size: 14px;
  color: var(--color-ink, #1a1a2e);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(37, 99, 235, 0.2);
  border-radius: 50%;
  border-top-color: var(--color-accent, #2563eb);
  animation: spin 1s linear infinite;
  flex-shrink: 0;
}

.content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.label {
  font-size: 0.75rem;
  color: var(--color-ink-muted, #7a7a8a);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 500;
}

.name {
  font-family: 'Menlo', 'Monaco', monospace;
  font-weight: 600;
  font-size: 0.9rem;
  color: #7c3aed;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>