<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

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

onMounted(() => {
  fetchConversations()
})
</script>

<template>
  <div class="sidebar">
    <div class="new-chat-btn" @click="createNewChat">
      + New chat
    </div>
    <div class="conversations-list">
      <div v-if="isLoading" class="loading">Loading...</div>
      <div 
        v-else
        v-for="id in conversations" 
        :key="id" 
        class="conversation-item"
        @click="selectConversation(id)"
      >
        <span class="icon">💬</span>
        <span class="title">{{ id }}</span>
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
}

.new-chat-btn {
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 5px;
  padding: 10px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  gap: 10px;
}

.new-chat-btn:hover {
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
  align-items: center;
  gap: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conversation-item:hover {
  background-color: #2A2B32;
}

.icon {
  font-size: 1.2em;
}

.title {
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
