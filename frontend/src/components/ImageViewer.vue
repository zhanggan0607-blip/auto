<template>
  <teleport to="body">
    <transition name="viewer-fade">
      <div
        v-if="visible"
        class="image-viewer"
        @touchstart="handleTouchStart"
        @touchmove="handleTouchMove"
        @touchend="handleTouchEnd"
      >
        <div class="viewer-header">
          <div class="viewer-title">
            <span v-if="currentIndex >= 0">{{ currentIndex + 1 }} / {{ imageList.length }}</span>
          </div>
          <div class="viewer-actions">
            <button class="action-btn" @click="zoomOut" title="缩小">
              <el-icon :size="20"><ZoomOut /></el-icon>
            </button>
            <button class="action-btn" @click="zoomIn" title="放大">
              <el-icon :size="20"><ZoomIn /></el-icon>
            </button>
            <button class="action-btn" @click="rotate" title="旋转">
              <el-icon :size="20"><RefreshRight /></el-icon>
            </button>
            <button class="action-btn" @click="toggleFullscreen" title="全屏">
              <el-icon :size="20"><FullScreen /></el-icon>
            </button>
            <button class="action-btn close-btn" @click="close" title="关闭">
              <el-icon :size="24"><Close /></el-icon>
            </button>
          </div>
        </div>

        <div class="viewer-body" ref="viewerBodyRef" @click.self="toggleZoom">
          <transition-group name="viewer-slide">
            <div
              v-for="(image, index) in imageList"
              :key="image.url"
              v-show="index === currentIndex"
              class="image-wrapper"
              :style="getImageStyle(index)"
            >
              <img
                ref="imageRefs"
                :src="image.url"
                :alt="image.name || ''"
                class="viewer-image"
                :style="getCurrentImageStyle()"
                @load="handleImageLoad(index)"
                @error="handleImageError(index)"
                draggable="false"
              />
            </div>
          </transition-group>

          <div v-if="imageList.length > 1" class="viewer-nav viewer-nav-prev" @click="prev">
            <el-icon :size="32"><ArrowLeft /></el-icon>
          </div>
          <div v-if="imageList.length > 1" class="viewer-nav viewer-nav-next" @click="next">
            <el-icon :size="32"><ArrowRight /></el-icon>
          </div>
        </div>

        <div class="viewer-footer" v-if="imageList.length > 1">
          <div class="thumbnail-list" ref="thumbnailRef">
            <div
              v-for="(image, index) in imageList"
              :key="'thumb-' + index"
              class="thumbnail-item"
              :class="{ active: index === currentIndex }"
              @click="switchTo(index)"
            >
              <img :src="image.thumbUrl || image.url" :alt="image.name || ''" />
            </div>
          </div>
        </div>

        <div class="viewer-loading" v-if="loading">
          <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { ZoomIn, ZoomOut, RefreshRight, FullScreen, Close, ArrowLeft, ArrowRight, Loading } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  images: {
    type: Array,
    default: () => []
  },
  initialIndex: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const visible = ref(false)
const imageList = ref([])
const currentIndex = ref(0)
const loading = ref(false)

const viewerBodyRef = ref(null)
const thumbnailRef = ref(null)
const imageRefs = ref([])

const scale = ref(1)
const rotation = ref(0)
const translateX = ref(0)
const translateY = ref(0)
const isDragging = ref(false)
const startX = ref(0)
const startY = ref(0)

const MIN_SCALE = 0.1
const MAX_SCALE = 10
const ZOOM_STEP = 0.25

let lastTouchDistance = 0
let lastTouchCenter = { x: 0, y: 0 }

const open = (images, index = 0) => {
  imageList.value = images.map(img => {
    if (typeof img === 'string') {
      return { url: img, name: '', thumbUrl: img }
    }
    return {
      url: img.url || img.src,
      name: img.name || '',
      thumbUrl: img.thumbUrl || img.url || img.src
    }
  })
  currentIndex.value = index
  scale.value = 1
  rotation.value = 0
  translateX.value = 0
  translateY.value = 0
  visible.value = true
  document.body.style.overflow = 'hidden'
  scrollToThumbnail(index)
}

const close = () => {
  visible.value = false
  emit('update:modelValue', false)
  document.body.style.overflow = ''
  resetImageState()
}

const resetImageState = () => {
  scale.value = 1
  rotation.value = 0
  translateX.value = 0
  translateY.value = 0
}

const switchTo = (index) => {
  if (index === currentIndex.value) return
  currentIndex.value = index
  resetImageState()
  emit('change', index)
  scrollToThumbnail(index)
}

const prev = () => {
  const newIndex = currentIndex.value > 0 ? currentIndex.value - 1 : imageList.value.length - 1
  switchTo(newIndex)
}

const next = () => {
  const newIndex = currentIndex.value < imageList.value.length - 1 ? currentIndex.value + 1 : 0
  switchTo(newIndex)
}

const scrollToThumbnail = (index) => {
  nextTick(() => {
    if (thumbnailRef.value) {
      const thumbnails = thumbnailRef.value.querySelectorAll('.thumbnail-item')
      if (thumbnails[index]) {
        thumbnails[index].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
      }
    }
  })
}

const zoomIn = () => {
  scale.value = Math.min(MAX_SCALE, scale.value + ZOOM_STEP)
}

const zoomOut = () => {
  scale.value = Math.max(MIN_SCALE, scale.value - ZOOM_STEP)
}

const rotate = () => {
  rotation.value = (rotation.value + 90) % 360
}

const toggleFullscreen = async () => {
  if (!document.fullscreenElement) {
    await viewerBodyRef.value?.requestFullscreen()
  } else {
    await document.exitFullscreen()
  }
}

const toggleZoom = () => {
  if (scale.value === 1) {
    scale.value = 2
  } else {
    scale.value = 1
    translateX.value = 0
    translateY.value = 0
  }
}

const getCurrentImageStyle = () => {
  return {
    transform: `scale(${scale.value}) rotate(${rotation.value}deg) translate(${translateX.value}px, ${translateY.value}px)`,
    transition: isDragging.value ? 'none' : 'transform 0.2s ease'
  }
}

const getImageStyle = () => {
  return {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center'
  }
}

const handleImageLoad = (index) => {
  if (index === currentIndex.value) {
    loading.value = false
  }
}

const handleImageError = (index) => {
  if (index === currentIndex.value) {
    loading.value = false
  }
}

const handleTouchStart = (e) => {
  if (e.touches.length === 1) {
    isDragging.value = true
    startX.value = e.touches[0].clientX - translateX.value
    startY.value = e.touches[0].clientY - translateY.value
  } else if (e.touches.length === 2) {
    lastTouchDistance = getTouchDistance(e.touches)
    lastTouchCenter = getTouchCenter(e.touches)
  }
}

const handleTouchMove = (e) => {
  if (e.touches.length === 1 && isDragging.value && scale.value > 1) {
    e.preventDefault()
    translateX.value = e.touches[0].clientX - startX.value
    translateY.value = e.touches[0].clientY - startY.value
  } else if (e.touches.length === 2) {
    e.preventDefault()
    const distance = getTouchDistance(e.touches)
    if (lastTouchDistance > 0) {
      const delta = distance / lastTouchDistance
      scale.value = Math.max(MIN_SCALE, Math.min(MAX_SCALE, scale.value * delta))
    }
    lastTouchDistance = distance
    lastTouchCenter = getTouchCenter(e.touches)
  }
}

const handleTouchEnd = () => {
  isDragging.value = false
  lastTouchDistance = 0
}

const getTouchDistance = (touches) => {
  const dx = touches[0].clientX - touches[1].clientX
  const dy = touches[0].clientY - touches[1].clientY
  return Math.sqrt(dx * dx + dy * dy)
}

const getTouchCenter = (touches) => {
  return {
    x: (touches[0].clientX + touches[1].clientX) / 2,
    y: (touches[0].clientY + touches[1].clientY) / 2
  }
}

const handleKeydown = (e) => {
  if (!visible.value) return
  switch (e.key) {
    case 'Escape':
      close()
      break
    case 'ArrowLeft':
      prev()
      break
    case 'ArrowRight':
      next()
      break
    case 'ArrowUp':
    case '+':
    case '=':
      e.preventDefault()
      zoomIn()
      break
    case 'ArrowDown':
    case '-':
      e.preventDefault()
      zoomOut()
      break
    case 'r':
    case 'R':
      rotate()
      break
  }
}

const handleMouseWheel = (e) => {
  if (!visible.value) return
  if (e.ctrlKey) {
    e.preventDefault()
    if (e.deltaY < 0) {
      zoomIn()
    } else {
      zoomOut()
    }
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  document.addEventListener('wheel', handleMouseWheel, { passive: false })
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('wheel', handleMouseWheel)
  document.body.style.overflow = ''
})

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    document.body.style.overflow = 'hidden'
    resetImageState()
  } else {
    document.body.style.overflow = ''
  }
})

watch(() => props.images, (val) => {
  if (val && val.length > 0) {
    open(val, props.initialIndex)
  }
}, { immediate: true })

defineExpose({
  open,
  close,
  prev,
  next,
  zoomIn,
  zoomOut,
  rotate
})
</script>

<style scoped>
.image-viewer {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.95);
  display: flex;
  flex-direction: column;
  user-select: none;
  -webkit-user-select: none;
}

.viewer-header {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 56px;
  background: linear-gradient(180deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0) 100%);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 16px;
  z-index: 10;
}

.viewer-title {
  color: #fff;
  font-size: 14px;
  font-weight: 500;
}

.viewer-actions {
  display: flex;
  gap: 4px;
}

.action-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.action-btn:active {
  background: rgba(255, 255, 255, 0.3);
}

.close-btn {
  margin-left: 8px;
}

.viewer-body {
  flex: 1;
  position: relative;
  overflow: hidden;
  cursor: zoom-in;
}

.viewer-body:active {
  cursor: zoom-out;
}

.image-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  pointer-events: none;
}

.viewer-image {
  max-width: 90vw;
  max-height: 90vh;
  object-fit: contain;
  transform-origin: center center;
  will-change: transform;
  pointer-events: auto;
}

.viewer-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 50px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  cursor: pointer;
  opacity: 0.6;
  transition: opacity 0.2s, background 0.2s;
  z-index: 5;
}

.viewer-nav:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.1);
}

.viewer-nav-prev {
  left: 16px;
  border-radius: 8px;
}

.viewer-nav-next {
  right: 16px;
  border-radius: 8px;
}

.viewer-footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 100px;
  background: linear-gradient(0deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0) 100%);
  display: flex;
  justify-content: center;
  align-items: flex-end;
  padding: 16px;
  z-index: 10;
}

.thumbnail-list {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  max-width: 100%;
  padding: 8px;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.3) transparent;
}

.thumbnail-list::-webkit-scrollbar {
  height: 4px;
}

.thumbnail-list::-webkit-scrollbar-track {
  background: transparent;
}

.thumbnail-list::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.3);
  border-radius: 2px;
}

.thumbnail-item {
  width: 60px;
  height: 60px;
  flex-shrink: 0;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  opacity: 0.6;
  transition: all 0.2s;
}

.thumbnail-item:hover {
  opacity: 0.9;
}

.thumbnail-item.active {
  border-color: #3B82F6;
  opacity: 1;
}

.thumbnail-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.viewer-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #fff;
}

.viewer-fade-enter-active,
.viewer-fade-leave-active {
  transition: opacity 0.3s ease;
}

.viewer-fade-enter-from,
.viewer-fade-leave-to {
  opacity: 0;
}

.viewer-slide-enter-active,
.viewer-slide-leave-active {
  transition: all 0.3s ease;
}

.viewer-slide-enter-from {
  opacity: 0;
  transform: scale(0.9);
}

.viewer-slide-leave-to {
  opacity: 0;
  transform: scale(1.1);
}

@media (max-width: 768px) {
  .viewer-header {
    height: 48px;
    padding: 0 12px;
  }

  .action-btn {
    width: 36px;
    height: 36px;
  }

  .viewer-nav {
    width: 40px;
    height: 60px;
  }

  .viewer-footer {
    height: 80px;
  }

  .thumbnail-item {
    width: 48px;
    height: 48px;
  }

  .viewer-image {
    max-width: 95vw;
    max-height: 80vh;
  }
}

@media (max-width: 480px) {
  .viewer-title {
    font-size: 12px;
  }

  .action-btn {
    width: 32px;
    height: 32px;
  }

  .viewer-nav {
    width: 36px;
    height: 50px;
  }

  .thumbnail-item {
    width: 40px;
    height: 40px;
  }
}
</style>
