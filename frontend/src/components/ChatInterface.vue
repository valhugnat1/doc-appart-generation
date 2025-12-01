<script setup>
import { ref, nextTick, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import OpenAI from 'openai'
import ToolCallStatus from './ToolCallStatus.vue'
import { API_BASE_URL } from '@/config.js'

const router = useRouter()

const props = defineProps({
  conversationId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['message-received', 'is-loading'])

// State
const messages = ref([])
const userInput = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const textareaRef = ref(null)
const isCreatingConversation = ref(false)
const currentToolCall = ref(null)

// Markdown rendering
const renderMarkdown = (content) => {
  if (!content) return ''
  const html = marked.parse(content)
  return DOMPurify.sanitize(html)
}

// Scroll logic
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// Auto-resize textarea
const resizeTextarea = () => {
  const el = textareaRef.value
  if (el) {
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }
}

const handleInput = () => {
  resizeTextarea()
}

const handleKeyDown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
  // If Shift+Enter, let the default behavior happen (new line)
}

// Load Conversation History
const loadConversation = async () => {
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
    const response = await fetch(`${API_BASE_URL}/conversations/${props.conversationId}`)
    if (response.ok) {
      const data = await response.json()
      messages.value = data.messages || []
    }
  } catch (error) {
    console.error('Error loading conversation:', error)
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}

watch(() => props.conversationId, loadConversation)
watch(isLoading, (val) => emit('is-loading', val))

onMounted(() => {
  loadConversation()
  resizeTextarea()
})

const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return

  const content = userInput.value
  userInput.value = ''
  if (textareaRef.value) textareaRef.value.style.height = 'auto'
  
  messages.value.push({ role: 'user', content })
  isLoading.value = true
  await scrollToBottom()

  let currentConversationId = props.conversationId
  if (!currentConversationId) {
    currentConversationId = crypto.randomUUID()
    isCreatingConversation.value = true
    router.replace(`/chat/${currentConversationId}`)
  }

  try {
    const openai = new OpenAI({
      baseURL: `${API_BASE_URL}/v1`,
      apiKey: 'not-needed',
      dangerouslyAllowBrowser: true
    })

    messages.value.push({ role: 'assistant', content: '' })
    const lastMsgIndex = messages.value.length - 1

    const apiMessages = messages.value
      .slice(0, -1) 
      .map(m => ({ role: m.role, content: m.content }))

    const stream = await openai.chat.completions.create({
      model: 'claude-sonnet-4-5',
      messages: apiMessages,
      stream: true,
      temperature: 0.1,
      user: currentConversationId 
    })

    for await (const chunk of stream) {
      const delta = chunk.choices[0]?.delta
      
      if (delta?.tool_calls) {
        const toolCall = delta.tool_calls[0]
        if (toolCall.function?.name) {
          currentToolCall.value = { name: toolCall.function.name }
          await scrollToBottom()
        }
      }

      const content = delta?.content || ''
      
      if (content) {
        if (currentToolCall.value) {
          currentToolCall.value = null
        }
        messages.value[lastMsgIndex].content += content
        await scrollToBottom() 
      }
    }
    
    currentToolCall.value = null

    emit('message-received', currentConversationId)

  } catch (error) {
    console.error('Error sending message:', error)
    if (messages.value[messages.value.length - 1].content === '') {
       messages.value.pop()
    }
    messages.value.push({ 
      role: 'assistant', 
      content: 'Sorry, I encountered an error connecting to the server.' 
    })
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}
</script>

<template>
  <div class="chat-container">
    <div class="messages" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-state">
        <h1>How can I help you today?</h1>
      </div>
      
      <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
        <div class="message-content">
          <div class="avatar">
            {{ msg.role === 'user' ? '👤' : '🤖' }}
          </div>
          <div class="content-wrapper">
            <div class="text markdown-body" v-html="renderMarkdown(msg.content)"></div>
            <ToolCallStatus 
              v-if="index === messages.length - 1 && currentToolCall" 
              :toolName="currentToolCall.name" 
            />
          </div>
        </div>
      </div>
      
      <div v-if="isLoading && messages[messages.length - 1]?.role !== 'assistant'" class="message assistant">
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
          ref="textareaRef"
          v-model="userInput" 
          @input="handleInput"
          @keydown="handleKeyDown"
          placeholder="Send a message..."
          rows="1"
        ></textarea>
        <button @click="sendMessage" :disabled="!userInput.trim() || isLoading">
          <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" height="16" width="16" xmlns="http://www.w3.org/2000/svg"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
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
  font-family: 'Söhne', 'ui-sans-serif', system-ui, -apple-system, sans-serif;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 150px;
  scroll-behavior: smooth;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #fff;
  font-weight: 600;
  opacity: 0.8;
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
  align-items: flex-start; 
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
  margin-top: 2px; 
}

.content-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.text {
  line-height: 1.6;
  overflow-wrap: break-word;
  width: 100%;
}

:deep(.markdown-body) {
  font-size: 16px;
  line-height: 1.6;
  color: #ececf1;
}

:deep(.markdown-body p) { margin-bottom: 1em; }
:deep(.markdown-body p:last-child) { margin-bottom: 0; }
:deep(.markdown-body pre) {
  background-color: #000;
  padding: 15px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 1em 0;
}
:deep(.markdown-body code) {
  font-family: 'Menlo', monospace;
  background-color: rgba(255, 255, 255, 0.1);
  padding: 2px 4px;
  border-radius: 3px;
}
:deep(.markdown-body pre code) {
  background-color: transparent;
  padding: 0;
  border: none;
}
:deep(.markdown-body ul), :deep(.markdown-body ol) { margin-bottom: 1em; padding-left: 20px; }
:deep(.markdown-body a) { color: #10a37f; text-decoration: underline; }

.input-area {
  position: fixed;
  bottom: 0;
  left: 0; /* Ensure it stretches if inside a container, otherwise use width: 100% */
  right: 0; /* Better for layout than width 100% in flex containers */
  background-image: linear-gradient(180deg, rgba(53,55,64,0), #353740 50%);
  padding: 20px 0 40px;
  z-index: 20;
}

.input-wrapper {
  max-width: 800px;
  margin: 0 auto;
  position: relative;
  padding: 0 20px;
  background: #40414f;
  border-radius: 16px;
  box-shadow: 0 0 15px rgba(0,0,0,0.1);
  border: 1px solid rgba(32,33,35,0.5);
  display: flex;
  align-items: flex-end; /* Aligns button to bottom if textarea grows */
}

textarea {
  width: 100%;
  max-height: 200px;
  background-color: transparent;
  border: none;
  color: #fff;
  padding: 14px 40px 14px 10px;
  font-family: inherit;
  font-size: 16px;
  line-height: 1.5;
  resize: none;
  outline: none;
  overflow-y: hidden; /* Hidden until max-height reached */
}

/* Scrollbar for textarea if it gets too tall */
textarea:focus { overflow-y: auto; }

button {
  position: absolute;
  right: 10px;
  bottom: 8px;
  background: #19c37d;
  border: none;
  color: white;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

button:hover:not(:disabled) { background-color: #1a885d; }
button:disabled { background-color: transparent; color: #aaa; cursor: not-allowed; }

.typing-indicator span {
  animation: blink 1.4s infinite both;
  font-size: 24px;
  line-height: 10px;
  margin: 0 2px;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
  0% { opacity: 0.2; }
  20% { opacity: 1; }
  100% { opacity: 0.2; }
}
</style>