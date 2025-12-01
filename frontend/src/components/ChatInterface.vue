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
      content: 'Désolé, j\'ai rencontré une erreur lors de la connexion au serveur.' 
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
        <div class="empty-icon">💬</div>
        <h1>Comment puis-je vous aider ?</h1>
        <p>Posez-moi vos questions pour créer votre bail de location</p>
      </div>
      
      <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
        <div class="message-content">
          <div class="avatar" :class="msg.role">
            <span v-if="msg.role === 'user'">👤</span>
            <svg v-else width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <path d="M14 2v6h6"/>
              <path d="M16 13H8"/>
              <path d="M16 17H8"/>
            </svg>
          </div>
          <div class="content-wrapper">
            <div class="sender-name">{{ msg.role === 'user' ? 'Vous' : 'BailAssist' }}</div>
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
          <div class="avatar assistant">
            <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <path d="M14 2v6h6"/>
              <path d="M16 13H8"/>
              <path d="M16 17H8"/>
            </svg>
          </div>
          <div class="content-wrapper">
            <div class="sender-name">BailAssist</div>
            <div class="text typing-indicator">
              <span></span><span></span><span></span>
            </div>
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
          placeholder="Tapez votre message..."
          rows="1"
        ></textarea>
        <button @click="sendMessage" :disabled="!userInput.trim() || isLoading" class="send-btn">
          <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
          </svg>
        </button>
      </div>
      <p class="input-hint">Appuyez sur Entrée pour envoyer, Maj+Entrée pour un saut de ligne</p>
    </div>
  </div>
</template>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--color-background);
  color: var(--color-ink);
  font-family: 'DM Sans', -apple-system, sans-serif;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 180px;
  scroll-behavior: smooth;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  padding: 40px;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 24px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.empty-state h1 {
  font-family: 'Fraunces', Georgia, serif;
  font-size: 2rem;
  font-weight: 500;
  color: var(--color-ink);
  margin-bottom: 12px;
}

.empty-state p {
  color: var(--color-ink-light);
  font-size: 1.1rem;
}

.message {
  padding: 32px 0;
}

.message.user {
  background-color: var(--color-background);
}

.message.assistant {
  background-color: var(--color-surface);
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

.message-content {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  gap: 20px;
  padding: 0 24px;
  align-items: flex-start; 
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.avatar.user {
  background: linear-gradient(135deg, var(--color-accent), var(--color-accent-dark));
  color: white;
}

.avatar.assistant {
  background: linear-gradient(135deg, #7c3aed, #a78bfa);
  color: white;
}

.content-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.sender-name {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--color-ink);
  margin-bottom: 8px;
}

.text {
  line-height: 1.7;
  overflow-wrap: break-word;
  width: 100%;
}

:deep(.markdown-body) {
  font-size: 16px;
  line-height: 1.7;
  color: var(--color-ink);
}

:deep(.markdown-body p) { margin-bottom: 1em; }
:deep(.markdown-body p:last-child) { margin-bottom: 0; }

:deep(.markdown-body pre) {
  background-color: var(--color-ink);
  color: #f8f8f2;
  padding: 16px 20px;
  border-radius: 12px;
  overflow-x: auto;
  margin: 1em 0;
  font-size: 14px;
}

:deep(.markdown-body code) {
  font-family: 'Menlo', 'Monaco', monospace;
  background-color: var(--color-cream-dark);
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.9em;
  color: #7c3aed;
}

:deep(.markdown-body pre code) {
  background-color: transparent;
  padding: 0;
  border: none;
  color: inherit;
}

:deep(.markdown-body ul), :deep(.markdown-body ol) { 
  margin-bottom: 1em; 
  padding-left: 24px; 
}

:deep(.markdown-body li) {
  margin-bottom: 0.5em;
}

:deep(.markdown-body a) {
  color: var(--color-accent);
  text-decoration: none;
  font-weight: 500;
}

:deep(.markdown-body a:hover) {
  text-decoration: underline;
}

:deep(.markdown-body strong) {
  font-weight: 600;
  color: var(--color-ink);
}

:deep(.markdown-body h1),
:deep(.markdown-body h2),
:deep(.markdown-body h3) {
  font-family: 'Fraunces', Georgia, serif;
  font-weight: 500;
  margin: 1.5em 0 0.75em;
  color: var(--color-ink);
}

:deep(.markdown-body h1) { font-size: 1.5em; }
:deep(.markdown-body h2) { font-size: 1.3em; }
:deep(.markdown-body h3) { font-size: 1.15em; }

:deep(.markdown-body blockquote) {
  border-left: 4px solid var(--color-accent);
  padding-left: 16px;
  margin: 1em 0;
  color: var(--color-ink-light);
  font-style: italic;
}

.input-area {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(180deg, transparent, var(--color-background) 30%);
  padding: 20px 24px 32px;
  z-index: 20;
}

.input-wrapper {
  max-width: 800px;
  margin: 0 auto;
  position: relative;
  background: var(--color-surface);
  border-radius: 24px;
  box-shadow: 0 4px 24px rgba(26, 26, 46, 0.1);
  border: 2px solid var(--color-border);
  display: flex;
  align-items: flex-end;
  padding: 8px 8px 8px 20px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-wrapper:focus-within {
  border-color: var(--color-accent);
  box-shadow: 0 4px 24px rgba(37, 99, 235, 0.15);
}

textarea {
  width: 100%;
  max-height: 200px;
  background-color: transparent;
  border: none;
  color: var(--color-ink);
  padding: 12px 0;
  font-family: inherit;
  font-size: 16px;
  line-height: 1.5;
  resize: none;
  outline: none;
  overflow-y: hidden;
}

textarea::placeholder {
  color: var(--color-ink-muted);
}

textarea:focus { overflow-y: auto; }

.send-btn {
  background: linear-gradient(135deg, var(--color-accent), var(--color-accent-dark));
  border: none;
  color: white;
  cursor: pointer;
  padding: 12px;
  border-radius: 16px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.3);
}

.send-btn:disabled {
  background: var(--color-cream-dark);
  color: var(--color-ink-muted);
  cursor: not-allowed;
}

.input-hint {
  text-align: center;
  font-size: 0.8rem;
  color: var(--color-ink-muted);
  margin-top: 12px;
}

.typing-indicator {
  display: flex;
  gap: 6px;
  padding: 8px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background-color: var(--color-accent);
  border-radius: 50%;
  animation: bounce 1.4s infinite both;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 80%, 100% { 
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% { 
    transform: scale(1);
    opacity: 1;
  }
}

/* Scrollbar styling */
.messages::-webkit-scrollbar {
  width: 8px;
}

.messages::-webkit-scrollbar-track {
  background: transparent;
}

.messages::-webkit-scrollbar-thumb {
  background: var(--color-cream-dark);
  border-radius: 4px;
}

.messages::-webkit-scrollbar-thumb:hover {
  background: var(--color-ink-muted);
}
</style>