<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { API_BASE_URL } from '@/config.js'
import ThemeToggle from './ThemeToggle.vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: true
  },
  width: {
    type: Number,
    default: 280
  },
  baseRoute: {
    type: String,
    default: '/admin/chat'
  }
})

const emit = defineEmits(['toggle'])

const router = useRouter()
const route = useRoute()
const conversations = ref([])
const isLoading = ref(false)

const fetchConversations = async () => {
  isLoading.value = true
  try {
    const response = await fetch(`${API_BASE_URL}/conversations`)
    if (response.ok) {
      const data = await response.json()
      conversations.value = data.conversations
    }
  } catch (error) {
    console.error('Error fetching conversations:', error)
  } finally {
    isLoading.value = false
  }
}

const createNewChat = () => {
  const uuid = crypto.randomUUID()
  router.push(`${props.baseRoute}/${uuid}`)
}

const selectConversation = (id) => {
  router.push(`${props.baseRoute}/${id}`)
}

const toggleSidebar = () => {
  emit('toggle')
}

const isActive = (id) => {
  return route.params.id === id
}

defineExpose({ fetchConversations })

onMounted(() => {
  fetchConversations()
})
</script>

<template>
  <div class="sidebar" v-show="isOpen">
    <!-- Logo -->
    <div class="sidebar-brand">
      <div class="logo">
        <div class="logo-icon">
          <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <path d="M14 2v6h6"/>
            <path d="M16 13H8"/>
            <path d="M16 17H8"/>
            <path d="M10 9H8"/>
          </svg>
        </div>
        <span class="logo-text">BailAssist</span>
      </div>
      <div class="sidebar-controls">
        <ThemeToggle />
        <button class="close-btn" @click="toggleSidebar" title="Fermer">
          <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- New Chat Button -->
    <div class="sidebar-actions">
      <button class="new-chat-btn" @click="createNewChat">
        <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path d="M12 5v14M5 12h14"/>
        </svg>
        Nouveau bail
      </button>
    </div>
    
    <!-- Conversations List -->
    <div class="conversations-section">
      <h3 class="section-title">Conversations récentes</h3>
      <div class="conversations-list">
        <div v-if="isLoading" class="loading">
          <div class="spinner"></div>
          Chargement...
        </div>
        <div v-else-if="conversations.length === 0" class="empty-list">
          <p>Aucune conversation</p>
        </div>
        <div 
          v-else
          v-for="conv in conversations" 
          :key="conv.id" 
          class="conversation-item"
          :class="{ 'active': isActive(conv.id) }"
          @click="selectConversation(conv.id)"
        >
          <div class="conversation-icon">
            <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <div class="conversation-info">
            <span class="title">{{ conv.title || 'Nouvelle conversation' }}</span>
            <span class="date">{{ new Date(conv.updated_at * 1000).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="sidebar-footer">
      <a href="/" class="footer-link">
        <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9,22 9,12 15,12 15,22"/>
        </svg>
        Retour à l'accueil
      </a>
    </div>
  </div>
</template>

<style scoped>
.sidebar {
  width: v-bind(width + 'px');
  height: 100vh;
  background: var(--color-surface);
  display: flex;
  flex-direction: column;
  color: var(--color-ink);
  border-right: 1px solid var(--color-border);
  font-family: 'DM Sans', -apple-system, sans-serif;
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.sidebar-brand {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--color-border);
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--color-accent), var(--color-accent-dark));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.logo-text {
  font-family: 'Fraunces', Georgia, serif;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-ink);
}

.sidebar-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.close-btn {
  background: transparent;
  border: none;
  color: var(--color-ink-muted);
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background-color: var(--color-cream);
  color: var(--color-ink);
}

.sidebar-actions {
  padding: 16px;
}

.new-chat-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px 20px;
  background: linear-gradient(135deg, var(--color-accent), var(--color-accent-dark));
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
}

.new-chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.35);
}

.conversations-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0 16px;
}

.section-title {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-ink-muted);
  margin-bottom: 12px;
  padding: 0 4px;
}

.conversations-list {
  flex: 1;
  overflow-y: auto;
  margin: 0 -16px;
  padding: 0 16px;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 20px;
  color: var(--color-ink-muted);
  font-size: 0.9rem;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-cream-dark);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-list {
  text-align: center;
  padding: 40px 20px;
  color: var(--color-ink-muted);
  font-size: 0.9rem;
}

.conversation-item {
  padding: 12px 16px;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.conversation-item:hover {
  background-color: var(--color-cream);
}

.conversation-item.active {
  background-color: var(--color-accent-light);
  border-color: var(--color-accent);
}

.conversation-item.active .conversation-icon {
  color: var(--color-accent);
}

.conversation-icon {
  width: 32px;
  height: 32px;
  background: var(--color-cream);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-ink-muted);
  flex-shrink: 0;
}

.conversation-item.active .conversation-icon {
  background: var(--color-surface);
}

.conversation-info {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-ink);
}

.date {
  font-size: 0.75rem;
  color: var(--color-ink-muted);
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--color-border);
}

.footer-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 10px;
  color: var(--color-ink-light);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s;
}

.footer-link:hover {
  background-color: var(--color-cream);
  color: var(--color-accent);
}

/* Scrollbar styling */
.conversations-list::-webkit-scrollbar {
  width: 6px;
}

.conversations-list::-webkit-scrollbar-track {
  background: transparent;
}

.conversations-list::-webkit-scrollbar-thumb {
  background: var(--color-cream-dark);
  border-radius: 3px;
}

.conversations-list::-webkit-scrollbar-thumb:hover {
  background: var(--color-ink-muted);
}
</style>