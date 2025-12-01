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

router.beforeEach((to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth)) {
    // Simple password check
    const password = prompt('Veuillez entrer le mot de passe administrateur :')
    if (password === 'admin123') { // Hardcoded for now as requested
      next()
    } else {
      alert('Mot de passe incorrect')
      next('/')
    }
  } else {
    next()
  }
})

export default router
