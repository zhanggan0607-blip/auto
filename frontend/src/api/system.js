import request from '@/utils/request'

export function getSystemServices() {
  return request.get('/v1/system/services/')
}

export function getSystemHealth() {
  return request.get('/v1/system/health/')
}
