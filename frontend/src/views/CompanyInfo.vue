<template>
  <div class="company-page">
    <div class="page-header">
      <div class="header-title">
        <h3 class="page-title">企业信息管理</h3>
        <p class="page-subtitle">管理企业基本信息、资质、人员及业绩记录</p>
      </div>
      <div class="header-actions">
        <el-button type="info" @click="showCollectPlaceholder">
          <el-icon><Connection /></el-icon>
          采集企业信息
        </el-button>
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新增企业
        </el-button>
      </div>
    </div>
    
    <div class="enterprise-list-section">
      <el-card class="list-card" shadow="hover">
        <template #header>
          <div class="section-header">
            <span class="section-title">
              <el-icon><OfficeBuilding /></el-icon>
              企业列表
            </span>
            <span class="enterprise-count">共 {{ enterpriseList.length }} 家企业</span>
          </div>
        </template>
        <el-table 
          :data="enterpriseList" 
          @row-click="selectEnterprise" 
          highlight-current-row
          :row-class-name="getRowClassName"
          class="enterprise-table"
        >
          <el-table-column prop="name" label="企业名称" min-width="200">
            <template #default="{ row }">
              <div class="enterprise-name-cell">
                <span class="enterprise-name">{{ row.name }}</span>
                <el-tag v-if="row.is_verified" type="success" size="small" class="verified-tag">已验证</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="legal_person" label="法人代表" width="100" />
          <el-table-column prop="contact_phone" label="联系电话" width="130" />
          <el-table-column prop="enterprise_scale" label="企业规模" width="100">
            <template #default="{ row }">
              <span>{{ row.enterprise_scale || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link @click.stop="editEnterprise(row)">
                <el-icon><Edit /></el-icon>编辑
              </el-button>
              <el-button type="danger" link @click.stop="deleteEnterprise(row)">
                <el-icon><Delete /></el-icon>删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
    
    <div class="enterprise-detail-section">
      <el-card v-if="selectedEnterprise" class="detail-card" shadow="hover">
        <template #header>
          <div class="section-header">
            <span class="section-title">
              <el-icon><Document /></el-icon>
              企业详情
            </span>
            <div class="detail-actions">
              <el-button type="primary" link @click="editEnterprise(selectedEnterprise)">
                <el-icon><Edit /></el-icon>编辑
              </el-button>
            </div>
          </div>
        </template>
        <el-tabs v-model="activeTab" class="detail-tabs">
          <el-tab-pane label="基本信息" name="basic">
            <el-descriptions :column="responsiveColumn" border size="small" class="info-descriptions">
              <el-descriptions-item label="企业名称">
                <span class="info-value highlight">{{ selectedEnterprise.name }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="统一社会信用代码">
                {{ selectedEnterprise.credit_code || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="法人代表">
                {{ selectedEnterprise.legal_person || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="注册资本">
                <span v-if="selectedEnterprise.registered_capital" class="info-value capital">
                  ¥{{ selectedEnterprise.registered_capital }}万元
                </span>
                <span v-else>-</span>
              </el-descriptions-item>
              <el-descriptions-item label="成立日期">
                {{ selectedEnterprise.establishment_date || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="企业规模">
                <el-tag v-if="selectedEnterprise.enterprise_scale" size="small">
                  {{ selectedEnterprise.enterprise_scale }}
                </el-tag>
                <span v-else>-</span>
              </el-descriptions-item>
              <el-descriptions-item label="员工人数">
                {{ selectedEnterprise.staff_count || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="联系电话">
                <span v-if="selectedEnterprise.contact_phone" class="info-value phone">
                  {{ selectedEnterprise.contact_phone }}
                </span>
                <span v-else>-</span>
              </el-descriptions-item>
              <el-descriptions-item label="邮箱">
                {{ selectedEnterprise.contact_email || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="参保人数">
                {{ selectedEnterprise.insured_count || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="企业地址" :span="2">
                <el-icon><Location /></el-icon>
                {{ selectedEnterprise.address || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="联系人">
                {{ selectedEnterprise.contact_person || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="开户银行">
                {{ selectedEnterprise.bank_name || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="银行账号" :span="2">
                {{ selectedEnterprise.bank_account || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="经营范围" :span="2">
                <div class="business-scope">{{ selectedEnterprise.business_scope || '-' }}</div>
              </el-descriptions-item>
            </el-descriptions>
          </el-tab-pane>
          <el-tab-pane label="项目经理" name="project_manager">
            <div class="personnel-section">
              <div class="personnel-header">
                <el-button type="primary" size="small" @click="showAddPersonnelDialog('project_manager')">
                  <el-icon><Plus /></el-icon>添加项目经理
                </el-button>
              </div>
              <el-table :data="projectManagers" size="small" stripe v-loading="personnelLoading">
                <el-table-column prop="personnel_id" label="人员ID" width="150" />
                <el-table-column prop="name" label="姓名" width="80" />
                <el-table-column prop="id_number" label="身份证号" width="180" />
                <el-table-column prop="birth_date" label="出生年月" width="100" />
                <el-table-column prop="builder_certificate" label="建造师证书" min-width="150" />
                <el-table-column prop="safety_certificate_b" label="B证" width="100" />
                <el-table-column prop="engineer_title_certificate" label="工程师职称证" min-width="150" />
                <el-table-column prop="certificate_number" label="证书编号" width="140" />
                <el-table-column prop="certificate_major" label="注册专业" width="100" />
                <el-table-column prop="expiry_date" label="证书有效期" width="110">
                  <template #default="{ row }">
                    <span :class="getPersonnelExpiryClass(row)">{{ row.expiry_date || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="title_level_display" label="职称等级" width="80" />
                <el-table-column prop="is_registered_locally" label="本单位注册" width="90">
                  <template #default="{ row }">
                    <el-tag :type="row.is_registered_locally ? 'success' : 'info'" size="small">
                      {{ row.is_registered_locally ? '是' : '否' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="professional_years" label="专业年限" width="80" />
                <el-table-column prop="certificate_status_display" label="状态" width="80">
                  <template #default="{ row }">
                    <el-tag :type="getPersonnelStatusType(row.certificate_status)" size="small">
                      {{ row.certificate_status_display }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="120" fixed="right">
                  <template #default="{ row }">
                    <el-button type="primary" link size="small" @click="editPersonnel(row)">编辑</el-button>
                    <el-button type="danger" link size="small" @click="deletePersonnel(row)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-if="projectManagers.length === 0 && !personnelLoading" description="暂无项目经理" />
            </div>
          </el-tab-pane>
          <el-tab-pane label="技术负责人" name="technical_director">
            <div class="personnel-section">
              <div class="personnel-header">
                <el-button type="primary" size="small" @click="showAddPersonnelDialog('technical_director')">
                  <el-icon><Plus /></el-icon>添加技术负责人
                </el-button>
              </div>
              <el-table :data="technicalDirectors" size="small" stripe v-loading="personnelLoading">
                <el-table-column prop="personnel_id" label="人员ID" width="150" />
                <el-table-column prop="name" label="姓名" width="80" />
                <el-table-column prop="id_number" label="身份证号" width="180" />
                <el-table-column prop="birth_date" label="出生年月" width="100" />
                <el-table-column prop="builder_certificate" label="建造师证书" min-width="150" />
                <el-table-column prop="safety_certificate_b" label="B证" width="100" />
                <el-table-column prop="engineer_title_certificate" label="工程师职称证" min-width="150" />
                <el-table-column prop="certificate_number" label="证书编号" width="140" />
                <el-table-column prop="title_level_display" label="职称等级" width="80" />
                <el-table-column prop="certificate_major" label="注册专业" width="100" />
                <el-table-column prop="expiry_date" label="证书有效期" width="110">
                  <template #default="{ row }">
                    <span :class="getPersonnelExpiryClass(row)">{{ row.expiry_date || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="is_registered_locally" label="本单位注册" width="90">
                  <template #default="{ row }">
                    <el-tag :type="row.is_registered_locally ? 'success' : 'info'" size="small">
                      {{ row.is_registered_locally ? '是' : '否' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="professional_years" label="专业年限" width="80" />
                <el-table-column prop="certificate_status_display" label="状态" width="80">
                  <template #default="{ row }">
                    <el-tag :type="getPersonnelStatusType(row.certificate_status)" size="small">
                      {{ row.certificate_status_display }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="120" fixed="right">
                  <template #default="{ row }">
                    <el-button type="primary" link size="small" @click="editPersonnel(row)">编辑</el-button>
                    <el-button type="danger" link size="small" @click="deletePersonnel(row)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-if="technicalDirectors.length === 0 && !personnelLoading" description="暂无技术负责人" />
            </div>
          </el-tab-pane>
          <el-tab-pane label="专业工程师" name="professional_engineer">
            <div class="personnel-section">
              <div class="personnel-header">
                <el-button type="primary" size="small" @click="showAddPersonnelDialog('professional_engineer')">
                  <el-icon><Plus /></el-icon>添加专业工程师
                </el-button>
              </div>
              <el-table :data="professionalEngineers" size="small" stripe v-loading="personnelLoading">
                <el-table-column prop="personnel_id" label="人员ID" width="150" />
                <el-table-column prop="name" label="姓名" width="80" />
                <el-table-column prop="id_number" label="身份证号" width="180" />
                <el-table-column prop="birth_date" label="出生年月" width="100" />
                <el-table-column prop="engineer_title_certificate" label="工程师职称证" min-width="150" />
                <el-table-column prop="certificate_number" label="证书编号" width="140" />
                <el-table-column prop="title_level_display" label="职称等级" width="80" />
                <el-table-column prop="certificate_major" label="专业" width="100" />
                <el-table-column prop="expiry_date" label="证书有效期" width="110">
                  <template #default="{ row }">
                    <span :class="getPersonnelExpiryClass(row)">{{ row.expiry_date || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="professional_years" label="专业年限" width="80" />
                <el-table-column prop="certificate_status_display" label="状态" width="80">
                  <template #default="{ row }">
                    <el-tag :type="getPersonnelStatusType(row.certificate_status)" size="small">
                      {{ row.certificate_status_display }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="120" fixed="right">
                  <template #default="{ row }">
                    <el-button type="primary" link size="small" @click="editPersonnel(row)">编辑</el-button>
                    <el-button type="danger" link size="small" @click="deletePersonnel(row)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-if="professionalEngineers.length === 0 && !personnelLoading" description="暂无专业工程师" />
            </div>
          </el-tab-pane>
          <el-tab-pane label="八大员" name="eight_officers">
            <div class="personnel-section">
              <div class="personnel-header">
                <el-button type="primary" size="small" @click="showAddPersonnelDialog('eight_officers')">
                  <el-icon><Plus /></el-icon>添加八大员
                </el-button>
              </div>
              <el-table :data="eightOfficers" size="small" stripe v-loading="personnelLoading">
                <el-table-column prop="personnel_id" label="人员ID" width="150" />
                <el-table-column prop="name" label="姓名" width="80" />
                <el-table-column prop="id_number" label="身份证号" width="180" />
                <el-table-column prop="birth_date" label="出生年月" width="100" />
                <el-table-column prop="officer_type_display" label="员种" width="80" />
                <el-table-column prop="certificate_number" label="证书编号" width="140" />
                <el-table-column prop="expiry_date" label="证书有效期" width="110">
                  <template #default="{ row }">
                    <span :class="getPersonnelExpiryClass(row)">{{ row.expiry_date || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="is_registered_locally" label="本单位注册" width="90">
                  <template #default="{ row }">
                    <el-tag :type="row.is_registered_locally ? 'success' : 'info'" size="small">
                      {{ row.is_registered_locally ? '是' : '否' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="certificate_status_display" label="状态" width="80">
                  <template #default="{ row }">
                    <el-tag :type="getPersonnelStatusType(row.certificate_status)" size="small">
                      {{ row.certificate_status_display }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="120" fixed="right">
                  <template #default="{ row }">
                    <el-button type="primary" link size="small" @click="editPersonnel(row)">编辑</el-button>
                    <el-button type="danger" link size="small" @click="deletePersonnel(row)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-if="eightOfficers.length === 0 && !personnelLoading" description="暂无八大员" />
            </div>
          </el-tab-pane>
          <el-tab-pane label="资质信息" name="qualification">
            <div class="personnel-section">
              <div class="personnel-header">
                <el-button type="primary" size="small" @click="showAddQualificationDialog">
                  <el-icon><Plus /></el-icon>添加资质信息
                </el-button>
              </div>
              <el-table :data="qualifications" size="small" stripe v-loading="qualificationLoading">
                <el-table-column prop="qualification_category_display" label="资质类别" width="100" />
                <el-table-column prop="qualification_name_display" label="资质名称" min-width="180" />
                <el-table-column prop="grade_display" label="等级" width="120" />
                <el-table-column prop="certificate_no" label="资质证书号" width="150" />
                <el-table-column prop="expiry_date" label="有效期" width="120" />
                <el-table-column label="操作" width="120" fixed="right">
                  <template #default="{ row }">
                    <el-button type="primary" link size="small" @click="editQualification(row)">编辑</el-button>
                    <el-button type="danger" link size="small" @click="deleteQualification(row)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-if="qualifications.length === 0 && !qualificationLoading" description="暂无资质信息" />
            </div>
          </el-tab-pane>
          <el-tab-pane label="业绩记录" name="performance">
            <div class="personnel-section">
              <div class="personnel-header">
                <el-button type="primary" size="small" @click="showAddPerformanceDialog">
                  <el-icon><Plus /></el-icon>添加业绩信息
                </el-button>
              </div>
              <el-table :data="performances" size="small" stripe v-loading="performanceLoading">
                <el-table-column prop="project_name" label="项目名称" min-width="200" />
                <el-table-column prop="contract_amount" label="合同金额(万元)" width="120">
                  <template #default="{ row }">
                    <span v-if="row.contract_amount" class="info-value capital">
                      ¥{{ row.contract_amount }}
                    </span>
                    <span v-else>-</span>
                  </template>
                </el-table-column>
                <el-table-column prop="end_date" label="完工日期" width="120" />
                <el-table-column prop="client_name" label="业主单位" width="150" />
                <el-table-column label="操作" width="120" fixed="right">
                  <template #default="{ row }">
                    <el-button type="primary" link size="small" @click="editPerformance(row)">编辑</el-button>
                    <el-button type="danger" link size="small" @click="deletePerformance(row)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-if="performances.length === 0 && !performanceLoading" description="暂无业绩记录" />
            </div>
          </el-tab-pane>
          <el-tab-pane label="文档资料" name="documents">
            <div class="documents-section">
              <div class="documents-header">
                <el-select v-model="documentFilterType" placeholder="证书类型" clearable style="width: 150px" @change="fetchDocuments">
                  <el-option v-for="item in documentTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
                </el-select>
                <el-select v-model="documentFilterStatus" placeholder="状态" clearable style="width: 100px; margin-left: 12px" @change="fetchDocuments">
                  <el-option v-for="item in documentStatusOptions" :key="item.value" :label="item.label" :value="item.value" />
                </el-select>
                <el-button type="primary" style="margin-left: auto" @click="showUploadDocumentDialog">
                  <el-icon><Upload /></el-icon>
                  上传证书
                </el-button>
              </div>
              <el-table :data="documentList" size="small" stripe v-loading="documentsLoading">
                <el-table-column prop="document_type_display" label="证书类型" width="100" />
                <el-table-column prop="document_name" label="证书名称" min-width="150">
                  <template #default="{ row }">
                    <div class="doc-name">
                      <el-icon v-if="row.is_primary" class="primary-icon"><Star /></el-icon>
                      {{ row.document_name }}
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="document_no" label="证书编号" width="130" />
                <el-table-column prop="expiry_date" label="有效期至" width="100">
                  <template #default="{ row }">
                    <span :class="getDocumentExpiryClass(row)">{{ row.expiry_date || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="status_display" label="状态" width="80">
                  <template #default="{ row }">
                    <el-tag :type="getDocumentStatusType(row.status)" size="small">{{ row.status_display }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="150" fixed="right">
                  <template #default="{ row }">
                    <el-button type="primary" link @click="previewDocument(row)">
                      <el-icon><View /></el-icon>预览
                    </el-button>
                    <el-button type="danger" link @click="deleteDocument(row)">
                      <el-icon><Delete /></el-icon>删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-if="documentList.length === 0 && !documentsLoading" description="暂无文档资料" />
            </div>
          </el-tab-pane>
          <el-tab-pane label="联系人" name="contacts">
            <div class="personnel-section">
              <div class="personnel-header">
                <el-button type="primary" size="small" @click="showAddContactDialog">
                  <el-icon><Plus /></el-icon>添加联系人
                </el-button>
              </div>
              <el-table :data="contacts" size="small" stripe v-loading="contactsLoading">
                <el-table-column prop="name" label="姓名" width="100" />
                <el-table-column prop="contact_type_display" label="联系人类型" width="120">
                  <template #default="{ row }">
                    <el-tag size="small">{{ row.contact_type_display || getContactTypeText(row.contact_type) }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="position" label="职位" width="120" />
                <el-table-column prop="phone" label="电话" width="140" />
                <el-table-column prop="email" label="邮箱" min-width="180" />
                <el-table-column prop="is_primary" label="主要联系人" width="100">
                  <template #default="{ row }">
                    <el-tag :type="row.is_primary ? 'success' : 'info'" size="small">
                      {{ row.is_primary ? '是' : '否' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="is_active" label="状态" width="80">
                  <template #default="{ row }">
                    <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                      {{ row.is_active ? '有效' : '无效' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="120" fixed="right">
                  <template #default="{ row }">
                    <el-button type="primary" link size="small" @click="editContact(row)">编辑</el-button>
                    <el-button type="danger" link size="small" @click="deleteContact(row)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-if="contacts.length === 0 && !contactsLoading" description="暂无联系人" />
            </div>
          </el-tab-pane>
          <el-tab-pane label="匹配规则" name="match_rules">
            <div class="personnel-section">
              <div class="personnel-header">
                <el-button type="primary" size="small" @click="showAddMatchRuleDialog">
                  <el-icon><Plus /></el-icon>添加匹配规则
                </el-button>
              </div>
              <el-table :data="matchRules" size="small" stripe v-loading="matchRulesLoading">
                <el-table-column prop="name" label="规则名称" min-width="150" />
                <el-table-column prop="rule_type_display" label="规则类型" width="120">
                  <template #default="{ row }">
                    <el-tag size="small">{{ row.rule_type_display || getMatchRuleTypeText(row.rule_type) }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="priority" label="优先级" width="80" />
                <el-table-column prop="weight" label="权重" width="80">
                  <template #default="{ row }">
                    <span>{{ row.weight || 1 }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="is_active" label="状态" width="80">
                  <template #default="{ row }">
                    <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                      {{ row.is_active ? '启用' : '禁用' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
                <el-table-column label="操作" width="120" fixed="right">
                  <template #default="{ row }">
                    <el-button type="primary" link size="small" @click="editMatchRule(row)">编辑</el-button>
                    <el-button type="danger" link size="small" @click="deleteMatchRule(row)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-if="matchRules.length === 0 && !matchRulesLoading" description="暂无匹配规则" />
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
      <el-card v-else class="empty-card" shadow="hover">
        <el-empty description="请从上方列表中选择企业查看详情">
          <template #image>
            <el-icon class="empty-icon"><Select /></el-icon>
          </template>
        </el-empty>
      </el-card>
    </div>
    
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑企业' : '新增企业'" width="900px" top="3vh">
      <el-form :model="enterpriseForm" label-width="140px">
        <el-collapse v-model="activeCollapse">
          <el-collapse-item title="基本信息" name="basic">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="企业名称" required>
                  <el-input v-model="enterpriseForm.name" placeholder="请输入企业名称" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="统一社会信用代码">
                  <el-input v-model="enterpriseForm.credit_code" placeholder="请输入统一社会信用代码" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="法人代表">
                  <el-input v-model="enterpriseForm.legal_person" placeholder="请输入法人代表" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="注册资本(万元)">
                  <el-input v-model="enterpriseForm.registered_capital" type="number" placeholder="请输入注册资本" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="成立日期">
                  <el-date-picker v-model="enterpriseForm.establishment_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" placeholder="请选择成立日期" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="企业类型">
                  <el-select v-model="enterpriseForm.enterprise_type" placeholder="请选择企业类型" style="width: 100%" clearable>
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
                  <el-input v-model="enterpriseForm.address" placeholder="请输入详细地址（不含省市区）" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-collapse-item>
          
          <el-collapse-item title="联系方式" name="contact">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="联系人">
                  <el-input v-model="enterpriseForm.contact_person" placeholder="请输入联系人" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="联系电话">
                  <el-input v-model="enterpriseForm.contact_phone" placeholder="请输入联系电话" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="联系邮箱">
                  <el-input v-model="enterpriseForm.contact_email" placeholder="请输入联系邮箱" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-collapse-item>
          
          <el-collapse-item title="财务信息" name="finance">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="开户银行">
                  <el-input v-model="enterpriseForm.bank_name" placeholder="请输入开户银行" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="银行账号">
                  <el-input v-model="enterpriseForm.bank_account" placeholder="请输入银行账号" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-collapse-item>
          
          <el-collapse-item title="其他信息" name="other">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="企业规模">
                  <el-select v-model="enterpriseForm.enterprise_scale" placeholder="请选择企业规模" style="width: 100%" clearable>
                    <el-option label="大型" value="大型" />
                    <el-option label="中型" value="中型" />
                    <el-option label="小型" value="小型" />
                    <el-option label="微型" value="微型" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="员工人数">
                  <el-input v-model="enterpriseForm.staff_count" type="number" placeholder="请输入员工人数" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="参保人数">
                  <el-input v-model="enterpriseForm.insured_count" type="number" placeholder="请输入参保人数" />
                </el-form-item>
              </el-col>
              <el-col :span="24">
                <el-form-item label="经营范围">
                  <el-input v-model="enterpriseForm.business_scope" type="textarea" :rows="4" placeholder="请输入经营范围" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-collapse-item>
          
          <el-collapse-item title="投标配置" name="bid">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="启用自动投标">
                  <el-switch v-model="enterpriseForm.auto_bid_enabled" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="自动投标阈值">
                  <el-input-number v-model="enterpriseForm.auto_bid_threshold" :min="0" :max="100" :disabled="!enterpriseForm.auto_bid_enabled" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="启用自动上传">
                  <el-switch v-model="enterpriseForm.auto_upload_enabled" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="企业状态">
                  <el-switch v-model="enterpriseForm.is_active" active-text="有效" inactive-text="无效" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="已验证">
                  <el-switch v-model="enterpriseForm.is_verified" active-text="已验证" inactive-text="未验证" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-collapse-item>
        </el-collapse>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEnterprise">保存</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="documentDialogVisible" title="上传证书" width="600px" destroy-on-close>
      <el-form :model="documentForm" :rules="documentFormRules" ref="documentFormRef" label-width="100px">
        <el-form-item label="证书类型" prop="document_type">
          <el-select v-model="documentForm.document_type" placeholder="请选择证书类型" style="width: 100%">
            <el-option v-for="item in documentTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="证书名称" prop="document_name">
          <el-input v-model="documentForm.document_name" placeholder="请输入证书名称" />
        </el-form-item>
        <el-form-item label="证书编号">
          <el-input v-model="documentForm.document_no" placeholder="请输入证书编号（如有）" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="发证日期">
              <el-date-picker v-model="documentForm.issue_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="有效期至">
              <el-date-picker v-model="documentForm.expiry_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="上传文件" prop="file_path">
          <el-upload
            ref="documentUploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleDocumentFileChange"
            :on-exceed="handleDocumentExceed"
            accept=".pdf,.jpg,.jpeg,.png,.gif,.bmp,.webp,.doc,.docx,.xls,.xlsx"
          >
            <template #trigger>
              <el-button type="primary">选择文件</el-button>
            </template>
            <template #tip>
              <div class="el-upload__tip">
                支持 PDF、图片、Word、Excel 格式，最大 10MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="自动识别">
          <el-switch v-model="documentForm.auto_recognize" />
          <span class="form-tip">上传后自动识别内容</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="documentDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitDocument" :loading="documentSubmitting">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="previewDialogVisible" title="证书预览" width="80%" top="5vh">
      <div class="preview-container">
        <img v-if="previewType === 'image'" :src="previewUrl" class="preview-image">
        <iframe v-else-if="previewType === 'pdf'" :src="previewUrl" class="preview-iframe" />
        <div v-else class="preview-unsupported">
          <el-icon><Document /></el-icon>
          <p>该文件类型不支持在线预览</p>
          <el-button type="primary" @click="downloadDocument(previewDoc)">下载文件</el-button>
        </div>
      </div>
    </el-dialog>
    
    <el-dialog v-model="personnelDialogVisible" :title="personnelDialogTitle" width="900px" top="3vh" destroy-on-close>
      <el-form :model="personnelForm" :rules="personnelFormRules" ref="personnelFormRef" label-width="130px">
        <el-collapse v-model="personnelCollapseActive">
          <el-collapse-item title="基本信息" name="basic">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="姓名" prop="name">
                  <el-input v-model="personnelForm.name" placeholder="请输入姓名" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="身份证号">
                  <el-input v-model="personnelForm.id_number" placeholder="请输入身份证号" maxlength="18" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="出生年月">
                  <el-date-picker v-model="personnelForm.birth_date" type="month" value-format="YYYY-MM-DD" placeholder="选择出生年月" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="联系电话">
                  <el-input v-model="personnelForm.phone" placeholder="请输入联系电话" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="从事专业年限">
                  <el-input-number v-model="personnelForm.professional_years" :min="0" :max="50" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="是否本单位注册">
                  <el-switch v-model="personnelForm.is_registered_locally" active-text="是" inactive-text="否" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-collapse-item>
          
          <el-collapse-item title="证书信息" name="certificate">
            <el-row :gutter="20">
              <el-col :span="12" v-if="personnelForm.personnel_type === 'project_manager'">
                <el-form-item label="建造师证书">
                  <el-input v-model="personnelForm.builder_certificate" placeholder="请输入建造师证书名称" />
                </el-form-item>
              </el-col>
              <el-col :span="12" v-if="personnelForm.personnel_type === 'project_manager'">
                <el-form-item label="安全生产B证">
                  <el-input v-model="personnelForm.safety_certificate_b" placeholder="请输入安全生产考核合格证B证" />
                </el-form-item>
              </el-col>
              <el-col :span="12" v-if="['technical_director', 'professional_engineer'].includes(personnelForm.personnel_type)">
                <el-form-item label="工程师职称证">
                  <el-input v-model="personnelForm.engineer_title_certificate" placeholder="请输入工程师职称证名称" />
                </el-form-item>
              </el-col>
              <el-col :span="12" v-if="personnelForm.personnel_type === 'eight_officers'">
                <el-form-item label="八大员类型">
                  <el-select v-model="personnelForm.officer_type" placeholder="请选择员种" style="width: 100%">
                    <el-option label="施工员" value="construction" />
                    <el-option label="质量员" value="quality" />
                    <el-option label="安全员" value="safety" />
                    <el-option label="标准员" value="standard" />
                    <el-option label="材料员" value="material" />
                    <el-option label="机械员" value="machinery" />
                    <el-option label="劳务员" value="labor" />
                    <el-option label="资料员" value="data" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="证书编号">
                  <el-input v-model="personnelForm.certificate_number" placeholder="请输入证书编号" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="注册专业">
                  <el-input v-model="personnelForm.certificate_major" placeholder="请输入注册专业" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="职称等级" v-if="['technical_director', 'professional_engineer', 'project_manager'].includes(personnelForm.personnel_type)">
                  <el-select v-model="personnelForm.title_level" placeholder="请选择职称等级" style="width: 100%" clearable>
                    <el-option label="高级" value="senior" />
                    <el-option label="中级" value="intermediate" />
                    <el-option label="初级" value="junior" />
                    <el-option label="助理" value="assistant" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="证书有效期">
                  <el-date-picker v-model="personnelForm.expiry_date" type="date" value-format="YYYY-MM-DD" placeholder="选择有效期" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="发证机关">
                  <el-input v-model="personnelForm.issuing_authority" placeholder="请输入发证机关" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="发证单位全称">
                  <el-input v-model="personnelForm.issuing_authority_full" placeholder="请输入发证单位全称" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-collapse-item>
          
          <el-collapse-item title="证明文件" name="files">
            <el-row :gutter="20">
              <el-col :span="12" v-if="personnelForm.personnel_type === 'project_manager'">
                <el-form-item label="建造师证书文件">
                  <el-upload
                    :auto-upload="false"
                    :limit="1"
                    :on-change="(file) => handlePersonnelFileChange(file, 'builder_certificate_file')"
                    accept=".pdf,.jpg,.jpeg,.png"
                  >
                    <el-button type="primary" size="small">上传文件</el-button>
                  </el-upload>
                  <span v-if="personnelForm.builder_certificate_file_name" class="file-name">{{ personnelForm.builder_certificate_file_name }}</span>
                </el-form-item>
              </el-col>
              <el-col :span="12" v-if="personnelForm.personnel_type === 'project_manager'">
                <el-form-item label="安全生产B证文件">
                  <el-upload
                    :auto-upload="false"
                    :limit="1"
                    :on-change="(file) => handlePersonnelFileChange(file, 'safety_certificate_b_file')"
                    accept=".pdf,.jpg,.jpeg,.png"
                  >
                    <el-button type="primary" size="small">上传文件</el-button>
                  </el-upload>
                  <span v-if="personnelForm.safety_certificate_b_file_name" class="file-name">{{ personnelForm.safety_certificate_b_file_name }}</span>
                </el-form-item>
              </el-col>
              <el-col :span="12" v-if="['technical_director', 'professional_engineer'].includes(personnelForm.personnel_type)">
                <el-form-item label="工程师职称证文件">
                  <el-upload
                    :auto-upload="false"
                    :limit="1"
                    :on-change="(file) => handlePersonnelFileChange(file, 'engineer_certificate_file')"
                    accept=".pdf,.jpg,.jpeg,.png"
                  >
                    <el-button type="primary" size="small">上传文件</el-button>
                  </el-upload>
                  <span v-if="personnelForm.engineer_certificate_file_name" class="file-name">{{ personnelForm.engineer_certificate_file_name }}</span>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="社保缴纳证明">
                  <el-upload
                    :auto-upload="false"
                    :limit="1"
                    :on-change="(file) => handlePersonnelFileChange(file, 'social_security_proof')"
                    accept=".pdf,.jpg,.jpeg,.png"
                  >
                    <el-button type="primary" size="small">上传文件</el-button>
                  </el-upload>
                  <span v-if="personnelForm.social_security_proof_name" class="file-name">{{ personnelForm.social_security_proof_name }}</span>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="无在建承诺">
                  <el-upload
                    :auto-upload="false"
                    :limit="1"
                    :on-change="(file) => handlePersonnelFileChange(file, 'no_ongoing_commitment')"
                    accept=".pdf,.jpg,.jpeg,.png"
                  >
                    <el-button type="primary" size="small">上传文件</el-button>
                  </el-upload>
                  <span v-if="personnelForm.no_ongoing_commitment_name" class="file-name">{{ personnelForm.no_ongoing_commitment_name }}</span>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="劳动合同">
                  <el-upload
                    :auto-upload="false"
                    :limit="1"
                    :on-change="(file) => handlePersonnelFileChange(file, 'labor_contract')"
                    accept=".pdf,.jpg,.jpeg,.png"
                  >
                    <el-button type="primary" size="small">上传文件</el-button>
                  </el-upload>
                  <span v-if="personnelForm.labor_contract_name" class="file-name">{{ personnelForm.labor_contract_name }}</span>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="类似业绩证明">
                  <el-upload
                    :auto-upload="false"
                    :limit="1"
                    :on-change="(file) => handlePersonnelFileChange(file, 'similar_performance_proof')"
                    accept=".pdf,.jpg,.jpeg,.png"
                  >
                    <el-button type="primary" size="small">上传文件</el-button>
                  </el-upload>
                  <span v-if="personnelForm.similar_performance_proof_name" class="file-name">{{ personnelForm.similar_performance_proof_name }}</span>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="社保验证码">
                  <el-input v-model="personnelForm.social_security_code" placeholder="部分地区社保系统支持验证码" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-collapse-item>
          
          <el-collapse-item title="其他信息" name="other">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="是否可用">
                  <el-switch v-model="personnelForm.is_available" active-text="可用" inactive-text="不可用" />
                </el-form-item>
              </el-col>
              <el-col :span="24">
                <el-form-item label="备注">
                  <el-input v-model="personnelForm.remarks" type="textarea" :rows="3" placeholder="请输入备注信息" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-collapse-item>
        </el-collapse>
      </el-form>
      <template #footer>
        <el-button @click="personnelDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePersonnel" :loading="personnelSaving">保存</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="qualificationDialogVisible" :title="qualificationDialogTitle" width="700px" destroy-on-close>
      <el-form :model="qualificationForm" :rules="qualificationFormRules" ref="qualificationFormRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="资质类别" prop="qualification_category">
              <el-select v-model="qualificationForm.qualification_category" placeholder="请选择资质类别" style="width: 100%" @change="onQualificationCategoryChange">
                <el-option label="工程勘察" value="survey" />
                <el-option label="工程设计" value="design" />
                <el-option label="建筑业企业" value="construction" />
                <el-option label="工程监理" value="supervision" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="资质名称" prop="qualification_name">
              <el-select v-model="qualificationForm.qualification_name" placeholder="请先选择资质类别" style="width: 100%" :disabled="!qualificationForm.qualification_category">
                <el-option-group v-if="qualificationForm.qualification_category === 'survey'" label="综合资质">
                  <el-option label="综合资质（工程勘察）" value="survey_comprehensive" />
                </el-option-group>
                <el-option-group v-if="qualificationForm.qualification_category === 'survey'" label="岩土工程专业">
                  <el-option label="岩土工程专业" value="survey_geotechnical" />
                  <el-option label="岩土工程勘察" value="survey_geotechnical_survey" />
                  <el-option label="岩土工程设计" value="survey_geotechnical_design" />
                  <el-option label="岩土工程物探测试检测监测" value="survey_geotechnical_testing" />
                </el-option-group>
                <el-option-group v-if="qualificationForm.qualification_category === 'survey'" label="其他专业">
                  <el-option label="水文地质勘察专业" value="survey_hydrogeology" />
                  <el-option label="工程测量专业" value="survey_engineering_measurement" />
                </el-option-group>
                <el-option-group v-if="qualificationForm.qualification_category === 'survey'" label="劳务资质">
                  <el-option label="工程钻探" value="survey_labor_drilling" />
                  <el-option label="凿井" value="survey_labor_well" />
                </el-option-group>
                <el-option-group v-if="qualificationForm.qualification_category === 'design'" label="综合资质">
                  <el-option label="综合资质（工程设计）" value="design_comprehensive" />
                </el-option-group>
                <el-option-group v-if="qualificationForm.qualification_category === 'design'" label="行业资质">
                  <el-option label="建筑行业（含人防工程）" value="design_industry_building" />
                  <el-option label="市政行业" value="design_industry_municipal" />
                  <el-option label="水利行业" value="design_industry_water_conservancy" />
                  <el-option label="电力行业（限送变电）" value="design_industry_power" />
                  <el-option label="公路行业" value="design_industry_highway" />
                  <el-option label="煤炭行业" value="design_industry_coal" />
                  <el-option label="化工石化医药行业" value="design_industry_chemical" />
                  <el-option label="石油天然气行业" value="design_industry_petroleum" />
                  <el-option label="冶金行业" value="design_industry_metallurgy" />
                  <el-option label="军工行业" value="design_industry_military" />
                  <el-option label="机械行业" value="design_industry_mechanical" />
                  <el-option label="商物粮行业" value="design_industry_commerce" />
                  <el-option label="核工业行业" value="design_industry_nuclear" />
                  <el-option label="电子通信广电行业" value="design_industry_electronics" />
                  <el-option label="轻纺行业" value="design_industry_textile" />
                  <el-option label="建材行业" value="design_industry_building_materials" />
                  <el-option label="铁道行业" value="design_industry_railway" />
                  <el-option label="水运行业" value="design_industry_water_transport" />
                  <el-option label="民航行业" value="design_industry_civil_aviation" />
                  <el-option label="农林行业" value="design_industry_agriculture_forestry" />
                  <el-option label="海洋行业" value="design_industry_ocean" />
                </el-option-group>
                <el-option-group v-if="qualificationForm.qualification_category === 'design'" label="专业资质">
                  <el-option label="建筑工程专业" value="design_professional_building" />
                  <el-option label="煤炭行业专业" value="design_professional_coal" />
                  <el-option label="电力行业专业" value="design_professional_power" />
                  <el-option label="化工石化医药行业专业" value="design_professional_chemical" />
                  <el-option label="石油天然气行业专业" value="design_professional_petroleum" />
                  <el-option label="冶金行业专业" value="design_professional_metallurgy" />
                  <el-option label="机械行业专业" value="design_professional_mechanical" />
                  <el-option label="市政行业专业" value="design_professional_municipal" />
                  <el-option label="水利行业专业" value="design_professional_water_conservancy" />
                  <el-option label="公路行业专业" value="design_professional_highway" />
                </el-option-group>
                <el-option-group v-if="qualificationForm.qualification_category === 'design'" label="专项资质">
                  <el-option label="建筑装饰工程设计专项" value="design_special_decoration" />
                  <el-option label="建筑幕墙工程设计专项" value="design_special_curtain_wall" />
                  <el-option label="轻型钢结构工程设计专项" value="design_special_light_steel" />
                  <el-option label="建筑智能化系统设计专项" value="design_special_intelligent" />
                  <el-option label="照明工程设计专项" value="design_special_lighting" />
                  <el-option label="消防设施工程设计专项" value="design_special_fire_protection" />
                  <el-option label="风景园林工程设计专项" value="design_special_landscape" />
                </el-option-group>
                <el-option-group v-if="qualificationForm.qualification_category === 'construction'" label="施工总承包">
                  <el-option label="建筑工程施工总承包" value="construction_general_building" />
                  <el-option label="公路工程施工总承包" value="construction_general_highway" />
                  <el-option label="铁路工程施工总承包" value="construction_general_railway" />
                  <el-option label="港口与航道工程施工总承包" value="construction_general_port_waterway" />
                  <el-option label="水利水电工程施工总承包" value="construction_general_water_hydro" />
                  <el-option label="电力工程施工总承包" value="construction_general_power" />
                  <el-option label="矿山工程施工总承包" value="construction_general_mining" />
                  <el-option label="冶金工程施工总承包" value="construction_general_metallurgy" />
                  <el-option label="石油化工工程施工总承包" value="construction_general_petrochemical" />
                  <el-option label="市政公用工程施工总承包" value="construction_general_municipal" />
                  <el-option label="通信工程施工总承包" value="construction_general_communication" />
                  <el-option label="机电工程施工总承包" value="construction_general_mechanical" />
                </el-option-group>
                <el-option-group v-if="qualificationForm.qualification_category === 'construction'" label="专业承包">
                  <el-option label="地基基础工程专业承包" value="construction_special_foundation" />
                  <el-option label="起重设备安装工程专业承包" value="construction_special_hoisting" />
                  <el-option label="预拌混凝土专业承包" value="construction_special_concrete" />
                  <el-option label="电子与智能化工程专业承包" value="construction_special_electronic_intelligent" />
                  <el-option label="消防设施工程专业承包" value="construction_special_fire_protection" />
                  <el-option label="防水防腐保温工程专业承包" value="construction_special_waterproof" />
                  <el-option label="桥梁工程专业承包" value="construction_special_bridge" />
                  <el-option label="隧道工程专业承包" value="construction_special_tunnel" />
                  <el-option label="钢结构工程专业承包" value="construction_special_steel_structure" />
                  <el-option label="模板脚手架专业承包" value="construction_special_scaffolding" />
                  <el-option label="建筑装修装饰工程专业承包" value="construction_special_decoration" />
                  <el-option label="建筑机电安装工程专业承包" value="construction_special_building_electrical" />
                  <el-option label="建筑幕墙工程专业承包" value="construction_special_curtain_wall" />
                  <el-option label="古建筑工程专业承包" value="construction_special_ancient_building" />
                  <el-option label="城市及道路照明工程专业承包" value="construction_special_lighting" />
                  <el-option label="公路路面工程专业承包" value="construction_special_road_surface" />
                  <el-option label="公路路基工程专业承包" value="construction_special_road_subgrade" />
                  <el-option label="公路交通工程专业承包" value="construction_special_highway_traffic" />
                  <el-option label="铁路电务工程专业承包" value="construction_special_railway_signal" />
                  <el-option label="铁路铺轨架梁工程专业承包" value="construction_special_railway_tracks" />
                  <el-option label="铁路电气化工程专业承包" value="construction_special_railway_electrification" />
                  <el-option label="机场场道工程专业承包" value="construction_special_airport_runway" />
                  <el-option label="民航空管工程及机场弱电系统工程专业承包" value="construction_special_airport_weak" />
                  <el-option label="机场目视助航工程专业承包" value="construction_special_airport_visual" />
                  <el-option label="港口与海岸工程专业承包" value="construction_special_port_coast" />
                  <el-option label="航道工程专业承包" value="construction_special_waterway" />
                  <el-option label="通航建筑物工程专业承包" value="construction_special_navigation" />
                  <el-option label="港航设备安装及水上交管工程专业承包" value="construction_special_port_equipment" />
                  <el-option label="水工金属结构制作与安装工程专业承包" value="construction_special_metal_structure" />
                  <el-option label="水利水电机电安装工程专业承包" value="construction_special_hydro_electrical" />
                  <el-option label="河湖整治工程专业承包" value="construction_special_river_lake" />
                  <el-option label="输变电工程专业承包" value="construction_special_power_transmission" />
                  <el-option label="核工程专业承包" value="construction_special_nuclear" />
                  <el-option label="海洋石油工程专业承包" value="construction_special_ocean_oil" />
                  <el-option label="环保工程专业承包" value="construction_special_environmental" />
                  <el-option label="特种工程专业承包" value="construction_special_special" />
                </el-option-group>
                <el-option-group v-if="qualificationForm.qualification_category === 'construction'" label="施工劳务">
                  <el-option label="施工劳务资质" value="construction_labor" />
                </el-option-group>
                <el-option-group v-if="qualificationForm.qualification_category === 'supervision'" label="工程监理">
                  <el-option label="综合资质" value="supervision_comprehensive" />
                  <el-option label="专业资质" value="supervision_professional" />
                </el-option-group>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="资质等级">
              <el-select v-model="qualificationForm.grade" placeholder="请先选择资质名称" style="width: 100%" :disabled="!qualificationForm.qualification_name">
                <el-option-group v-if="['survey_comprehensive'].includes(qualificationForm.qualification_name)" label="综合资质">
                  <el-option label="甲级" value="survey_first" />
                </el-option-group>
                <el-option-group v-if="['survey_geotechnical'].includes(qualificationForm.qualification_name)" label="岩土工程专业">
                  <el-option label="甲级" value="survey_first" />
                  <el-option label="乙级" value="survey_second" />
                  <el-option label="丙级" value="survey_third" />
                </el-option-group>
                <el-option-group v-if="['survey_geotechnical_survey'].includes(qualificationForm.qualification_name)" label="岩土工程勘察">
                  <el-option label="甲级" value="survey_first" />
                  <el-option label="乙级" value="survey_second" />
                  <el-option label="丙级" value="survey_third" />
                </el-option-group>
                <el-option-group v-if="['survey_geotechnical_design', 'survey_geotechnical_testing'].includes(qualificationForm.qualification_name)" label="岩土工程分项">
                  <el-option label="甲级" value="survey_first" />
                  <el-option label="乙级" value="survey_second" />
                </el-option-group>
                <el-option-group v-if="['survey_hydrogeology', 'survey_engineering_measurement'].includes(qualificationForm.qualification_name)" label="专业资质">
                  <el-option label="甲级" value="survey_first" />
                  <el-option label="乙级" value="survey_second" />
                  <el-option label="丙级" value="survey_third" />
                </el-option-group>
                <el-option-group v-if="['survey_labor_drilling', 'survey_labor_well'].includes(qualificationForm.qualification_name)" label="劳务资质">
                  <el-option label="不分等级" value="survey_labor" />
                </el-option-group>
                <el-option-group v-if="['design_comprehensive'].includes(qualificationForm.qualification_name)" label="综合资质">
                  <el-option label="甲级" value="design_first" />
                </el-option-group>
                <el-option-group v-if="['design_industry_building', 'design_industry_municipal', 'design_industry_water_conservancy', 'design_industry_power', 'design_industry_highway'].includes(qualificationForm.qualification_name)" label="行业资质">
                  <el-option label="甲级" value="design_first" />
                  <el-option label="乙级" value="design_second" />
                  <el-option label="丙级" value="design_third" />
                </el-option-group>
                <el-option-group v-if="['design_industry_coal', 'design_industry_chemical', 'design_industry_petroleum', 'design_industry_metallurgy', 'design_industry_military', 'design_industry_mechanical', 'design_industry_commerce', 'design_industry_nuclear', 'design_industry_electronics', 'design_industry_textile', 'design_industry_building_materials', 'design_industry_railway', 'design_industry_water_transport', 'design_industry_civil_aviation', 'design_industry_agriculture_forestry', 'design_industry_ocean'].includes(qualificationForm.qualification_name)" label="行业资质">
                  <el-option label="甲级" value="design_first" />
                  <el-option label="乙级" value="design_second" />
                </el-option-group>
                <el-option-group v-if="['design_professional_building'].includes(qualificationForm.qualification_name)" label="专业资质">
                  <el-option label="甲级" value="design_first" />
                  <el-option label="乙级" value="design_second" />
                  <el-option label="丙级" value="design_third" />
                  <el-option label="丁级" value="design_fourth" />
                </el-option-group>
                <el-option-group v-if="['design_professional_coal', 'design_professional_power', 'design_professional_chemical', 'design_professional_petroleum', 'design_professional_metallurgy', 'design_professional_mechanical', 'design_professional_municipal', 'design_professional_water_conservancy', 'design_professional_highway'].includes(qualificationForm.qualification_name)" label="专业资质">
                  <el-option label="甲级" value="design_first" />
                  <el-option label="乙级" value="design_second" />
                  <el-option label="丙级（部分专业）" value="design_third" />
                </el-option-group>
                <el-option-group v-if="['design_special_decoration', 'design_special_curtain_wall', 'design_special_light_steel', 'design_special_intelligent', 'design_special_lighting', 'design_special_fire_protection', 'design_special_landscape'].includes(qualificationForm.qualification_name)" label="专项资质">
                  <el-option label="甲级" value="design_first" />
                  <el-option label="乙级" value="design_second" />
                </el-option-group>
                <el-option-group v-if="['construction_general_building', 'construction_general_highway', 'construction_general_railway', 'construction_general_port_waterway', 'construction_general_water_hydro', 'construction_general_power', 'construction_general_mining', 'construction_general_metallurgy', 'construction_general_petrochemical', 'construction_general_municipal'].includes(qualificationForm.qualification_name)" label="施工总承包">
                  <el-option label="特级" value="special" />
                  <el-option label="一级" value="first" />
                  <el-option label="二级" value="second" />
                  <el-option label="三级" value="third" />
                </el-option-group>
                <el-option-group v-if="['construction_general_communication', 'construction_general_mechanical'].includes(qualificationForm.qualification_name)" label="施工总承包">
                  <el-option label="一级" value="first" />
                  <el-option label="二级" value="second" />
                  <el-option label="三级" value="third" />
                </el-option-group>
                <el-option-group v-if="['construction_special_foundation', 'construction_special_hoisting', 'construction_special_electronic_intelligent', 'construction_special_fire_protection', 'construction_special_waterproof', 'construction_special_bridge', 'construction_special_tunnel', 'construction_special_steel_structure', 'construction_special_decoration', 'construction_special_building_electrical', 'construction_special_curtain_wall', 'construction_special_ancient_building', 'construction_special_lighting', 'construction_special_road_surface', 'construction_special_road_subgrade', 'construction_special_railway_signal', 'construction_special_railway_tracks', 'construction_special_railway_electrification', 'construction_special_airport_runway', 'construction_special_airport_weak', 'construction_special_airport_visual', 'construction_special_port_coast', 'construction_special_waterway', 'construction_special_navigation', 'construction_special_port_equipment', 'construction_special_metal_structure', 'construction_special_hydro_electrical', 'construction_special_river_lake', 'construction_special_power_transmission', 'construction_special_nuclear', 'construction_special_ocean_oil', 'construction_special_environmental'].includes(qualificationForm.qualification_name)" label="专业承包">
                  <el-option label="一级" value="first" />
                  <el-option label="二级" value="second" />
                  <el-option label="三级" value="third" />
                </el-option-group>
                <el-option-group v-if="['construction_special_highway_traffic'].includes(qualificationForm.qualification_name)" label="专业承包">
                  <el-option label="一级" value="first" />
                  <el-option label="二级" value="second" />
                </el-option-group>
                <el-option-group v-if="['construction_special_concrete', 'construction_special_scaffolding', 'construction_special_special'].includes(qualificationForm.qualification_name)" label="专业承包">
                  <el-option label="不分等级" value="no_level" />
                </el-option-group>
                <el-option-group v-if="['construction_labor'].includes(qualificationForm.qualification_name)" label="施工劳务">
                  <el-option label="不分等级" value="no_level" />
                </el-option-group>
                <el-option-group v-if="['supervision_comprehensive'].includes(qualificationForm.qualification_name)" label="综合资质">
                  <el-option label="不分等级" value="supervision_no_level" />
                </el-option-group>
                <el-option-group v-if="['supervision_professional'].includes(qualificationForm.qualification_name)" label="专业资质">
                  <el-option label="甲级" value="supervision_first" />
                  <el-option label="乙级" value="supervision_second" />
                  <el-option label="丙级（部分专业）" value="supervision_third" />
                </el-option-group>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="资质证书号">
              <el-input v-model="qualificationForm.certificate_no" placeholder="请输入资质证书号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="发证日期">
              <el-date-picker v-model="qualificationForm.issue_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="有效期至">
              <el-date-picker v-model="qualificationForm.expiry_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="发证机关">
              <el-input v-model="qualificationForm.issuing_authority" placeholder="请输入发证机关" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否有效">
              <el-switch v-model="qualificationForm.is_valid" active-text="有效" inactive-text="无效" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="主要资质">
              <el-switch v-model="qualificationForm.is_primary" active-text="是" inactive-text="否" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="qualificationDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveQualification" :loading="qualificationSaving">保存</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="performanceDialogVisible" :title="performanceDialogTitle" width="800px" destroy-on-close>
      <el-form :model="performanceForm" :rules="performanceFormRules" ref="performanceFormRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="项目名称" prop="project_name">
              <el-input v-model="performanceForm.project_name" placeholder="请输入项目名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="项目编号">
              <el-input v-model="performanceForm.project_code" placeholder="请输入项目编号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="业主名称" prop="client_name">
              <el-input v-model="performanceForm.client_name" placeholder="请输入业主名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="合同金额">
              <el-input-number v-model="performanceForm.contract_amount" :min="0" :precision="2" style="width: 100%" placeholder="万元" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结算金额">
              <el-input-number v-model="performanceForm.settlement_amount" :min="0" :precision="2" style="width: 100%" placeholder="万元" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="开工日期">
              <el-date-picker v-model="performanceForm.start_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="完工日期">
              <el-date-picker v-model="performanceForm.end_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="项目经理">
              <el-input v-model="performanceForm.project_manager" placeholder="请输入项目经理姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="技术负责人">
              <el-input v-model="performanceForm.technical_director" placeholder="请输入技术负责人姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="项目地点">
              <el-input v-model="performanceForm.project_location" placeholder="请输入项目地点" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="项目描述">
              <el-input v-model="performanceForm.description" type="textarea" :rows="3" placeholder="请输入项目描述" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="performanceDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePerformance" :loading="performanceSaving">保存</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="contactDialogVisible" :title="contactDialogTitle" width="600px" destroy-on-close>
      <el-form :model="contactForm" :rules="contactFormRules" ref="contactFormRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="姓名" prop="name">
              <el-input v-model="contactForm.name" placeholder="请输入姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系人类型" prop="contact_type">
              <el-select v-model="contactForm.contact_type" placeholder="请选择类型" style="width: 100%">
                <el-option label="商务联系人" value="business" />
                <el-option label="技术联系人" value="technical" />
                <el-option label="财务联系人" value="finance" />
                <el-option label="法务联系人" value="legal" />
                <el-option label="其他联系人" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="职位">
              <el-input v-model="contactForm.position" placeholder="请输入职位" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电话">
              <el-input v-model="contactForm.phone" placeholder="请输入电话" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手机">
              <el-input v-model="contactForm.mobile" placeholder="请输入手机号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮箱">
              <el-input v-model="contactForm.email" placeholder="请输入邮箱" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="地址">
              <el-input v-model="contactForm.address" placeholder="请输入地址" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="主要联系人">
              <el-switch v-model="contactForm.is_primary" active-text="是" inactive-text="否" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-switch v-model="contactForm.is_active" active-text="有效" inactive-text="无效" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="contactForm.remarks" type="textarea" :rows="2" placeholder="请输入备注" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="contactDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveContact" :loading="contactSaving">保存</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="matchRuleDialogVisible" :title="matchRuleDialogTitle" width="700px" destroy-on-close>
      <el-form :model="matchRuleForm" :rules="matchRuleFormRules" ref="matchRuleFormRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="规则名称" prop="name">
              <el-input v-model="matchRuleForm.name" placeholder="请输入规则名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="规则类型" prop="rule_type">
              <el-select v-model="matchRuleForm.rule_type" placeholder="请选择类型" style="width: 100%">
                <el-option label="关键词匹配" value="keyword" />
                <el-option label="语义匹配" value="semantic" />
                <el-option label="地区匹配" value="region" />
                <el-option label="行业匹配" value="industry" />
                <el-option label="预算匹配" value="budget" />
                <el-option label="资质匹配" value="qualification" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="优先级">
              <el-input-number v-model="matchRuleForm.priority" :min="1" :max="100" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="权重">
              <el-input-number v-model="matchRuleForm.weight" :min="0.1" :max="10" :precision="1" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="关键词" v-if="matchRuleForm.rule_type === 'keyword'">
              <el-select 
                v-model="matchRuleForm.keywords" 
                multiple 
                filterable 
                allow-create 
                default-first-option
                placeholder="输入关键词后回车添加"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12" v-if="matchRuleForm.rule_type === 'region'">
            <el-form-item label="匹配地区">
              <el-cascader
                v-model="matchRuleForm.regions"
                :options="regionData"
                :props="{ multiple: true, expandTrigger: 'hover', value: 'value', label: 'label', children: 'children' }"
                placeholder="选择地区"
                style="width: 100%"
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="12" v-if="matchRuleForm.rule_type === 'budget'">
            <el-form-item label="预算范围(万)">
              <el-slider v-model="matchRuleForm.budget_range" range :max="10000" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="匹配条件">
              <el-input v-model="matchRuleForm.match_condition" type="textarea" :rows="3" placeholder="JSON格式的匹配条件" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="描述">
              <el-input v-model="matchRuleForm.description" type="textarea" :rows="2" placeholder="请输入规则描述" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否启用">
              <el-switch v-model="matchRuleForm.is_active" active-text="启用" inactive-text="禁用" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="matchRuleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveMatchRule" :loading="matchRuleSaving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Connection, Plus, Edit, Delete, OfficeBuilding, Document, 
  Location, Select, Upload, View, Star
} from '@element-plus/icons-vue'
import { enterpriseApi } from '@/api/enterprise'
import { regionData, getRegionValue, parseRegionValue } from '@/utils/regions'
import { getContactTypeText, getMatchRuleTypeText } from '@/store/constants'

const enterpriseList = ref([])
const windowWidth = ref(window.innerWidth)

const responsiveColumn = computed(() => {
  if (windowWidth.value < 768) return 1
  if (windowWidth.value < 1200) return 2
  return 2
})

const handleResize = () => {
  windowWidth.value = window.innerWidth
}

const getRowClassName = ({ row }) => {
  if (selectedEnterprise.value && row.id === selectedEnterprise.value.id) {
    return 'selected-row'
  }
  return ''
}

onMounted(() => {
  fetchEnterpriseList()
  fetchDocumentOptions()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
const selectedEnterprise = ref(null)
const dialogVisible = ref(false)
const isEdit = ref(false)
const activeTab = ref('basic')
const activeCollapse = ref(['basic', 'contact', 'finance', 'other', 'bid'])
const qualifications = ref([])
const performances = ref([])
const keyPersonnel = ref([])

const qualificationLoading = ref(false)
const qualificationDialogVisible = ref(false)
const qualificationSaving = ref(false)
const qualificationFormRef = ref(null)

const performanceLoading = ref(false)
const performanceDialogVisible = ref(false)
const performanceSaving = ref(false)
const performanceFormRef = ref(null)

const personnelLoading = ref(false)
const personnelDialogVisible = ref(false)
const personnelSaving = ref(false)
const personnelFormRef = ref(null)
const personnelCollapseActive = ref(['basic', 'certificate', 'files', 'other'])
const personnelFiles = ref({})

const projectManagers = computed(() => keyPersonnel.value.filter(p => p.personnel_type === 'project_manager'))
const technicalDirectors = computed(() => keyPersonnel.value.filter(p => p.personnel_type === 'technical_director'))
const professionalEngineers = computed(() => keyPersonnel.value.filter(p => p.personnel_type === 'professional_engineer'))
const eightOfficers = computed(() => keyPersonnel.value.filter(p => p.personnel_type === 'eight_officers'))

const personnelDialogTitle = computed(() => {
  const titles = {
    'project_manager': '项目经理',
    'technical_director': '技术负责人',
    'professional_engineer': '专业工程师',
    'eight_officers': '八大员'
  }
  return (personnelForm.id ? '编辑' : '添加') + (titles[personnelForm.personnel_type] || '人员')
})

const defaultPersonnelForm = {
  id: null,
  enterprise: null,
  personnel_type: '',
  officer_type: '',
  name: '',
  id_number: '',
  birth_date: '',
  builder_certificate: '',
  safety_certificate_b: '',
  engineer_title_certificate: '',
  certificate_number: '',
  certificate_major: '',
  expiry_date: '',
  issuing_authority: '',
  issuing_authority_full: '',
  title_level: '',
  is_registered_locally: true,
  social_security_code: '',
  professional_years: null,
  phone: '',
  is_available: true,
  remarks: ''
}

const personnelForm = reactive({ ...defaultPersonnelForm })

const personnelFormRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }]
}

const qualificationDialogTitle = computed(() => qualificationForm.id ? '编辑资质信息' : '添加资质信息')

const defaultQualificationForm = {
  id: null,
  enterprise: null,
  qualification_category: '',
  qualification_name: '',
  grade: '',
  certificate_no: '',
  issue_date: '',
  expiry_date: '',
  issuing_authority: '',
  is_valid: true,
  is_primary: false
}

const qualificationForm = reactive({ ...defaultQualificationForm })

const qualificationFormRules = {
  qualification_category: [{ required: true, message: '请选择资质类别', trigger: 'change' }],
  qualification_name: [{ required: true, message: '请选择资质名称', trigger: 'change' }]
}

const performanceDialogTitle = computed(() => performanceForm.id ? '编辑业绩信息' : '添加业绩信息')

const defaultPerformanceForm = {
  id: null,
  enterprise: null,
  project_name: '',
  project_code: '',
  client_name: '',
  contract_amount: null,
  settlement_amount: null,
  start_date: '',
  end_date: '',
  project_manager: '',
  technical_director: '',
  project_location: '',
  description: ''
}

const performanceForm = reactive({ ...defaultPerformanceForm })

const performanceFormRules = {
  project_name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  client_name: [{ required: true, message: '请输入业主名称', trigger: 'blur' }]
}

const documentList = ref([])
const documentsLoading = ref(false)
const documentFilterType = ref('')
const documentFilterStatus = ref('')
const documentDialogVisible = ref(false)
const documentSubmitting = ref(false)
const previewDialogVisible = ref(false)
const previewUrl = ref('')
const previewType = ref('')
const previewDoc = ref(null)
const documentFormRef = ref(null)
const documentUploadRef = ref(null)
const selectedDocumentFile = ref(null)
const documentOptions = ref({
  document_types: {},
  document_statuses: {}
})

const documentTypeOptions = computed(() => {
  const options = documentOptions.value
  if (!options) return []
  const types = options.document_types || {}
  return Object.entries(types)
    .filter(([value]) => value !== undefined && value !== null && value !== '')
    .map(([value, label]) => ({ value, label }))
})

const documentStatusOptions = computed(() => {
  const options = documentOptions.value
  if (!options) return []
  const statuses = options.document_statuses || {}
  return Object.entries(statuses)
    .filter(([value]) => value !== undefined && value !== null && value !== '')
    .map(([value, label]) => ({ value, label }))
})

const defaultDocumentForm = {
  enterprise: null,
  document_type: '',
  document_name: '',
  document_no: '',
  issue_date: '',
  expiry_date: '',
  file_path: null,
  auto_recognize: false
}

const documentForm = reactive({ ...defaultDocumentForm })

const documentFormRules = {
  document_type: [{ required: true, message: '请选择证书类型', trigger: 'change' }],
  document_name: [{ required: true, message: '请输入证书名称', trigger: 'blur' }]
}

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

const enterpriseForm = reactive({ ...defaultForm })

const regionValue = ref([])

const handleRegionChange = (value) => {
  const parsed = parseRegionValue(value)
  enterpriseForm.province = parsed.province
  enterpriseForm.city = parsed.city
  enterpriseForm.district = parsed.district
}

const fetchEnterpriseList = async () => {
  try {
    const res = await enterpriseApi.getEnterprises()
    enterpriseList.value = res.data?.list || res.results || res.data || []
    if (enterpriseList.value.length > 0) {
      selectEnterprise(enterpriseList.value[0])
    }
  } catch (error) {
    console.error('获取企业列表失败:', error)
    ElMessage.error('获取企业列表失败')
  }
}

const selectEnterprise = async (row) => {
  selectedEnterprise.value = row
  await fetchQualifications(row.id)
  await fetchPerformances(row.id)
  await fetchKeyPersonnel(row.id)
  await fetchDocuments()
  await fetchContacts(row.id)
  await fetchMatchRules(row.id)
}

const fetchKeyPersonnel = async (enterpriseId) => {
  try {
    const res = await enterpriseApi.getKeyPersonnel({ enterprise: enterpriseId })
    keyPersonnel.value = res.data?.list || res.results || res.data || []
  } catch (error) {
    console.error('获取关键人员信息失败:', error)
    keyPersonnel.value = []
  }
}

const fetchQualifications = async (enterpriseId) => {
  try {
    const res = await enterpriseApi.getQualifications({ enterprise: enterpriseId })
    qualifications.value = res.data?.list || res.results || res.data || []
  } catch (error) {
    console.error('获取资质信息失败:', error)
    qualifications.value = []
  }
}

const fetchPerformances = async (enterpriseId) => {
  try {
    const res = await enterpriseApi.getPerformances({ enterprise: enterpriseId })
    performances.value = res.data?.list || res.results || res.data || []
  } catch (error) {
    console.error('获取业绩记录失败:', error)
    performances.value = []
  }
}

const fetchDocumentOptions = async () => {
  try {
    const res = await enterpriseApi.getDocumentOptions()
    documentOptions.value = res?.data || res || { document_types: {}, document_statuses: {} }
  } catch (error) {
    console.error('获取文档选项失败:', error)
    documentOptions.value = { document_types: {}, document_statuses: {} }
  }
}

const fetchDocuments = async () => {
  if (!selectedEnterprise.value) return
  
  documentsLoading.value = true
  try {
    const params = {
      enterprise: selectedEnterprise.value.id,
      page_size: 100
    }
    if (documentFilterType.value) params.document_type = documentFilterType.value
    if (documentFilterStatus.value) params.status = documentFilterStatus.value

    const res = await enterpriseApi.getDocuments(params)
    const rawData = res?.data?.list || res?.list || res?.data?.results || res?.data || []
    documentList.value = Array.isArray(rawData) ? rawData : []
  } catch (error) {
    console.error('获取文档列表失败:', error)
    documentList.value = []
  } finally {
    documentsLoading.value = false
  }
}

const showUploadDocumentDialog = () => {
  if (!selectedEnterprise.value) {
    ElMessage.warning('请先选择企业')
    return
  }
  Object.assign(documentForm, { ...defaultDocumentForm, enterprise: selectedEnterprise.value.id })
  selectedDocumentFile.value = null
  documentDialogVisible.value = true
}

const handleDocumentFileChange = (file) => {
  selectedDocumentFile.value = file.raw
}

const handleDocumentExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

const submitDocument = async () => {
  if (!documentFormRef.value) return
  
  await documentFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    if (!selectedDocumentFile.value) {
      ElMessage.warning('请选择要上传的文件')
      return
    }
    
    documentSubmitting.value = true
    try {
      const formData = new FormData()
      Object.keys(documentForm).forEach(key => {
        if (documentForm[key] !== null && documentForm[key] !== '' && key !== 'file_path') {
          formData.append(key, documentForm[key])
        }
      })
      
      if (selectedDocumentFile.value) {
        formData.append('file_path', selectedDocumentFile.value)
      }

      await enterpriseApi.createDocument(formData)
      ElMessage.success('上传成功')
      documentDialogVisible.value = false
      fetchDocuments()
    } catch (error) {
      console.error('上传失败:', error)
      ElMessage.error('上传失败')
    } finally {
      documentSubmitting.value = false
    }
  })
}

const previewDocument = (row) => {
  if (!row.file_url) {
    ElMessage.warning('该证书没有可预览的文件')
    return
  }
  
  previewDoc.value = row
  previewUrl.value = row.file_url
  
  const ext = row.file_url.split('.').pop().toLowerCase()
  if (['jpg', 'jpeg', 'png', 'gif'].includes(ext)) {
    previewType.value = 'image'
  } else if (ext === 'pdf') {
    previewType.value = 'pdf'
  } else {
    previewType.value = 'unsupported'
  }
  
  previewDialogVisible.value = true
}

const downloadDocument = (row) => {
  if (!row.file_url) {
    ElMessage.warning('该证书没有可下载的文件')
    return
  }
  
  const link = document.createElement('a')
  link.href = row.file_url
  link.download = row.document_name
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const deleteDocument = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除证书"${row.document_name}"吗？删除后无法恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await enterpriseApi.deleteDocument(row.id)
    ElMessage.success('删除成功')
    fetchDocuments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const getDocumentStatusType = (status) => {
  const types = {
    valid: 'success',
    expiring: 'warning',
    expired: 'danger',
    pending: 'info'
  }
  return types[status] || 'info'
}

const getDocumentExpiryClass = (row) => {
  if (!row.expiry_date) return ''
  if (row.status === 'expired') return 'expiry-expired'
  if (row.status === 'expiring') return 'expiry-expiring'
  return ''
}

const showCreateDialog = () => {
  isEdit.value = false
  Object.assign(enterpriseForm, { ...defaultForm })
  regionValue.value = []
  activeCollapse.value = ['basic', 'contact', 'finance', 'other', 'bid']
  dialogVisible.value = true
}

const editEnterprise = (row) => {
  isEdit.value = true
  
  Object.assign(enterpriseForm, defaultForm)
  
  Object.keys(row).forEach(key => {
    if (key in enterpriseForm) {
      const value = row[key]
      if (Array.isArray(value) && typeof enterpriseForm[key] === 'string') {
        console.warn(`${key}字段收到数组值，已忽略:`, value)
        return
      }
      enterpriseForm[key] = value
    }
  })
  
  enterpriseForm.id = row.id
  
  regionValue.value = getRegionValue(row.province, row.city, row.district)
  
  activeCollapse.value = ['basic', 'contact', 'finance', 'other', 'bid']
  dialogVisible.value = true
}

const saveEnterprise = async () => {
  if (!enterpriseForm.name) {
    ElMessage.warning('请输入企业名称')
    return
  }
  
  try {
    const submitData = { ...enterpriseForm }
    
    const numericFields = ['registered_capital', 'staff_count', 'insured_count', 'auto_bid_threshold']
    numericFields.forEach(field => {
      const value = submitData[field]
      if (value === '' || value === undefined || value === null || (typeof value === 'string' && value.trim() === '')) {
        submitData[field] = null
      } else if (typeof value === 'string' && value !== '') {
        const num = Number(value)
        submitData[field] = isNaN(num) ? null : num
      } else if (typeof value === 'number' && isNaN(value)) {
        submitData[field] = null
      }
    })
    
    const emptyStringFields = ['credit_code', 'legal_person',
      'province', 'city', 'district', 'address', 'contact_person', 'contact_phone',
      'contact_email', 'bank_name', 'bank_account', 'enterprise_type',
      'enterprise_scale', 'business_scope']
    emptyStringFields.forEach(field => {
      if (submitData[field] === '') {
        submitData[field] = null
      }
    })
    
    const dateFields = ['establishment_date']
    dateFields.forEach(field => {
      if (submitData[field] === '' || submitData[field] === undefined || submitData[field] === null) {
        submitData[field] = null
      }
    })
    
    if (isEdit.value) {
      await enterpriseApi.updateEnterprise(enterpriseForm.id, submitData)
    } else {
      const res = await enterpriseApi.createEnterprise(submitData)
      enterpriseForm.id = res.data?.id || res.id
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await fetchEnterpriseList()
    if (enterpriseForm.id) {
      const savedEnterprise = enterpriseList.value.find(e => e.id === enterpriseForm.id)
      if (savedEnterprise) {
        selectEnterprise(savedEnterprise)
      }
    }
  } catch (error) {
    ElMessage.error('保存失败: ' + (error.response?.data?.message || error.message))
  }
}

const deleteEnterprise = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除企业"${row.name}"吗？删除后无法恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await enterpriseApi.deleteEnterprise(row.id)
    ElMessage.success('删除成功')
    if (selectedEnterprise.value?.id === row.id) {
      selectedEnterprise.value = null
    }
    fetchEnterpriseList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const showCollectPlaceholder = () => {
  ElMessage.info('采集功能开发中，敬请期待')
}

const showAddQualificationDialog = () => {
  if (!selectedEnterprise.value) {
    ElMessage.warning('请先选择企业')
    return
  }
  Object.assign(qualificationForm, { ...defaultQualificationForm, enterprise: selectedEnterprise.value.id })
  qualificationDialogVisible.value = true
}

const editQualification = (row) => {
  Object.assign(qualificationForm, { ...defaultQualificationForm })
  Object.keys(row).forEach(key => {
    if (key in qualificationForm) {
      const value = row[key]
      if (Array.isArray(value) && typeof qualificationForm[key] === 'string') {
        console.warn(`${key}字段收到数组值，已忽略:`, value)
        return
      }
      qualificationForm[key] = value
    }
  })
  qualificationForm.id = row.id
  qualificationDialogVisible.value = true
}

const deleteQualification = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除资质"${row.qualification_name_display || row.qualification_name}"吗？删除后无法恢复。`,
      '删除确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await enterpriseApi.deleteQualification(row.id)
    ElMessage.success('删除成功')
    if (selectedEnterprise.value) {
      fetchQualifications(selectedEnterprise.value.id)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const onQualificationCategoryChange = () => {
  qualificationForm.qualification_name = ''
}

const saveQualification = async () => {
  if (!qualificationFormRef.value) return

  await qualificationFormRef.value.validate(async (valid) => {
    if (!valid) return

    qualificationSaving.value = true
    try {
      const data = { ...qualificationForm }
      delete data.id

      if (!data.issue_date) data.issue_date = null
      if (!data.expiry_date) data.expiry_date = null

      if (qualificationForm.id) {
        await enterpriseApi.updateQualification(qualificationForm.id, data)
      } else {
        await enterpriseApi.createQualification(data)
      }
      ElMessage.success('保存成功')
      qualificationDialogVisible.value = false
      if (selectedEnterprise.value) {
        fetchQualifications(selectedEnterprise.value.id)
      }
    } catch (error) {
      console.error('保存失败:', error)
      ElMessage.error('保存失败')
    } finally {
      qualificationSaving.value = false
    }
  })
}

const showAddPerformanceDialog = () => {
  if (!selectedEnterprise.value) {
    ElMessage.warning('请先选择企业')
    return
  }
  Object.assign(performanceForm, { ...defaultPerformanceForm, enterprise: selectedEnterprise.value.id })
  performanceDialogVisible.value = true
}

const editPerformance = (row) => {
  Object.assign(performanceForm, { ...defaultPerformanceForm })
  Object.keys(row).forEach(key => {
    if (key in performanceForm) {
      const value = row[key]
      if (Array.isArray(value) && typeof performanceForm[key] === 'string') {
        console.warn(`${key}字段收到数组值，已忽略:`, value)
        return
      }
      performanceForm[key] = value
    }
  })
  performanceForm.id = row.id
  performanceDialogVisible.value = true
}

const deletePerformance = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除业绩"${row.project_name}"吗？删除后无法恢复。`,
      '删除确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await enterpriseApi.deletePerformance(row.id)
    ElMessage.success('删除成功')
    if (selectedEnterprise.value) {
      fetchPerformances(selectedEnterprise.value.id)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const savePerformance = async () => {
  if (!performanceFormRef.value) return
  
  await performanceFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    performanceSaving.value = true
    try {
      const data = { ...performanceForm }
      delete data.id
      
      if (performanceForm.id) {
        await enterpriseApi.updatePerformance(performanceForm.id, data)
      } else {
        await enterpriseApi.createPerformance(data)
      }
      ElMessage.success('保存成功')
      performanceDialogVisible.value = false
      if (selectedEnterprise.value) {
        fetchPerformances(selectedEnterprise.value.id)
      }
    } catch (error) {
      console.error('保存失败:', error)
      ElMessage.error('保存失败')
    } finally {
      performanceSaving.value = false
    }
  })
}

const showAddPersonnelDialog = (personnelType) => {
  if (!selectedEnterprise.value) {
    ElMessage.warning('请先选择企业')
    return
  }
  Object.assign(personnelForm, { ...defaultPersonnelForm, enterprise: selectedEnterprise.value.id, personnel_type: personnelType })
  personnelFiles.value = {}
  personnelCollapseActive.value = ['basic', 'certificate', 'files', 'other']
  personnelDialogVisible.value = true
}

const editPersonnel = (row) => {
  Object.assign(personnelForm, { ...defaultPersonnelForm })
  Object.keys(row).forEach(key => {
    if (key in personnelForm) {
      const value = row[key]
      if (key === 'name' && Array.isArray(value)) {
        console.warn('name字段收到数组值，已忽略:', value)
        return
      }
      personnelForm[key] = value
    }
  })
  personnelForm.id = row.id
  personnelFiles.value = {}
  personnelCollapseActive.value = ['basic', 'certificate', 'files', 'other']
  personnelDialogVisible.value = true
}

const deletePersonnel = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除人员"${row.name}"吗？删除后无法恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await enterpriseApi.deleteKeyPersonnel(row.id)
    ElMessage.success('删除成功')
    if (selectedEnterprise.value) {
      fetchKeyPersonnel(selectedEnterprise.value.id)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handlePersonnelFileChange = (file, field) => {
  personnelFiles.value[field] = file.raw
  personnelForm[`${field}_name`] = file.name
}

const savePersonnel = async () => {
  if (!personnelFormRef.value) return
  
  await personnelFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    personnelSaving.value = true
    try {
      const formData = new FormData()
      Object.keys(personnelForm).forEach(key => {
        if (personnelForm[key] !== null && personnelForm[key] !== '' && !key.endsWith('_name')) {
          formData.append(key, personnelForm[key])
        }
      })
      
      Object.keys(personnelFiles.value).forEach(key => {
        if (personnelFiles.value[key]) {
          formData.append(key, personnelFiles.value[key])
        }
      })

      if (personnelForm.id) {
        await enterpriseApi.updateKeyPersonnel(personnelForm.id, formData)
      } else {
        await enterpriseApi.createKeyPersonnel(formData)
      }
      ElMessage.success('保存成功')
      personnelDialogVisible.value = false
      if (selectedEnterprise.value) {
        fetchKeyPersonnel(selectedEnterprise.value.id)
      }
    } catch (error) {
      console.error('保存失败:', error)
      ElMessage.error('保存失败: ' + (error.response?.data?.message || error.message))
    } finally {
      personnelSaving.value = false
    }
  })
}

const getPersonnelStatusType = (status) => {
  const types = {
    valid: 'success',
    expiring: 'warning',
    expired: 'danger'
  }
  return types[status] || 'info'
}

const getPersonnelExpiryClass = (row) => {
  if (!row.expiry_date) return ''
  if (row.certificate_status === 'expired') return 'expiry-expired'
  if (row.certificate_status === 'expiring') return 'expiry-expiring'
  return ''
}

const contacts = ref([])
const contactsLoading = ref(false)
const contactDialogVisible = ref(false)
const contactSaving = ref(false)
const contactFormRef = ref(null)

const contactDialogTitle = computed(() => contactForm.id ? '编辑联系人' : '添加联系人')

const defaultContactForm = {
  id: null,
  enterprise: null,
  name: '',
  contact_type: 'business',
  position: '',
  phone: '',
  mobile: '',
  email: '',
  address: '',
  is_primary: false,
  is_active: true,
  remarks: ''
}

const contactForm = reactive({ ...defaultContactForm })

const contactFormRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  contact_type: [{ required: true, message: '请选择联系人类型', trigger: 'change' }]
}

const fetchContacts = async (enterpriseId) => {
  contactsLoading.value = true
  try {
    const res = await enterpriseApi.getContacts({ enterprise: enterpriseId })
    contacts.value = res.data?.list || res.results || res.data || []
  } catch (error) {
    console.error('获取联系人信息失败:', error)
    contacts.value = []
  } finally {
    contactsLoading.value = false
  }
}

const showAddContactDialog = () => {
  if (!selectedEnterprise.value) {
    ElMessage.warning('请先选择企业')
    return
  }
  Object.assign(contactForm, { ...defaultContactForm, enterprise: selectedEnterprise.value.id })
  contactDialogVisible.value = true
}

const editContact = (row) => {
  Object.assign(contactForm, { ...defaultContactForm })
  Object.keys(row).forEach(key => {
    if (key in contactForm) {
      const value = row[key]
      if (key === 'name' && Array.isArray(value)) {
        console.warn('name字段收到数组值，已忽略:', value)
        return
      }
      contactForm[key] = value
    }
  })
  contactForm.id = row.id
  contactDialogVisible.value = true
}

const deleteContact = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除联系人"${row.name}"吗？删除后无法恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await enterpriseApi.deleteContact(row.id)
    ElMessage.success('删除成功')
    if (selectedEnterprise.value) {
      fetchContacts(selectedEnterprise.value.id)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const saveContact = async () => {
  if (!contactFormRef.value) return
  
  await contactFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    contactSaving.value = true
    try {
      const data = { ...contactForm }
      delete data.id
      
      if (contactForm.id) {
        await enterpriseApi.updateContact(contactForm.id, data)
      } else {
        await enterpriseApi.createContact(data)
      }
      ElMessage.success('保存成功')
      contactDialogVisible.value = false
      if (selectedEnterprise.value) {
        fetchContacts(selectedEnterprise.value.id)
      }
    } catch (error) {
      console.error('保存失败:', error)
      ElMessage.error('保存失败')
    } finally {
      contactSaving.value = false
    }
  })
}

const matchRules = ref([])
const matchRulesLoading = ref(false)
const matchRuleDialogVisible = ref(false)
const matchRuleSaving = ref(false)
const matchRuleFormRef = ref(null)

const matchRuleDialogTitle = computed(() => matchRuleForm.id ? '编辑匹配规则' : '添加匹配规则')

const defaultMatchRuleForm = {
  id: null,
  enterprise: null,
  name: '',
  rule_type: 'keyword',
  priority: 1,
  weight: 1,
  keywords: [],
  regions: [],
  budget_range: [0, 1000],
  match_condition: '',
  description: '',
  is_active: true
}

const matchRuleForm = reactive({ ...defaultMatchRuleForm })

const matchRuleFormRules = {
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  rule_type: [{ required: true, message: '请选择规则类型', trigger: 'change' }]
}

const fetchMatchRules = async (enterpriseId) => {
  matchRulesLoading.value = true
  try {
    const res = await enterpriseApi.getMatchRules({ enterprise: enterpriseId })
    matchRules.value = res.data?.list || res.results || res.data || []
  } catch (error) {
    console.error('获取匹配规则失败:', error)
    matchRules.value = []
  } finally {
    matchRulesLoading.value = false
  }
}

const showAddMatchRuleDialog = () => {
  if (!selectedEnterprise.value) {
    ElMessage.warning('请先选择企业')
    return
  }
  Object.assign(matchRuleForm, { ...defaultMatchRuleForm, enterprise: selectedEnterprise.value.id })
  matchRuleDialogVisible.value = true
}

const editMatchRule = (row) => {
  Object.assign(matchRuleForm, { ...defaultMatchRuleForm })
  Object.keys(row).forEach(key => {
    if (key in matchRuleForm) {
      const value = row[key]
      if (key === 'name' && Array.isArray(value)) {
        console.warn('name字段收到数组值，已忽略:', value)
        return
      }
      matchRuleForm[key] = value
    }
  })
  matchRuleForm.id = row.id
  matchRuleDialogVisible.value = true
}

const deleteMatchRule = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除匹配规则"${row.name}"吗？删除后无法恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await enterpriseApi.deleteMatchRule(row.id)
    ElMessage.success('删除成功')
    if (selectedEnterprise.value) {
      fetchMatchRules(selectedEnterprise.value.id)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const saveMatchRule = async () => {
  if (!matchRuleFormRef.value) return
  
  await matchRuleFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    matchRuleSaving.value = true
    try {
      const data = { ...matchRuleForm }
      delete data.id
      
      if (matchRuleForm.id) {
        await enterpriseApi.updateMatchRule(matchRuleForm.id, data)
      } else {
        await enterpriseApi.createMatchRule(data)
      }
      ElMessage.success('保存成功')
      matchRuleDialogVisible.value = false
      if (selectedEnterprise.value) {
        fetchMatchRules(selectedEnterprise.value.id)
      }
    } catch (error) {
      console.error('保存失败:', error)
      ElMessage.error('保存失败')
    } finally {
      matchRuleSaving.value = false
    }
  })
}
</script>

<style scoped>
.company-page {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.header-title {
  flex: 1;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.page-subtitle {
  margin: 8px 0 0;
  font-size: 14px;
  opacity: 0.9;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.enterprise-list-section {
  margin-bottom: 24px;
}

.list-card {
  border-radius: 12px;
  overflow: hidden;
}

.list-card :deep(.el-card__header) {
  padding: 16px 20px;
  background-color: #fafafa;
  border-bottom: 1px solid #ebeef5;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.section-title .el-icon {
  font-size: 18px;
  color: #409eff;
}

.enterprise-count {
  font-size: 13px;
  color: #909399;
}

.enterprise-table {
  width: 100%;
}

.enterprise-table :deep(.el-table__row) {
  cursor: pointer;
  transition: background-color 0.2s;
}

.enterprise-table :deep(.el-table__row:hover) {
  background-color: #ecf5ff !important;
}

.enterprise-table :deep(.selected-row) {
  background-color: #e6f7ff !important;
}

.enterprise-table :deep(.selected-row td) {
  background-color: transparent !important;
}

.enterprise-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.enterprise-name {
  font-weight: 500;
}

.verified-tag {
  margin-left: 4px;
}

.enterprise-detail-section {
  margin-bottom: 24px;
}

.detail-card {
  border-radius: 12px;
  overflow: hidden;
}

.detail-card :deep(.el-card__header) {
  padding: 16px 20px;
  background-color: #fafafa;
  border-bottom: 1px solid #ebeef5;
}

.detail-actions {
  display: flex;
  gap: 8px;
}

.detail-tabs {
  padding: 0 4px;
}

.detail-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}

.info-descriptions {
  background-color: #fff;
}

.info-descriptions :deep(.el-descriptions__label) {
  font-weight: 500;
  color: #606266;
  background-color: #fafafa;
  white-space: nowrap;
  width: 110px;
}

.info-value {
  font-weight: 500;
}

.info-value.highlight {
  color: #409eff;
  font-size: 15px;
}

.info-value.capital {
  color: #67c23a;
}

.info-value.phone {
  color: #409eff;
}

.table-container {
  overflow-x: auto;
}

.empty-card {
  border-radius: 12px;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-icon {
  font-size: 64px;
  color: #c0c4cc;
}

.personnel-section {
  padding: 0;
}

.personnel-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

.file-name {
  margin-left: 8px;
  color: #409eff;
  font-size: 12px;
}

.business-scope {
  max-height: 120px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.6;
  padding: 8px 0;
  color: #606266;
}

.documents-section {
  padding: 0;
}

.documents-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.doc-name {
  display: flex;
  align-items: center;
}

.primary-icon {
  color: #E6A23C;
  margin-right: 4px;
}

.expiry-expired {
  color: #F56C6C;
}

.expiry-expiring {
  color: #E6A23C;
}

.form-tip {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}

.preview-container {
  width: 100%;
  height: 70vh;
  display: flex;
  justify-content: center;
  align-items: center;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.preview-unsupported {
  text-align: center;
  color: #909399;
}

.preview-unsupported .el-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.personnel-sub-tabs {
  margin-bottom: 16px;
}

.personnel-section {
  padding: 0;
}

.personnel-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

.file-name {
  margin-left: 8px;
  color: #409eff;
  font-size: 12px;
}

@media screen and (max-width: 1200px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
}

@media screen and (max-width: 768px) {
  .company-page {
    padding: 12px;
  }
  
  .page-header {
    padding: 16px;
  }
  
  .page-title {
    font-size: 20px;
  }
  
  .page-subtitle {
    font-size: 13px;
  }
  
  .header-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .header-actions .el-button {
    width: 100%;
    margin: 0;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .enterprise-count {
    font-size: 12px;
  }
  
  .enterprise-table :deep(.el-table__body-wrapper) {
    overflow-x: auto;
  }
  
  .detail-card :deep(.el-tabs__item) {
    font-size: 13px;
    padding: 0 12px;
  }
}

@media screen and (max-width: 480px) {
  .page-title {
    font-size: 18px;
  }
  
  .section-title {
    font-size: 14px;
  }
  
  .info-descriptions :deep(.el-descriptions__label) {
    min-width: 80px;
  }
}
</style>
