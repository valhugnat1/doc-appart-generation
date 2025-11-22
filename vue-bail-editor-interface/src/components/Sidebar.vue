<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['toggle'])

const router = useRouter()
const conversations = ref([])
const isLoading = ref(false)

const fetchConversations = async () => {
  isLoading.value = true
  try {
    const response = await fetch('http://localhost:8000/conversations')
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
  router.push('/')
}

const selectConversation = (id) => {
  router.push(`/chat/${id}`)
}

const toggleSidebar = () => {
  emit('toggle')
}

// Expose fetchConversations so parent or siblings can trigger refresh if needed
defineExpose({ fetchConversations })

onMounted(() => {
  fetchConversations()
})
</script>

<template>
  <div class="sidebar" v-show="isOpen">
    <div class="sidebar-header">
      <div class="new-chat-btn" @click="createNewChat">
        + New chat
      </div>
      <button class="close-btn" @click="toggleSidebar" title="Close sidebar">
        ◀
      </button>
    </div>
    
    <div class="conversations-list">
      <div v-if="isLoading" class="loading">Loading...</div>
      <div 
        v-else
        v-for="conv in conversations" 
        :key="conv.id" 
        class="conversation-item"
        @click="selectConversation(conv.id)"
      >
        <span class="icon">💬</span>
        <div class="conversation-info">
          <span class="title">{{ conv.title || conv.id }}</span>
          <span class="date">{{ new Date(conv.updated_at * 1000).toLocaleString() }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sidebar {
  width: 260px;
  height: 100vh;
  background-color: #202123;
  display: flex;
  flex-direction: column;
  color: #ececf1;
  padding: 10px;
  box-sizing: border-box;
  border-right: 1px solid rgba(255,255,255,0.1);
}

.sidebar-header {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.new-chat-btn {
  flex: 1;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 5px;
  padding: 10px;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  gap: 10px;
  white-space: nowrap;
}

.new-chat-btn:hover {
  background-color: rgba(255,255,255,0.1);
}

.close-btn {
  background: transparent;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 5px;
  color: #ececf1;
  cursor: pointer;
  padding: 0 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background-color: rgba(255,255,255,0.1);
}

.conversations-list {
  flex: 1;
  overflow-y: auto;
}

.conversation-item {
  padding: 10px;
  border-radius: 5px;
  cursor: pointer;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 2px;
}

.conversation-item:hover {
  background-color: #2A2B32;
}

.conversation-info {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.icon {
  font-size: 1.2em;
  margin-top: 2px;
}

.title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.9em;
}

.date {
  font-size: 0.7em;
  color: #8e8ea0;
}
</style>
