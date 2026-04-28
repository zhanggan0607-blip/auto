import request from '@/utils/request'

export function getMonitorDashboard() {
  return request.get('/v1/monitor/dashboard/')
}

export function createMonitoredService(data) {
  return request.post('/v1/monitor/services/', data)
}

export function checkServiceHealth(id) {
  return request.post(`/v1/monitor/services/${id}/check_health/`)
}

export function restartService(id) {
  return request.post(`/v1/monitor/services/${id}/restart/`)
}

export function getServiceCategories() {
  return request.get('/v1/monitor/services/categories/')
}

export function getHealthRecords(params) {
  return request.get('/v1/monitor/health-records/', { params })
}

export function getAlerts(params) {
  return request.get('/v1/monitor/alerts/', { params })
}

export function resolveAlert(id) {
  return request.post(`/v1/monitor/alerts/${id}/resolve/`)
}

export function resolveAllAlerts(alertIds) {
  return request.post('/v1/monitor/alerts/resolve_all/', { alert_ids: alertIds })
}

export function sendAlertNotification(id) {
  return request.post(`/v1/monitor/alerts/${id}/send_notification/`)
}

export function getActionLogs(params) {
  return request.get('/v1/monitor/action-logs/', { params })
}

export function triggerAutoRecovery() {
  return request.post('/v1/monitor/auto-recovery/')
}
