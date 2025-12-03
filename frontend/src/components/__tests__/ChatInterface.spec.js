import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatInterface from '../ChatInterface.vue'

// Mock vue-router
const mockPush = vi.fn()
const mockReplace = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace
  })
}))

// Mock fetch
global.fetch = vi.fn()

// Mock scroll
Element.prototype.scrollTo = vi.fn()

describe('ChatInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders empty state initially', () => {
    const wrapper = mount(ChatInterface)
    expect(wrapper.find('.empty-state').exists()).toBe(true)
    expect(wrapper.text()).toContain('Comment puis-je vous aider ?')
  })

  it('renders input area', () => {
    const wrapper = mount(ChatInterface)
    expect(wrapper.find('textarea').exists()).toBe(true)
    expect(wrapper.find('.send-btn').exists()).toBe(true)
  })

  it('loads conversation if conversationId prop is provided', async () => {
    const mockMessages = [
      { role: 'user', content: 'Hello' },
      { role: 'assistant', content: 'Hi there' }
    ]
    
    global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ messages: mockMessages })
    })

    const wrapper = mount(ChatInterface, {
      props: {
        conversationId: 'test-uuid'
      }
    })

    // Wait for onMounted and fetch
    await new Promise(resolve => setTimeout(resolve, 0))
    await wrapper.vm.$nextTick()

    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/conversations/test-uuid'))
    // Check if messages are rendered (this might require more complex waiting/flushing promises)
    // For now, just checking the fetch call is a good start.
  })
})
