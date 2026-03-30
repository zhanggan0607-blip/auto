/**
 * 图片懒加载指令
 * 用于优化图片加载性能
 */

/**
 * 默认占位图
 */
const defaultPlaceholder = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiB2aWV3Qm94PSIwIDAgMTAwIDEwMCI+PHJlY3Qgd2lkdGg9IjEwMCIgaGVpZ2h0PSIxMDAiIGZpbGw9IiNmNWY3ZmEiLz48dGV4dCB4PSI1MCIgeT0iNTAiIGZpbGw9IiNjMGM0Y2MiIGZvbnQtc2l6ZT0iMTIiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7lm77niYfliqDovb3lpLHotKU8L3RleHQ+PC9zdmc+'

/**
 * 已加载的图片集合
 */
const loadedImages = new Set()

/**
 * IntersectionObserver实例
 */
let observer = null

/**
 * 初始化IntersectionObserver
 */
function initObserver() {
  if (observer) return
  
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const img = entry.target
          const src = img._lazySrc
          
          if (src && !loadedImages.has(src)) {
            img.src = src
            img.onload = () => {
              loadedImages.add(src)
              img.classList.add('lazy-loaded')
            }
            img.onerror = () => {
              img.src = defaultPlaceholder
              img.classList.add('lazy-error')
            }
          }
          
          observer.unobserve(img)
        }
      })
    },
    {
      rootMargin: '50px 0px',
      threshold: 0.01
    }
  )
}

/**
 * 懒加载指令
 */
export const lazyLoad = {
  /**
   * 挂载时
   */
  mounted(el, binding) {
    initObserver()
    
    el._lazySrc = binding.value
    el.src = defaultPlaceholder
    el.classList.add('lazy-loading')
    
    observer.observe(el)
  },
  
  /**
   * 更新时
   */
  updated(el, binding) {
    if (binding.value !== binding.oldValue) {
      el._lazySrc = binding.value
      
      if (loadedImages.has(binding.value)) {
        el.src = binding.value
        el.classList.remove('lazy-loading')
        el.classList.add('lazy-loaded')
      }
    }
  },
  
  /**
   * 卸载时
   */
  unmounted(el) {
    if (observer) {
      observer.unobserve(el)
    }
  }
}

/**
 * 防抖指令
 */
export const debounce = {
  mounted(el, binding) {
    const delay = binding.arg ? parseInt(binding.arg) : 300
    let timer = null
    
    el._debounceHandler = (event) => {
      if (timer) clearTimeout(timer)
      timer = setTimeout(() => {
        binding.value(event)
      }, delay)
    }
    
    el.addEventListener('input', el._debounceHandler)
  },
  
  unmounted(el) {
    if (el._debounceHandler) {
      el.removeEventListener('input', el._debounceHandler)
    }
  }
}

/**
 * 节流指令
 */
export const throttle = {
  mounted(el, binding) {
    const delay = binding.arg ? parseInt(binding.arg) : 300
    let lastTime = 0
    
    el._throttleHandler = (event) => {
      const now = Date.now()
      if (now - lastTime >= delay) {
        lastTime = now
        binding.value(event)
      }
    }
    
    el.addEventListener('click', el._throttleHandler)
  },
  
  unmounted(el) {
    if (el._throttleHandler) {
      el.removeEventListener('click', el._throttleHandler)
    }
  }
}

/**
 * 注册全局指令
 */
export function registerDirectives(app) {
  app.directive('lazy', lazyLoad)
  app.directive('debounce', debounce)
  app.directive('throttle', throttle)
}

export default {
  lazy: lazyLoad,
  debounce,
  throttle
}
