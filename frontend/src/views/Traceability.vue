<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { trace } from '../api'
import { SPECS, LABEL_NAMES, LABEL_TAG_TYPE, WEAR_NAMES } from '../utils/constants'

const filters = ref({
  spec: '',
  workstation_id: '',
  operator: '',
  batch_id: '',
  label: null,
  timeRange: null,
})

const options = ref({ workstations: [], operators: [], batches: [] })

const loading = ref(false)
const summary = ref({ n: 0, pass_rate: null, label_dist: {} })
const totalMatched = ref(0)
const records = ref([])
const detail = ref(null)
const detailVisible = ref(false)

async function loadOptions() {
  // 拉取一批记录用于生成筛选下拉选项
  const resp = await trace({ limit: 1000 })
  const rs = resp.records || []
  options.value = {
    workstations: [...new Set(rs.map((r) => r.workstation_id))].sort(),
    operators: [...new Set(rs.map((r) => r.operator))].sort(),
    batches: [...new Set(rs.map((r) => r.batch_id))].sort(),
  }
}

async function doQuery() {
  loading.value = true
  try {
    const [start, end] = filters.value.timeRange || [null, null]
    const q = {
      spec: filters.value.spec || null,
      workstation_id: filters.value.workstation_id || null,
      operator: filters.value.operator || null,
      batch_id: filters.value.batch_id || null,
      label: filters.value.label,
      start_time: start || null,
      end_time: end || null,
    }
    const resp = await trace(q)
    summary.value = resp.summary
    totalMatched.value = resp.total_matched
    records.value = resp.records || []
    ElMessage.success(`查询完成，匹配 ${resp.total_matched} 条`)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function reset() {
  filters.value = { spec: '', workstation_id: '', operator: '', batch_id: '', label: null, timeRange: null }
  doQuery()
}

function showDetail(row) {
  detail.value = row
  detailVisible.value = true
}

onMounted(() => {
  loadOptions()
  doQuery()
})
</script>

<template>
  <div class="page">
    <h3 class="page-title">工艺追溯查询</h3>

    <el-card shadow="never" class="card">
      <div class="toolbar">
        <el-select v-model="filters.spec" placeholder="螺栓规格" clearable style="width: 120px">
          <el-option v-for="s in SPECS" :key="s" :label="s" :value="s" />
        </el-select>
        <el-select v-model="filters.workstation_id" placeholder="工位" clearable style="width: 130px">
          <el-option v-for="w in options.workstations" :key="w" :label="w" :value="w" />
        </el-select>
        <el-select v-model="filters.operator" placeholder="操作人员" clearable style="width: 120px">
          <el-option v-for="o in options.operators" :key="o" :label="o" :value="o" />
        </el-select>
        <el-select v-model="filters.batch_id" placeholder="物料批次" clearable style="width: 130px">
          <el-option v-for="b in options.batches" :key="b" :label="b" :value="b" />
        </el-select>
        <el-select v-model="filters.label" placeholder="质量结果" clearable style="width: 120px">
          <el-option v-for="(name, k) in LABEL_NAMES" :key="k" :label="name" :value="Number(k)" />
        </el-select>
        <el-date-picker
          v-model="filters.timeRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          value-format="YYYY-MM-DD HH:mm:ss"
          style="width: 360px"
        />
        <el-button type="primary" icon="Search" @click="doQuery">查询</el-button>
        <el-button icon="RefreshLeft" @click="reset">重置</el-button>
      </div>
    </el-card>

    <div class="stat-grid">
      <el-card shadow="never">
        <div class="kpi-label">匹配记录数</div>
        <div class="kpi-value">{{ totalMatched }}</div>
      </el-card>
      <el-card shadow="never">
        <div class="kpi-label">合格率</div>
        <div class="kpi-value">{{ summary.pass_rate == null ? '—' : (summary.pass_rate * 100).toFixed(2) + '%' }}</div>
      </el-card>
      <el-card shadow="never">
        <div class="kpi-label">缺陷分布</div>
        <div class="kpi-dist">
          <el-tag
            v-for="(cnt, name) in summary.label_dist"
            v-show="name !== '合格'"
            :key="name"
            type="danger"
            size="small"
            style="margin: 2px"
          >{{ name }} {{ cnt }}</el-tag>
          <span v-if="!Object.keys(summary.label_dist || {}).some(k => k !== '合格')" style="color:#909399">无缺陷</span>
        </div>
      </el-card>
    </div>

    <el-card shadow="never">
      <el-table
        :data="records"
        border
        size="small"
        v-loading="loading"
        :row-class-name="({ row }) => (row.label !== 0 ? 'defect-row' : '')"
        @row-click="showDetail"
      >
        <el-table-column prop="record_time" label="时间" width="150" />
        <el-table-column prop="id" label="记录ID" width="100" />
        <el-table-column prop="spec" label="规格" width="70" />
        <el-table-column prop="workstation_id" label="工位" width="90" />
        <el-table-column prop="operator" label="操作员" width="80" />
        <el-table-column prop="batch_id" label="批次" width="90" />
        <el-table-column prop="target_torque" label="目标扭矩" width="90" />
        <el-table-column prop="speed" label="转速" width="80">
          <template #default="{ row }">{{ row.speed?.toFixed(0) }}</template>
        </el-table-column>
        <el-table-column prop="wear" label="磨损" width="90">
          <template #default="{ row }">{{ WEAR_NAMES[row.wear] }}</template>
        </el-table-column>
        <el-table-column label="判定" width="90">
          <template #default="{ row }">
            <el-tag :type="LABEL_TAG_TYPE[row.label]" size="small" effect="dark">{{ row.label_name }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top: 8px; color: #909399; font-size: 12px">
        共显示 {{ records.length }} 条（点击行查看追溯详情）；匹配总数 {{ totalMatched }} 条
      </div>
    </el-card>

    <el-dialog v-model="detailVisible" title="记录追溯详情（反向定位）" width="640px">
      <el-descriptions v-if="detail" :column="2" border>
        <el-descriptions-item label="记录ID">{{ detail.id }}</el-descriptions-item>
        <el-descriptions-item label="质量结果">
          <el-tag :type="LABEL_TAG_TYPE[detail.label]" size="small" effect="dark">{{ detail.label_name }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="螺栓规格">{{ detail.spec }}</el-descriptions-item>
        <el-descriptions-item label="性能等级">{{ detail.grade }}</el-descriptions-item>
        <el-descriptions-item label="目标扭矩">{{ detail.target_torque }} N·m</el-descriptions-item>
        <el-descriptions-item label="拧紧转速">{{ detail.speed?.toFixed(1) }} deg/s</el-descriptions-item>
        <el-descriptions-item label="工具磨损">{{ WEAR_NAMES[detail.wear] }}</el-descriptions-item>
        <el-descriptions-item label="环境温度">{{ detail.temp }} ℃</el-descriptions-item>
        <el-descriptions-item label="工位">{{ detail.workstation_name }}（{{ detail.workstation_id }}）</el-descriptions-item>
        <el-descriptions-item label="设备编号">{{ detail.device_no }}</el-descriptions-item>
        <el-descriptions-item label="操作人员">{{ detail.operator }}</el-descriptions-item>
        <el-descriptions-item label="所属车间">{{ detail.workshop }}</el-descriptions-item>
        <el-descriptions-item label="物料批次">{{ detail.batch_id }}</el-descriptions-item>
        <el-descriptions-item label="记录时间">{{ detail.record_time }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<style scoped>
.kpi-label { font-size: 13px; color: #909399; margin-bottom: 6px; }
.kpi-value { font-size: 26px; font-weight: 700; color: #303133; }
.kpi-dist { min-height: 26px; }
:deep(.defect-row) { background: #fef0f0; }
:deep(.el-table__row) { cursor: pointer; }
</style>
