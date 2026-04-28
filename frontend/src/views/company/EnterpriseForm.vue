/**
 * 企业表单组件
 * 用于新增和编辑企业信息
 */
<template>
  <el-dialog 
    :model-value="visible" 
    :title="isEdit ? '编辑企业' : '新增企业'" 
    width="900px" 
    top="3vh"
    @update:model-value="$emit('update:visible', $event)"
  >
    <el-form :model="form" label-width="140px">
      <el-collapse v-model="activeCollapse">
        <el-collapse-item title="基本信息" name="basic">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="企业名称" required>
                <el-input v-model="form.name" placeholder="请输入企业名称" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="统一社会信用代码">
                <el-input v-model="form.credit_code" placeholder="请输入统一社会信用代码" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="法人代表">
                <el-input v-model="form.legal_person" placeholder="请输入法人代表" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="注册资本(万元)">
                <el-input v-model="form.registered_capital" type="number" placeholder="请输入注册资本" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="成立日期">
                <el-date-picker 
                  v-model="form.establishment_date" 
                  type="date" 
                  value-format="YYYY-MM-DD" 
                  style="width: 100%" 
                  placeholder="请选择成立日期" 
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="企业类型">
                <el-select v-model="form.enterprise_type" placeholder="请选择企业类型" style="width: 100%" clearable>
                  <el-option label="有限责任公司" value="limited" />
                  <el-option label="股份有限公司" value="joint_stock" />
                  <el-option label="个人独资企业" value="sole_proprietorship" />
                  <el-option label="合伙企业" value="partnership" />
                  <el-option label="其他" value="other" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="24">
              <el-form-item label="所在地区">
                <el-cascader
                  v-model="regionValue"
                  :options="regionData"
                  :props="{ expandTrigger: 'hover', value: 'value', label: 'label', children: 'children' }"
                  placeholder="请选择省/市/区"
                  style="width: 100%"
                  clearable
                  @change="handleRegionChange"
                />
              </el-form-item>
            </el-col>
            <el-col :span="24">
              <el-form-item label="详细地址">
                <el-input v-model="form.address" placeholder="请输入详细地址（不含省市区）" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-collapse-item>
        
        <el-collapse-item title="联系方式" name="contact">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="联系人">
                <el-input v-model="form.contact_person" placeholder="请输入联系人" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="联系电话">
                <el-input v-model="form.contact_phone" placeholder="请输入联系电话" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="联系邮箱">
                <el-input v-model="form.contact_email" placeholder="请输入联系邮箱" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-collapse-item>
        
        <el-collapse-item title="财务信息" name="finance">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="开户银行">
                <el-input v-model="form.bank_name" placeholder="请输入开户银行" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="银行账号">
                <el-input v-model="form.bank_account" placeholder="请输入银行账号" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-collapse-item>
        
        <el-collapse-item title="其他信息" name="other">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="企业规模">
                <el-select v-model="form.enterprise_scale" placeholder="请选择企业规模" style="width: 100%" clearable>
                  <el-option label="大型" value="大型" />
                  <el-option label="中型" value="中型" />
                  <el-option label="小型" value="小型" />
                  <el-option label="微型" value="微型" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="员工人数">
                <el-input v-model="form.staff_count" type="number" placeholder="请输入员工人数" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="参保人数">
                <el-input v-model="form.insured_count" type="number" placeholder="请输入参保人数" />
              </el-form-item>
            </el-col>
            <el-col :span="24">
              <el-form-item label="经营范围">
                <el-input v-model="form.business_scope" type="textarea" :rows="4" placeholder="请输入经营范围" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-collapse-item>
        
        <el-collapse-item title="投标配置" name="bid">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="启用自动投标">
                <el-switch v-model="form.auto_bid_enabled" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="自动投标阈值">
                <el-input-number v-model="form.auto_bid_threshold" :min="0" :max="100" :disabled="!form.auto_bid_enabled" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="启用自动上传">
                <el-switch v-model="form.auto_upload_enabled" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="企业状态">
                <el-switch v-model="form.is_active" active-text="有效" inactive-text="无效" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="已验证">
                <el-switch v-model="form.is_verified" active-text="已验证" inactive-text="未验证" />
              </el-form-item>
            </el-col>
            <el-col :span="24">
              <el-form-item label="自动投标关键词">
                <el-select
                  v-model="form.auto_bid_keywords"
                  multiple
                  filterable
                  allow-create
                  default-first-option
                  placeholder="输入关键词后按回车添加"
                  style="width: 100%"
                >
                  <el-option
                    v-for="kw in form.auto_bid_keywords"
                    :key="kw"
                    :label="kw"
                    :value="kw"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="24">
              <el-form-item label="通知渠道">
                <el-checkbox-group v-model="form.notification_channels">
                  <el-checkbox value="dingtalk">钉钉</el-checkbox>
                  <el-checkbox value="wechat">企业微信</el-checkbox>
                  <el-checkbox value="email">邮件</el-checkbox>
                  <el-checkbox value="sms">短信</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
            </el-col>
          </el-row>
        </el-collapse-item>
      </el-collapse>
    </el-form>
    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { regionData, getRegionValue, parseRegionValue } from '@/utils/regions'
import { useFormDraft } from '@/composables/useFormDraft'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  enterprise: {
    type: Object,
    default: null
  },
  isEdit: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible', 'save'])

const saving = ref(false)
const activeCollapse = ref(['basic', 'contact', 'finance', 'other', 'bid'])
const regionValue = ref([])

const defaultForm = {
  id: null,
  name: '',
  credit_code: '',
  legal_person: '',
  registered_capital: '',
  establishment_date: '',
  province: '',
  city: '',
  district: '',
  address: '',
  contact_person: '',
  contact_phone: '',
  contact_email: '',
  bank_name: '',
  bank_account: '',
  enterprise_type: '',
  enterprise_scale: '',
  staff_count: '',
  insured_count: '',
  business_scope: '',
  auto_bid_enabled: false,
  auto_bid_threshold: 60,
  auto_upload_enabled: false,
  auto_bid_keywords: [],
  notification_channels: [],
  tags: [],
  extra_info: {},
  is_active: true,
  is_verified: false
}

const form = reactive({ ...defaultForm })

const draftKey = computed(() => {
  if (props.isEdit && props.enterprise?.id) {
    return `enterprise:edit:${props.enterprise.id}`
  }
  return 'enterprise:create'
})

const { clearDraft } = useFormDraft(form, {
  key: draftKey,
  sensitiveFields: ['bank_account', 'credit_code'],
  context: () => ({ isEdit: props.isEdit, enterpriseId: props.enterprise?.id }),
  onRestored: (data) => {
    if (data.province || data.city || data.district) {
      regionValue.value = getRegionValue(data.province, data.city, data.district)
    }
  }
})

watch(() => props.enterprise, (newVal) => {
  if (newVal) {
    Object.keys(defaultForm).forEach(key => {
      form[key] = newVal[key] !== undefined ? newVal[key] : defaultForm[key]
    })
    form.id = newVal.id
    regionValue.value = getRegionValue(newVal.province, newVal.city, newVal.district)
  } else {
    Object.assign(form, defaultForm)
    regionValue.value = []
  }
}, { immediate: true })

const handleRegionChange = (value) => {
  const parsed = parseRegionValue(value)
  form.province = parsed.province
  form.city = parsed.city
  form.district = parsed.district
}

const handleSave = async () => {
  if (!form.name) {
    return
  }

  saving.value = true

  try {
    const submitData = {
      name: form.name,
      credit_code: form.credit_code || null,
      legal_person: form.legal_person || null,
      registered_capital: form.registered_capital ? Number(form.registered_capital) : null,
      establishment_date: form.establishment_date || null,
      province: form.province || null,
      city: form.city || null,
      district: form.district || null,
      address: form.address || null,
      contact_person: form.contact_person || null,
      contact_phone: form.contact_phone || null,
      contact_email: form.contact_email || null,
      bank_name: form.bank_name || null,
      bank_account: form.bank_account || null,
      enterprise_type: form.enterprise_type || null,
      enterprise_scale: form.enterprise_scale || null,
      staff_count: form.staff_count ? Number(form.staff_count) : null,
      insured_count: form.insured_count ? Number(form.insured_count) : null,
      business_scope: form.business_scope || null,
      auto_bid_enabled: form.auto_bid_enabled,
      auto_bid_threshold: form.auto_bid_threshold ?? 60,
      auto_upload_enabled: form.auto_upload_enabled,
      auto_bid_keywords: Array.isArray(form.auto_bid_keywords) ? form.auto_bid_keywords : [],
      notification_channels: Array.isArray(form.notification_channels) ? form.notification_channels : [],
      tags: Array.isArray(form.tags) ? form.tags : [],
      extra_info: form.extra_info || {},
      is_active: form.is_active,
      is_verified: form.is_verified
    }

    if (form.id) {
      submitData.id = form.id
    }

    clearDraft()
    emit('save', submitData)
  } finally {
    saving.value = false
  }
}
</script>
