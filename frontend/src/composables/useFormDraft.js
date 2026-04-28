import { watch, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'

const STORAGE_PREFIX = 'form_draft_'
const EXPIRE_DAYS = 7
const DEBOUNCE_MS = 5000
const PERIODIC_MS = 30000

const SENSITIVE_FIELDS = new Set([
  'password', 'password_confirm', 'confirm_password', 'new_password', 'old_password',
  'api_key', 'secret', 'secret_key', 'access_token', 'refresh_token',
  'bank_account', 'credit_code'
])

function isExpired(timestamp) {
  if (!timestamp) return true
  const diff = Date.now() - timestamp
  return diff > EXPIRE_DAYS * 24 * 60 * 60 * 1000
}

function sanitizeData(data, extraSensitive = []) {
  if (!data || typeof data !== 'object') return data
  if (Array.isArray(data)) return data.map(item => sanitizeData(item, extraSensitive))

  const allSensitive = new Set([...SENSITIVE_FIELDS, ...extraSensitive])
  const result = {}

  for (const [key, value] of Object.entries(data)) {
    if (allSensitive.has(key)) {
      if (value && typeof value === 'string' && value.length > 0) {
        result[key] = '••••••••'
      } else {
        result[key] = value
      }
    } else if (value && typeof value === 'object' && !Array.isArray(value) && !(value instanceof Date)) {
      result[key] = sanitizeData(value, extraSensitive)
    } else {
      result[key] = value
    }
  }

  return result
}

function restoreData(target, saved, sensitiveFields = []) {
  if (!saved || !target || typeof target !== 'object') return

  const allSensitive = new Set([...SENSITIVE_FIELDS, ...sensitiveFields])

  for (const [key, value] of Object.entries(saved)) {
    if (key in target) {
      if (allSensitive.has(key)) continue
      if (value === '••••••••') continue

      if (value && typeof value === 'object' && !Array.isArray(value) && !(value instanceof Date)) {
        if (target[key] && typeof target[key] === 'object') {
          restoreData(target[key], value, sensitiveFields)
        }
      } else {
        target[key] = value
      }
    }
  }
}

function saveDraft(key, data, context = {}) {
  try {
    const payload = {
      data,
      context,
      savedAt: Date.now(),
      version: 1
    }
    localStorage.setItem(STORAGE_PREFIX + key, JSON.stringify(payload))
  } catch (e) {
    if (e.name === 'QuotaExceededError') {
      cleanExpiredDrafts()
      try {
        const payload = { data, context, savedAt: Date.now(), version: 1 }
        localStorage.setItem(STORAGE_PREFIX + key, JSON.stringify(payload))
      } catch (_e) {
        console.warn('[FormDraft] 存储空间不足，无法保存草稿')
      }
    }
  }
}

function loadDraft(key) {
  try {
    const raw = localStorage.getItem(STORAGE_PREFIX + key)
    if (!raw) return null

    const payload = JSON.parse(raw)
    if (isExpired(payload.savedAt)) {
      localStorage.removeItem(STORAGE_PREFIX + key)
      return null
    }

    return payload
  } catch (_e) {
    localStorage.removeItem(STORAGE_PREFIX + key)
    return null
  }
}

function removeDraft(key) {
  localStorage.removeItem(STORAGE_PREFIX + key)
}

function cleanExpiredDrafts() {
  const keysToRemove = []
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i)
    if (k && k.startsWith(STORAGE_PREFIX)) {
      try {
        const raw = localStorage.getItem(k)
        if (raw) {
          const payload = JSON.parse(raw)
          if (isExpired(payload.savedAt)) {
            keysToRemove.push(k)
          }
        }
      } catch (_e) {
        keysToRemove.push(k)
      }
    }
  }
  keysToRemove.forEach(k => localStorage.removeItem(k))
  return keysToRemove.length
}

function getAllDrafts() {
  const drafts = []
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i)
    if (k && k.startsWith(STORAGE_PREFIX)) {
      try {
        const raw = localStorage.getItem(k)
        if (raw) {
          const payload = JSON.parse(raw)
          if (!isExpired(payload.savedAt)) {
            drafts.push({
              key: k.slice(STORAGE_PREFIX.length),
              savedAt: payload.savedAt,
              context: payload.context || {}
            })
          }
        }
      } catch (_e) {
        // skip
      }
    }
  }
  return drafts.sort((a, b) => b.savedAt - a.savedAt)
}

function clearAllDrafts() {
  const keysToRemove = []
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i)
    if (k && k.startsWith(STORAGE_PREFIX)) {
      keysToRemove.push(k)
    }
  }
  keysToRemove.forEach(k => localStorage.removeItem(k))
  return keysToRemove.length
}

function formatSavedTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now - date
  const diffMin = Math.floor(diffMs / 60000)
  const diffHour = Math.floor(diffMs / 3600000)
  const diffDay = Math.floor(diffMs / 86400000)

  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin}分钟前`
  if (diffHour < 24) return `${diffHour}小时前`
  if (diffDay < 7) return `${diffDay}天前`
  return date.toLocaleDateString('zh-CN')
}

export function useFormDraft(formData, options = {}) {
  const {
    key = '',
    sensitiveFields = [],
    context = {},
    autoSave = true,
    debounceMs = DEBOUNCE_MS,
    periodicMs = PERIODIC_MS,
    promptOnRestore = true,
    promptMessage = '',
    onRestored = null,
    onSaved = null
  } = options

  const draftKey = key
  let debounceTimer = null
  let periodicTimer = null
  let hasUnsavedChanges = false
  let isRestoring = false
  let stopWatch = null

  function triggerAutoSave() {
    if (!autoSave || isRestoring || !draftKey) return

    hasUnsavedChanges = false
    const dataToSave = sanitizeData(
      typeof formData === 'object' && formData !== null && 'value' in formData
        ? formData.value
        : formData,
      sensitiveFields
    )
    const ctx = typeof context === 'function' ? context() : context
    saveDraft(draftKey, dataToSave, ctx)
    if (onSaved) onSaved()
  }

  function scheduleDebouncedSave() {
    if (!autoSave || isRestoring) return
    hasUnsavedChanges = true

    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
      triggerAutoSave()
    }, debounceMs)
  }

  function startWatching() {
    if (!autoSave || !draftKey) return

    stopWatch = watch(
      () => {
        if (typeof formData === 'object' && formData !== null && 'value' in formData) {
          return JSON.parse(JSON.stringify(formData.value || {}))
        }
        if (typeof formData === 'object' && formData !== null) {
          return JSON.parse(JSON.stringify(formData))
        }
        return formData
      },
      () => {
        if (!isRestoring) {
          scheduleDebouncedSave()
        }
      },
      { deep: true }
    )

    periodicTimer = setInterval(() => {
      if (hasUnsavedChanges) {
        triggerAutoSave()
      }
    }, periodicMs)
  }

  function stopWatching() {
    if (stopWatch) {
      stopWatch()
      stopWatch = null
    }
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
    if (periodicTimer) {
      clearInterval(periodicTimer)
      periodicTimer = null
    }
  }

  async function checkAndRestore() {
    if (!draftKey || !promptOnRestore) return

    const draft = loadDraft(draftKey)
    if (!draft || !draft.data) return

    const savedTime = formatSavedTime(draft.savedAt)
    const defaultMsg = `检测到您在 ${savedTime} 有未保存的输入内容，是否恢复？`
    const message = promptMessage || defaultMsg

    try {
      await ElMessageBox.confirm(message, '恢复草稿', {
        confirmButtonText: '恢复',
        cancelButtonText: '不恢复',
        type: 'info',
        distinguishCancelAndClose: true
      })

      isRestoring = true
      const target = typeof formData === 'object' && formData !== null && 'value' in formData
        ? formData.value
        : formData

      restoreData(target, draft.data, sensitiveFields)

      await nextTick()
      isRestoring = false

      if (onRestored) onRestored(draft.data, draft.context)
      ElMessage.success('草稿已恢复')
    } catch (action) {
      if (action === 'cancel') {
        clearDraft()
      }
      isRestoring = false
    }
  }

  function clearDraft() {
    if (draftKey) {
      removeDraft(draftKey)
    }
    hasUnsavedChanges = false
  }

  function saveNow() {
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
    triggerAutoSave()
  }

  onMounted(() => {
    cleanExpiredDrafts()
    checkAndRestore()
    startWatching()
  })

  onUnmounted(() => {
    if (hasUnsavedChanges && draftKey) {
      triggerAutoSave()
    }
    stopWatching()
  })

  return {
    clearDraft,
    saveNow,
    hasDraft: () => draftKey ? !!loadDraft(draftKey) : false,
    getDraftInfo: () => {
      const draft = loadDraft(draftKey)
      if (!draft) return null
      return { savedAt: draft.savedAt, context: draft.context, savedTime: formatSavedTime(draft.savedAt) }
    }
  }
}

export function useFormDraftManager() {
  return {
    getAllDrafts,
    clearAllDrafts,
    cleanExpiredDrafts,
    clearDraftByKey: (key) => removeDraft(key),
    getDraftCount: () => getAllDrafts().length,
    formatSavedTime
  }
}
