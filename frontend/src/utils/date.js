/**
 * 日期格式化工具
 * 提供统一的日期时间格式化功能
 */

export function formatDate(date, format = 'YYYY-MM-DD') {
  if (!date) return '-'

  const d = new Date(date)
  if (isNaN(d.getTime())) return '-'

  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')

  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

export function formatDateTime(datetime) {
  return formatDate(datetime, 'YYYY-MM-DD HH:mm:ss')
}

export function formatTime(time) {
  return formatDate(time, 'HH:mm:ss')
}

export function formatDateCompact(date) {
  return formatDate(date, 'YYYYMMDD')
}

export function formatTimestamp(timestamp) {
  if (!timestamp) return '-'
  return formatDateTime(new Date(timestamp * 1000))
}

export function isToday(date) {
  if (!date) return false
  const d = new Date(date)
  const today = new Date()
  return d.getFullYear() === today.getFullYear() &&
    d.getMonth() === today.getMonth() &&
    d.getDate() === today.getDate()
}

export function isYesterday(date) {
  if (!date) return false
  const d = new Date(date)
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)
  return d.getFullYear() === yesterday.getFullYear() &&
    d.getMonth() === yesterday.getMonth() &&
    d.getDate() === yesterday.getDate()
}

export function isThisWeek(date) {
  if (!date) return false
  const d = new Date(date)
  const today = new Date()
  const startOfWeek = new Date(today)
  startOfWeek.setDate(today.getDate() - today.getDay())
  startOfWeek.setHours(0, 0, 0, 0)
  return d >= startOfWeek && d <= today
}

export function getRelativeTime(date) {
  if (!date) return '-'

  const d = new Date(date)
  const now = new Date()
  const diff = now - d

  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (seconds < 60) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`

  return formatDate(d, 'YYYY-MM-DD')
}

export function parseDate(dateString) {
  if (!dateString) return null
  const d = new Date(dateString)
  return isNaN(d.getTime()) ? null : d
}

export function addDays(date, days) {
  const d = new Date(date)
  d.setDate(d.getDate() + days)
  return d
}

export function addHours(date, hours) {
  const d = new Date(date)
  d.setHours(d.getHours() + hours)
  return d
}

export function diffDays(date1, date2) {
  const d1 = new Date(date1)
  const d2 = new Date(date2)
  const diff = Math.abs(d1 - d2)
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}
