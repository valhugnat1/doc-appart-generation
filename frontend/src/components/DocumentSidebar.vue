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
    <div class="sidebar-header">
      <div class="header-left">
        <div class="header-icon">
          <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <path d="M14 2v6h6"/>
            <path d="M16 13H8"/>
            <path d="M16 17H8"/>
          </svg>
        </div>
        <div class="header-text">
          <h2>Aperçu du bail</h2>
          <p>Document en cours de génération</p>
        </div>
      </div>

      <div v-if="htmlContent && !isLoading" class="header-actions">
        <button class="action-btn secondary" title="Aperçu plein écran">
          <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        </button>
        <button class="action-btn primary">
          <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7,10 12,15 17,10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          <span>PDF</span>
        </button>
      </div>
    </div>

    <div class="sidebar-content">
      <div v-if="htmlContent || isLoading" class="preview-container">
        <div v-if="htmlContent" class="document-wrapper" :class="{ 'content-blurred': isLoading }">
          <div class="document-content" v-html="htmlContent"></div>
        </div>
        <div v-if="isLoading" class="loading-overlay">
          <div class="loading-card">
            <div class="refresh-spinner"></div>
            <p>Mise à jour du document...</p>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">
        <div class="empty-icon">📄</div>
        <h3>Aucun document</h3>
        <p>Le bail apparaîtra ici au fur et à mesure de la conversation</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.right-sidebar {
  width: 0;
  background-color: var(--color-background);
  border-left: 1px solid var(--color-border);
  transition: width 0.3s ease, background-color 0.3s ease, border-color 0.3s ease;
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
  font-family: 'DM Sans', -apple-system, sans-serif;
}

.right-sidebar.is-open {
  width: v-bind(width + 'px');
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  transition: background-color 0.3s ease, border-color 0.3s ease;
  min-height: 80px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.header-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #7c3aed, #a78bfa);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.header-text h2 {
  font-family: 'Fraunces', Georgia, serif;
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--color-ink);
  margin: 0 0 4px 0;
}

.header-text p {
  font-size: 0.85rem;
  color: var(--color-ink-muted);
  margin: 0;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  /* Top 24px, Sides 24px, Bottom 15% of viewport height */
  padding: 24px 24px 15vh 24px; 
}

.preview-container {
  position: relative;
  min-height: 100%;
}

.document-wrapper {
  background: var(--color-surface);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(26, 26, 46, 0.08);
  overflow: hidden;
  transition: filter 0.3s, background-color 0.3s ease;
}

.document-content {
  padding: 40px;
}

.content-blurred {
  filter: blur(3px);
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
  align-items: flex-start;
  padding-top: 100px;
}

.loading-card {
  background: var(--color-surface);
  padding: 32px 48px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(26, 26, 46, 0.15);
  text-align: center;
  transition: background-color 0.3s ease;
}

.refresh-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--color-cream-dark);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-card p {
  color: var(--color-ink-light);
  font-size: 0.95rem;
  margin: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 400px;
  text-align: center;
  padding: 40px;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 24px;
  opacity: 0.5;
}

.empty-state h3 {
  font-family: 'Fraunces', Georgia, serif;
  font-size: 1.5rem;
  font-weight: 500;
  color: var(--color-ink);
  margin: 0 0 12px 0;
}

.empty-state p {
  color: var(--color-ink-muted);
  font-size: 0.95rem;
  max-width: 280px;
  margin: 0;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  white-space: nowrap;
}

.action-btn.primary {
  background: linear-gradient(135deg, var(--color-accent), var(--color-accent-dark));
  color: white;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
}

.action-btn.primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
}

.action-btn.secondary {
  background: var(--color-cream);
  color: var(--color-ink);
  border: 1px solid var(--color-border);
  padding: 8px;
}

.action-btn.secondary:hover {
  border-color: var(--color-ink-muted);
  background: var(--color-surface);
}

/* Document content styling */
:deep(.document-content h1) {
  font-family: 'Fraunces', Georgia, serif;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-ink);
  text-align: center;
  margin-bottom: 8px;
}

:deep(.document-content h2) {
  font-family: 'Fraunces', Georgia, serif;
  font-size: 1.1rem;
  font-weight: 500;
  color: var(--color-ink);
  margin: 24px 0 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--color-accent);
}

:deep(.document-content p) {
  font-size: 0.9rem;
  line-height: 1.7;
  color: var(--color-ink);
  margin-bottom: 12px;
}

:deep(.document-content ul),
:deep(.document-content ol) {
  padding-left: 24px;
  margin-bottom: 16px;
}

:deep(.document-content li) {
  font-size: 0.9rem;
  line-height: 1.6;
  margin-bottom: 6px;
}

.sidebar-content::-webkit-scrollbar {
  width: 8px;
}

.sidebar-content::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-content::-webkit-scrollbar-thumb {
  background: var(--color-cream-dark);
  border-radius: 4px;
}

.sidebar-content::-webkit-scrollbar-thumb:hover {
  background: var(--color-ink-muted);
}
</style>