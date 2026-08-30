<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { SPECS, GRADES } from '../utils/constants'

// 演示用基础数据 CRUD：前端 localStorage 持久化，生产环境替换为 MySQL 基础数据服务
// 预置数据对齐 data/business/init.sql
const STORAGE_PREFIX = 'bdm_'

const ROLE_NAMES = {
  operator: '操作工',
  inspector: '质检员',
  engineer: '工艺工程师',
  admin: '管理员',
}

const entities = {
  bolt: {
    title: '螺栓基础信息',
    fields: [
      { key: 'spec', label: '规格', type: 'select', options: SPECS },
      { key: 'grade', label: '等级', type: 'select', options: GRADES },
      { key: 'standard_torque', label: '标准扭矩(N·m)', type: 'number' },
      { key: 'material', label: '材质', type: 'text' },
      { key: 'remark', label: '备注', type: 'text' },
    ],
    seed: [
      { id: 1, spec: 'M12', grade: '8.8', standard_torque: 80, material: '碳钢', remark: '' },
      { id: 2, spec: 'M12', grade: '10.9', standard_torque: 80, material: '合金钢', remark: '' },
      { id: 3, spec: 'M16', grade: '8.8', standard_torque: 180, material: '碳钢', remark: '' },
      { id: 4, spec: 'M16', grade: '10.9', standard_torque: 180, material: '合金钢', remark: '' },
      { id: 5, spec: 'M20', grade: '8.8', standard_torque: 320, material: '碳钢', remark: '' },
      { id: 6, spec: 'M20', grade: '12.9', standard_torque: 320, material: '合金钢', remark: '' },
      { id: 7, spec: 'M24', grade: '8.8', standard_torque: 520, material: '碳钢', remark: '' },
      { id: 8, spec: 'M24', grade: '12.9', standard_torque: 520, material: '合金钢', remark: '' },
    ],
  },
  workstation: {
    title: '工位信息',
    fields: [
      { key: 'name', label: '工位名称', type: 'text' },
      { key: 'device_no', label: '设备编号', type: 'text' },
      { key: 'owner', label: '负责人', type: 'text' },
      { key: 'workshop', label: '所属车间', type: 'text' },
    ],
    seed: [
      { id: 1, name: '一号装配工位', device_no: 'WS-001', owner: '张伟', workshop: '总装一车间' },
      { id: 2, name: '二号装配工位', device_no: 'WS-002', owner: '李强', workshop: '总装一车间' },
      { id: 3, name: '三号装配工位', device_no: 'WS-003', owner: '王芳', workshop: '总装二车间' },
      { id: 4, name: '四号装配工位', device_no: 'WS-004', owner: '刘洋', workshop: '总装二车间' },
    ],
  },
  param: {
    title: '工艺参数基准',
    fields: [
      { key: 'spec', label: '规格', type: 'select', options: SPECS },
      { key: 'target_torque', label: '目标扭矩(N·m)', type: 'number' },
      { key: 'speed', label: '转速(deg/s)', type: 'number' },
      { key: 'feed', label: '进给量(mm)', type: 'number' },
      { key: 'version', label: '版本号', type: 'text' },
      { key: 'status', label: '状态', type: 'select', options: [{ value: 1, label: '启用' }, { value: 0, label: '停用' }] },
    ],
    seed: [
      { id: 1, spec: 'M12', target_torque: 80, speed: 150, feed: 2.0, version: 'V1.0', status: 1 },
      { id: 2, spec: 'M16', target_torque: 180, speed: 140, feed: 2.5, version: 'V1.0', status: 1 },
      { id: 3, spec: 'M20', target_torque: 320, speed: 130, feed: 3.0, version: 'V1.0', status: 1 },
      { id: 4, spec: 'M24', target_torque: 520, speed: 120, feed: 3.5, version: 'V1.0', status: 1 },
    ],
  },
  user: {
    title: '人员信息',
    fields: [
      { key: 'username', label: '用户名', type: 'text' },
      { key: 'role', label: '角色', type: 'select', options: Object.keys(ROLE_NAMES).map((v) => ({ value: v, label: ROLE_NAMES[v] })) },
      { key: 'real_name', label: '姓名', type: 'text' },
    ],
    seed: [
      { id: 1, username: 'operator', role: 'operator', real_name: '张伟' },
      { id: 2, username: 'inspector', role: 'inspector', real_name: '李强' },
      { id: 3, username: 'engineer', role: 'engineer', real_name: '王芳' },
      { id: 4, username: 'admin', role: 'admin', real_name: '刘洋' },
    ],
  },
}

const activeKey = ref('bolt')
const rows = reactive({})
const dialogVisible = ref(false)
const editing = ref(false)
const form = ref({})

function loadRows(key) {
  try {
    const raw = localStorage.getItem(STORAGE_PREFIX + key)
    if (raw) return JSON.parse(raw)
  } catch { /* ignore */ }
  return JSON.parse(JSON.stringify(entities[key].seed))
}

function persist(key) {
  localStorage.setItem(STORAGE_PREFIX + key, JSON.stringify(rows[key]))
}

function init(key) {
  if (!rows[key]) rows[key] = loadRows(key)
}
init(activeKey.value)

const currentRows = computed(() => rows[activeKey.value] || [])
const currentFields = computed(() => entities[activeKey.value].fields)

function onTabChange(key) {
  init(key)
}

function openAdd() {
  editing.value = false
  form.value = {}
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = true
  form.value = JSON.parse(JSON.stringify(row))
  dialogVisible.value = true
}

function save() {
  const key = activeKey.value
  for (const f of currentFields.value) {
    if (f.type === 'number') form.value[f.key] = Number(form.value[f.key] || 0)
  }
  if (editing.value) {
    const i = rows[key].findIndex((r) => r.id === form.value.id)
    if (i >= 0) rows[key][i] = { ...form.value }
  } else {
    const maxId = rows[key].reduce((m, r) => Math.max(m, r.id || 0), 0)
    form.value.id = maxId + 1
    rows[key].push({ ...form.value })
  }
  persist(key)
  dialogVisible.value = false
  ElMessage.success(editing.value ? '已更新' : '已新增')
}

async function remove(row) {
  const key = activeKey.value
  await ElMessageBox.confirm('确定删除该条记录吗？', '提示', { type: 'warning' })
  rows[key] = rows[key].filter((r) => r.id !== row.id)
  persist(key)
  ElMessage.success('已删除')
}

function cellText(field, row) {
  if (field.key === 'role') return ROLE_NAMES[row[field.key]] || row[field.key]
  if (field.key === 'status') return row[field.key] === 1 ? '启用' : '停用'
  return row[field.key]
}
</script>

<template>
  <div class="page">
    <h3 class="page-title">基础数据管理</h3>
    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="演示模式：本页数据仅保存在浏览器 localStorage，生产环境替换为 MySQL 基础数据服务（表结构见 data/business/init.sql）。"
      style="margin-bottom: 12px"
    />

    <el-tabs v-model="activeKey" type="border-card" @tab-change="onTabChange">
      <el-tab-pane v-for="(e, key) in entities" :key="key" :label="e.title" :name="key">
        <div class="toolbar">
          <el-button type="primary" icon="Plus" @click="openAdd">新增</el-button>
        </div>
        <el-table :data="currentRows" border size="default">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column
            v-for="f in currentFields"
            :key="f.key"
            :prop="f.key"
            :label="f.label"
            min-width="120"
          >
            <template #default="{ row }">{{ cellText(f, row) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button link type="danger" @click="remove(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="dialogVisible" :title="(editing ? '编辑' : '新增') + ' - ' + entities[activeKey].title" width="520px">
      <el-form label-width="120px">
        <el-form-item v-for="f in currentFields" :key="f.key" :label="f.label">
          <el-select v-if="f.type === 'select'" v-model="form[f.key]" style="width: 100%">
            <el-option
              v-for="o in f.options"
              :key="o.value !== undefined ? o.value : o"
              :label="o.label !== undefined ? o.label : o"
              :value="o.value !== undefined ? o.value : o"
            />
          </el-select>
          <el-input-number
            v-else-if="f.type === 'number'"
            v-model="form[f.key]"
            :precision="2"
            style="width: 100%"
          />
          <el-input v-else v-model="form[f.key]" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
