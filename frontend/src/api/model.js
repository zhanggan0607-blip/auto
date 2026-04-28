import request from '@/utils/request'

export const modelApi = {
  listProviders: () => {
    return request.get('/v1/openclaw/llm-providers/')
  },

  testConnection: (providerId, modelId) => {
    return request.post('/v1/openclaw/llm-providers/test_connection/', {
      provider_id: providerId,
      model_id: modelId
    })
  },

  listModels: (params = {}) => {
    return request.get('/v1/openclaw/llm-models/', { params })
  },

  getAgentConfigs: () => {
    return request.get('/v1/openclaw/agent-model-configs/')
  },

  batchUpdateAgentConfigs: (configs) => {
    return request.post('/v1/openclaw/agent-model-configs/batch_update/', { configs })
  },

  getOllamaModels: (url = 'http://localhost:11434') => {
    return request.get('/v1/openclaw/llm-providers/ollama_models/', {
      params: { url }
    })
  },

  getOllamaStatus: (url = 'http://localhost:11434') => {
    return request.get('/v1/openclaw/llm-providers/ollama_status/', {
      params: { url }
    })
  },

  playground: {
    chat: (data) => {
      return request.post('/v1/openclaw/playground/chat/', data)
    },

    getHistory: (params = {}) => {
      return request.get('/v1/openclaw/playground/history/', { params })
    },

    testAllProviders: (message = '你好，请回复"测试成功"') => {
      return request.post('/v1/openclaw/llm-providers/test_all_providers/', {
        message
      })
    }
  }
}

export default modelApi
