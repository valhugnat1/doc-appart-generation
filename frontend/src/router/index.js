import { createRouter, createWebHistory } from 'vue-router'
import PublicView from '../views/PublicView.vue'
import AdminView from '../views/AdminView.vue'
import ChatView from '../views/ChatView.vue'

const routes = [
  {
    path: '/',
    component: PublicView,
    children: [
      {
        path: '',
        name: 'PublicHome',
        component: ChatView // Or a placeholder if needed, but ChatView handles the chat
      },
      {
        path: 'chat/:id',
        name: 'PublicChat',
        component: ChatView
      }
    ]
  },
  {
    path: '/admin',
    component: AdminView,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'AdminHome',
        component: ChatView
      },
      {
        path: 'chat/:id',
        name: 'AdminChat',
        component: ChatView
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

import Cookies from 'js-cookie'

router.beforeEach((to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth)) {
    // Check for existing auth cookie
    const isAuthenticated = Cookies.get('admin_auth') === 'true'
    
    if (isAuthenticated) {
      next()
    } else {
      // Simple password check
      const password = prompt('Veuillez entrer le mot de passe administrateur :')
      // Use environment variable for password
      const adminPassword = import.meta.env.VITE_ADMIN_PASSWORD || 'admin123'
      
      if (password === adminPassword) {
        // Set cookie to expire in 7 days
        Cookies.set('admin_auth', 'true', { expires: 7 })
        next()
      } else {
        alert('Mot de passe incorrect')
        next('/')
      }
    }
  } else {
    next()
  }
})

export default router
