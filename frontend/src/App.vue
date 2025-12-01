<script setup>
import { onMounted } from 'vue'
import { useTheme } from '@/composables/useTheme'

const { initTheme } = useTheme()

onMounted(() => {
  initTheme()
})
</script>

<template>
  <router-view></router-view>
</template>

<style>
:root {
  /* Light theme colors */
  --color-background: #faf9f7;
  --color-surface: #ffffff;
  --color-surface-alt: #faf9f7;
  --color-border: #f0ede8;
  --color-ink: #1a1a2e;
  --color-ink-light: #4a4a5a;
  --color-ink-muted: #7a7a8a;
  --color-cream: #faf9f7;
  --color-cream-dark: #f0ede8;
  --color-accent: #2563eb;
  --color-accent-dark: #1d4ed8;
  --color-accent-light: #dbeafe;
}

:root.dark {
  /* Dark theme colors */
  --color-background: #1a1a2e;
  --color-surface: #252540;
  --color-surface-alt: #2d2d48;
  --color-border: #3a3a54;
  --color-ink: #ececf1;
  --color-ink-light: #d1d1d6;
  --color-ink-muted: #9b9ba8;
  --color-cream: #252540;
  --color-cream-dark: #3a3a54;
  --color-accent: #3b82f6;
  --color-accent-dark: #2563eb;
  --color-accent-light: #1e3a8a;
}

body {
  margin: 0;
  padding: 0;
  background-color: var(--color-background);
  color: var(--color-ink);
  transition: background-color 0.3s ease, color 0.3s ease;
}
</style>

