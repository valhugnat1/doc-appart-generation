import { createRouter, createWebHistory } from 'vue-router'
import App from '../App.vue' // We might need to separate Home/Chat views, but for now let's see. 
// Actually, App.vue is currently the main view. I should probably refactor App.vue content into a Home or Chat view.
// Let's assume I'll create a ChatView.vue that contains the current chat logic from App.vue.

// For now, let's define the routes and I will refactor App.vue content into a view component next.
// But wait, the user wants a sidebar. 
// App.vue should hold the Sidebar and the RouterView.
// The RouterView will display the ChatInterface.

// So I need to move the current chat interface from App.vue to a new component, say `views/ChatView.vue`.

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/ChatView.vue') // Lazy load
  },
  {
    path: '/chat/:id',
    name: 'Chat',
    component: () => import('../views/ChatView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
