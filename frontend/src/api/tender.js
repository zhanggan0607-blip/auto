import { createApi } from './base'
import request from '@/utils/request'

const tenderApi = createApi('/v1/tenders')

tenderApi.favorite = (id) => request.post(`/v1/tenders/${id}/favorite/`)

tenderApi.getStatistics = () => request.get('/v1/tenders/statistics/')

tenderApi.getKeywords = (params) => request.get('/v1/tenders/keywords/', { params })

tenderApi.createKeyword = (data) => request.post('/v1/tenders/keywords/', data)

tenderApi.deleteKeyword = (id) => request.delete(`/v1/tenders/keywords/${id}/`)

tenderApi.delete = (id) => request.delete(`/v1/tenders/${id}/`)

export { tenderApi }
export default tenderApi
