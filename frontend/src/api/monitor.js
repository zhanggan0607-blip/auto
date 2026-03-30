import request from '@/utils/request'

export function getMonitorDashboard() {
  return request.get('/v1/monitor/dashboard/')
}

export function getMonitoredServices(params) {
  return request.get('/v1/monitor/services/', { params })
}

export function getMonitoredService(id) {
  return request.get(`/v1/monitor/services/${id}/`)
}

export function createMonitoredService(data) {
  return request.post('/v1/monitor/services/', data)
}

export function updateMonitoredService(id, data) {
  return request.put(`/v1/monitor/services/${id}/`, data)
}

export function deleteMonitoredService(id) {
  return request.delete(`/v1/monitor/services/${id}/`)
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

export function getHealthRecordLatest(serviceId) {
  return request.get('/v1/monitor/health-records/latest/', { params: { service_id: serviceId } })
}

export function getHealthRecordStatistics(serviceId, hours = 24) {
  return request.get('/v1/monitor/health-records/statistics/', { params: { service_id: serviceId, hours } })
}

export function getAlerts(params) {
  return request.get('/v1/monitor/alerts/', { params })
}

export function getAlert(id) {
  return request.get(`/v1/monitor/alerts/${id}/`)
}

export function updateAlert(id, data) {
  return request.patch(`/v1/monitor/alerts/${id}/`, data)
}

export function resolveAlert(id) {
  return request.post(`/v1/monitor/alerts/${id}/resolve/`)
}

export function resolveAllAlerts(alertIds) {
  return request.post('/v1/monitor/alerts/resolve_all/', { alert_ids: alertIds })
}

export function getPendingAlerts() {
  return request.get('/v1/monitor/alerts/pending/')
}

export function sendAlertNotification(id) {
  return request.post(`/v1/monitor/alerts/${id}/send_notification/`)
}

export function getActionLogs(params) {
  return request.get('/v1/monitor/action-logs/', { params })
}

export function triggerHealthCheck() {
  return request.post('/v1/monitor/health-check/')
}

export function triggerAutoRecovery() {
  return request.post('/v1/monitor/auto-recovery/')
}