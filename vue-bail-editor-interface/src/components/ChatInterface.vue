<script setup>
import { ref, nextTick, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const router = useRouter()

const props = defineProps({
  conversationId: {
    type: String,
    default: null
  }
})

const messages = ref([])
const userInput = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const isCreatingConversation = ref(false)

const renderMarkdown = (content) => {
  if (!content) return ''
  const html = marked.parse(content)
  return DOMPurify.sanitize(html)
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const loadConversation = async () => {
  // If we are in the process of creating a conversation, don't reload (which would clear messages)
  if (isCreatingConversation.value) {
    isCreatingConversation.value = false
    return
  }

  if (!props.conversationId) {
    messages.value = []
    return
  }

  isLoading.value = true
  try {
    const response = await fetch(`http://localhost:8000/conversations/${props.conversationId}`)
    if (response.ok) {
      const data = await response.json()
      if (data.messages && data.messages.length > 0) {
        messages.value = data.messages
      } else {
        messages.value = []
      }
    }
  } catch (error) {
    console.error('Error loading conversation:', error)
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}

watch(() => props.conversationId, () => {
  loadConversation()
})

onMounted(() => {
  loadConversation()
})

const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return

  const userMessage = { role: 'user', content: userInput.value }
  messages.value.push(userMessage)
  userInput.value = ''
  isLoading.value = true
  await scrollToBottom()

  let currentConversationId = props.conversationId
  if (!currentConversationId) {
    // Generate new UUID
    currentConversationId = crypto.randomUUID()
    // Mark that we are creating a conversation so the watcher doesn't clear our messages
    isCreatingConversation.value = true
    // Update URL
    router.replace(`/chat/${currentConversationId}`)
  }

  try {
    const response = await fetch('http://localhost:8000/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        messages: messages.value,
        user: currentConversationId
      })
    })

    if (!response.ok) {
      throw new Error('Network response was not ok')
    }

    const data = await response.json()
    const assistantMessage = data.choices[0].message
    messages.value.push(assistantMessage)
    
    // Trigger sidebar refresh if possible (not easily accessible here without global state/bus)
    // Ideally we would emit an event or use a store. 
    // For now, the user will see it in the sidebar on refresh or next load.
    
  } catch (error) {
    console.error('Error:', error)
    messages.value.push({ role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' })
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}
</script>

<template>
  <div class="chat-container">
    <div class="messages" ref="messagesContainer">
      <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
        <div class="message-content">
          <div class="avatar">
            {{ msg.role === 'user' ? '👤' : '🤖' }}
          </div>
          <div class="text markdown-body" v-html="renderMarkdown(msg.content)"></div>
        </div>
      </div>
      <div v-if="isLoading" class="message assistant">
        <div class="message-content">
          <div class="avatar">🤖</div>
          <div class="text typing-indicator">
            <span>.</span><span>.</span><span>.</span>
          </div>
        </div>
      </div>
    </div>
    <div class="input-area">
      <div class="input-wrapper">
        <textarea 
          v-model="userInput" 
          @keydown.enter.prevent="sendMessage"
          placeholder="Send a message..."
          rows="1"
        ></textarea>
        <button @click="sendMessage" :disabled="!userInput.trim() || isLoading">
          ➤
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #343541;
  color: #ececf1;
  font-family: 'Söhne', 'ui-sans-serif', 'system-ui', -apple-system, 'Segoe UI', Roboto, Ubuntu, Cantarell, 'Noto Sans', sans-serif, 'Helvetica Neue', Arial, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji';
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 150px;
}

.message {
  padding: 24px 0;
  border-bottom: 1px solid rgba(0,0,0,0.1);
}

.message.assistant {
  background-color: #444654;
}

.message-content {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  gap: 20px;
  padding: 0 20px;
}

.avatar {
  width: 30px;
  height: 30px;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.text {
  flex: 1;
  line-height: 1.6;
  overflow-wrap: break-word;
}

/* Markdown Styles */
:deep(.markdown-body) {
  font-size: 16px;
  line-height: 1.6;
}

:deep(.markdown-body p) {
  margin-bottom: 1em;
}

:deep(.markdown-body p:last-child) {
  margin-bottom: 0;
}

:deep(.markdown-body pre) {
  background-color: #000;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  margin-bottom: 1em;
}

:deep(.markdown-body code) {
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  background-color: rgba(255, 255, 255, 0.1);
  padding: 2px 4px;
  border-radius: 3px;
}

:deep(.markdown-body pre code) {
  background-color: transparent;
  padding: 0;
}

:deep(.markdown-body ul), :deep(.markdown-body ol) {
  margin-bottom: 1em;
  padding-left: 20px;
}

:deep(.markdown-body h1), :deep(.markdown-body h2), :deep(.markdown-body h3), :deep(.markdown-body h4), :deep(.markdown-body h5), :deep(.markdown-body h6) {
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  font-weight: 600;
}

:deep(.markdown-body a) {
  color: #10a37f;
  text-decoration: none;
}

:deep(.markdown-body a:hover) {
  text-decoration: underline;
}

.input-area {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  background-image: linear-gradient(180deg, rgba(53,55,64,0), #353740 58.85%);
  padding: 20px 0 40px;
}

.input-wrapper {
  max-width: 800px;
  margin: 0 auto;
  position: relative;
  padding: 0 20px;
}

textarea {
  width: 100%;
  background-color: #40414f;
  border: 1px solid rgba(32,33,35,0.5);
  border-radius: 12px;
  color: #fff;
  padding: 12px 45px 12px 16px;
  font-family: inherit;
  font-size: 16px;
  line-height: 1.5;
  resize: none;
  outline: none;
  box-shadow: 0 0 15px rgba(0,0,0,0.1);
}

textarea:focus {
  border-color: rgba(32,33,35,0.5);
  box-shadow: 0 0 20px rgba(0,0,0,0.2);
}

button {
  position: absolute;
  right: 30px;
  bottom: 15px;
  background: transparent;
  border: none;
  color: #ececf1;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

button:hover:not(:disabled) {
  background-color: #202123;
}

button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.typing-indicator span {
  animation: blink 1.4s infinite both;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes blink {
  0% { opacity: 0.2; }
  20% { opacity: 1; }
  100% { opacity: 0.2; }
}
</style>
