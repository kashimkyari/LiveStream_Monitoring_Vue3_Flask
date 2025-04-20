/**
 * MobileChatScroll directive for Vue 3
 * A custom Vue 3 directive for auto-scrolling chat elements, optimized for mobile
 * This provides similar functionality to vue-chat-scroll but is fully compatible with Vue 3
 */

export const MobileChatScroll = {
  mounted(el, binding) {
    // Set default behavior if no binding value is provided
    const smoothScroll = binding.value === undefined ? true : binding.value
    
    // MutationObserver setup
    const observer = new MutationObserver(mutations => {
      // If we have children mutation, scroll down
      const shouldScroll = mutations.some(mutation => 
        mutation.type === 'childList' && mutation.addedNodes.length
      )
      
      if (shouldScroll) {
        // Scroll to bottom of element
        if (smoothScroll) {
          el.scrollTo({
            top: el.scrollHeight,
            behavior: 'smooth'
          })
        } else {
          el.scrollTop = el.scrollHeight
        }
      }
    })
    
    // Start observing
    observer.observe(el, {
      childList: true,
      subtree: true
    })
    
    // Store observer reference for cleanup
    el._mobileChatScrollObserver = observer
    
    // Initial scroll
    el.scrollTop = el.scrollHeight
  },
  
  // Cleanup when unmounted
  unmounted(el) {
    if (el._mobileChatScrollObserver) {
      el._mobileChatScrollObserver.disconnect()
      delete el._mobileChatScrollObserver
    }
  }
}

// Default export for convenience
export default MobileChatScroll