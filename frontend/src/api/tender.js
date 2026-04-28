import { createApi } from './base'
import request from '@/utils/request'

const tenderApi = createApi('/v1/tenders')

tenderApi.favorite = (id) => request.post(`/v1/tenders/${id}/favorite/`)

tenderApi.getSourceContent = (id) => request.get(`/v1/tenders/${id}/source-content/`)

tenderApi.getStatistics = () => request.get('/v1/tenders/statistics/')

tenderApi.getTrend = (params) => request.get('/v1/tenders/trend/', { params })

tenderApi.getKeywords = (params) => request.get('/v1/tenders/keywords/', { params })

tenderApi.createKeyword = (data) => request.post('/v1/tenders/keywords/', data)

tenderApi.deleteKeyword = (id) => request.delete(`/v1/tenders/keywords/${id}/`)

tenderApi.delete = (id) => request.delete(`/v1/tenders/${id}/`)

tenderApi.crawlSync = () => request.post('/v1/tenders/crawl-sync/')

tenderApi.getCrawlSyncStatus = () => request.get('/v1/tenders/crawl-sync/')

tenderApi.getSources = () => request.get('/v1/tenders/sources/')

tenderApi.getCrawlStatistics = (params) => request.get('/v1/tenders/crawl-statistics/', { params })

tenderApi.exportCrawlData = () => request.get('/v1/tenders/crawl-export/', {}, { responseType: 'blob' })

export { tenderApi }
export default tenderApi
