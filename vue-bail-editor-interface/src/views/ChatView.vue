<script setup>
import ChatInterface from '../components/ChatInterface.vue'
import { useRoute } from 'vue-router'
import { watch } from 'vue'

const route = useRoute()

// We might need to pass the ID to ChatInterface if it supports it
// For now, just wrapping it.

const emit = defineEmits(['message-received'])
</script>

<template>
  <ChatInterface 
    :key="route.params.id" 
    :conversation-id="route.params.id" 
    @message-received="$emit('message-received', $event)"
  />
</template>
