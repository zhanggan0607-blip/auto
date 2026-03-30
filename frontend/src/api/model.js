/**
 * 模型配置 API
 * 支持 Ollama、OpenAI、vLLM 等多种大模型提供商
 */
import request from '@/utils/request'

export const modelApi = {
  /**
   * 获取提供商列表
   */
  listProviders: () => {
    return request.get('/v1/openclaw/llm-providers/')
  },

  /**
   * 获取提供商详情
   */
  getProvider: (id) => {
    return request.get(`/v1/openclaw/llm-providers/${id}/`)
  },

  /**
   * 创建提供商
   */
  createProvider: (data) => {
    return request.post('/v1/openclaw/llm-providers/', data)
  },

  /**
   * 更新提供商
   */
  updateProvider: (id, data) => {
    return request.patch(`/v1/openclaw/llm-providers/${id}/`, data)
  },

  /**
   * 删除提供商
   */
  deleteProvider: (id) => {
    return request.delete(`/v1/openclaw/llm-providers/${id}/`)
  },

  /**
   * 测试连接
   */
  testConnection: (providerId, modelId) => {
    return request.post('/v1/openclaw/llm-providers/test_connection/', {
      provider_id: providerId,
      model_id: modelId
    })
  },

  /**
   * 获取模型列表
   */
  listModels: (params = {}) => {
    return request.get('/v1/openclaw/llm-models/', { params })
  },

  /**
   * 获取模型详情
   */
  getModel: (id) => {
    return request.get(`/v1/openclaw/llm-models/${id}/`)
  },

  /**
   * 创建模型
   */
  createModel: (data) => {
    return request.post('/v1/openclaw/llm-models/', data)
  },

  /**
   * 更新模型
   */
  updateModel: (id, data) => {
    return request.patch(`/v1/openclaw/llm-models/${id}/`, data)
  },

  /**
   * 删除模型
   */
  deleteModel: (id) => {
    return request.delete(`/v1/openclaw/llm-models/${id}/`)
  },

  /**
   * 获取Agent模型配置
   */
  getAgentConfigs: () => {
    return request.get('/v1/openclaw/agent-model-configs/')
  },

  /**
   * 更新Agent模型配置
   */
  updateAgentConfig: (id, data) => {
    return request.patch(`/v1/openclaw/agent-model-configs/${id}/`, data)
  },

  /**
   * 批量更新Agent配置
   */
  batchUpdateAgentConfigs: (configs) => {
    return request.post('/v1/openclaw/agent-model-configs/batch_update/', { configs })
  },

  /**
   * 获取Ollama可用模型列表
   * @param {string} url - Ollama服务地址，默认http://localhost:11434
   */
  getOllamaModels: (url = 'http://localhost:11434') => {
    return request.get('/v1/openclaw/llm-providers/ollama_models/', {
      params: { url }
    })
  },

  /**
   * 获取Ollama服务状态
   * @param {string} url - Ollama服务地址，默认http://localhost:11434
   */
  getOllamaStatus: (url = 'http://localhost:11434') => {
    return request.get('/v1/openclaw/llm-providers/ollama_status/', {
      params: { url }
    })
  },

  /**
   * 同步Ollama已安装模型到数据库
   */
  syncOllamaModels: () => {
    return request.post('/v1/openclaw/llm-providers/sync_ollama_models/')
  },

  /**
   * AI Playground API
   */
  playground: {
    /**
     * 获取所有可用的模型提供商
     */
    getProviders: () => {
      return request.get('/v1/openclaw/playground/providers/')
    },

    /**
     * 统一聊天接口
     */
    chat: (data) => {
      return request.post('/v1/openclaw/playground/chat/', data)
    },

    /**
     * 流式聊天接口
     */
    streamChat: (data) => {
      return request.post('/v1/openclaw/playground/stream_chat/', data)
    },

    /**
     * 获取调用历史记录
     */
    getHistory: (params = {}) => {
      return request.get('/v1/openclaw/playground/history/', { params })
    },

    /**
     * 获取模型详细信息和特性
     */
    getModelInfo: (type) => {
      return request.get('/v1/openclaw/playground/model_info/', {
        params: { type }
      })
    },

    /**
     * 测试所有提供商连接状态
     * @param {string} message - 测试消息，默认"你好，请回复测试成功"
     */
    testAllProviders: (message = '你好，请回复"测试成功"') => {
      return request.post('/v1/openclaw/llm-providers/test_all_providers/', {
        message
      })
    }
  }
}

export default modelApi
