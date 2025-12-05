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
import { API_BASE_URL } from '@/config.js'

router.beforeEach(async (to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth)) {
    // Check for existing auth cookie
    const isAuthenticated = Cookies.get('admin_auth') === 'true'

    if (isAuthenticated) {
      next()
    } else {
      // Prompt for password
      const password = prompt('Veuillez entrer le mot de passe administrateur :')

      if (!password) {
        // User cancelled the prompt
        next('/')
        return
      }

      try {
        // Verify password with backend
        const response = await fetch(`${API_BASE_URL}/api/auth/verify-admin`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ password })
        })

        if (response.ok) {
          // Password is correct, set cookie to expire in 7 days
          Cookies.set('admin_auth', 'true', { expires: 7 })
          next()
        } else {
          // Password is incorrect
          alert('Mot de passe incorrect')
          next('/')
        }
      } catch (error) {
        console.error('Error verifying password:', error)
        alert('Erreur lors de la vérification du mot de passe')
        next('/')
      }
    }
  } else {
    next()
  }
})

export default router
