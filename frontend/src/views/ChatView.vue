<script setup>
import ChatInterface from '../components/ChatInterface.vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const emit = defineEmits(['message-received', 'is-loading'])
</script>

<template>
  <ChatInterface 
    :key="route.params.id" 
    :conversation-id="route.params.id" 
    @message-received="$emit('message-received', $event)"
    @is-loading="$emit('is-loading', $event)"
  />
</template>