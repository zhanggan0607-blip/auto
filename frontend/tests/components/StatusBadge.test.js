/**
 * 组件测试
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StatusBadge from '@/components/StatusBadge.vue'

describe('StatusBadge组件', () => {
  /**
   * 测试组件渲染
   */
  it('应正确渲染状态徽章', () => {
    const wrapper = mount(StatusBadge, {
      props: {
        status: 'success',
        text: '成功'
      }
    })
    
    expect(wrapper.text()).toContain('成功')
    expect(wrapper.find('.el-tag').exists()).toBe(true)
  })

  /**
   * 测试不同状态类型
   */
  it('应根据状态类型显示不同样式', () => {
    const successWrapper = mount(StatusBadge, {
      props: { status: 'success', text: '成功' }
    })
    
    const dangerWrapper = mount(StatusBadge, {
      props: { status: 'danger', text: '失败' }
    })
    
    expect(successWrapper.classes()).toContain('el-tag--success')
    expect(dangerWrapper.classes()).toContain('el-tag--danger')
  })

  /**
   * 测试默认状态
   */
  it('应使用默认状态info', () => {
    const wrapper = mount(StatusBadge, {
      props: { text: '信息' }
    })
    
    expect(wrapper.classes()).toContain('el-tag--info')
  })
})
