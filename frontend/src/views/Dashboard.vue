<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { stats, trace } from '../api'
import { LABEL_NAMES, LABEL_COLORS } from '../utils/constants'
import ChartBox from '../components/ChartBox.vue'

const loading = ref(false)
const overview = ref({ total: 0, pass_rate: 0, label_dist: {}, pass_rate_by_workstation: {} })
const records = ref([])

// 实时滚动窗口
const feedStart = ref(0)
let timer = null

const feed = computed(() =>
  [...records.value].sort((a, b) => (b.record_time || '').localeCompare(a.record_time || '')).slice(0, 40)
)
const visibleFeed = computed(() => {
  const n = 8
  if (!feed.value.length) return []
  const out = []
  for (let i = 0; i < n; i++) out.push(feed.value[(feedStart.value + i) % feed.value.length])
  return out
})

const labelPieOption = computed(() => {
  const dist = overview.value.label_dist || {}
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['40%', '68%'],
      label: { formatter: '{b}: {c}' },
      data: Object.keys(LABEL_NAMES).map((k) => ({
        name: LABEL_NAMES[k],
        value: dist[LABEL_NAMES[k]] || 0,
        itemStyle: { color: LABEL_COLORS[LABEL_NAMES[k]] },
      })),
    }],
  }
})

const wsBarOption = computed(() => {
  const d = overview.value.pass_rate_by_workstation || {}
  const keys = Object.keys(d).sort()
  return {
    tooltip: { trigger: 'axis', formatter: '{b}<br/>合格率: {c}%' },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: keys },
    yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
    series: [{
      type: 'bar',
      barWidth: 40,
      data: keys.map((k) => +(d[k] * 100).toFixed(1)),
      itemStyle: { color: '#409eff', borderRadius: [4, 4, 0, 0] },
      label: { show: true, position: 'top', formatter: '{c}%' },
    }],
  }
})

const trendOption = computed(() => {
  // 按小时聚合：总拧紧数 / 缺陷数 / 合格率
  const buckets = new Map()
  for (const r of records.value) {
    const h = (r.record_time || '').slice(0, 13) // YYYY-MM-DD HH
    if (!h) continue
    if (!buckets.has(h)) buckets.set(h, { total: 0, defect: 0 })
    const b = buckets.get(h)
    b.total += 1
    if (r.label !== 0) b.defect += 1
  }
  const keys = [...buckets.keys()].sort()
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['拧紧数', '缺陷数'] },
    grid: { left: 40, right: 40, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: keys, axisLabel: { rotate: 45 } },
    yAxis: { type: 'value' },
    series: [
      { name: '拧紧数', type: 'line', smooth: true, data: keys.map((k) => buckets.get(k).total), itemStyle: { color: '#409eff' }, areaStyle: { opacity: 0.15 } },
      { name: '缺陷数', type: 'line', smooth: true, data: keys.map((k) => buckets.get(k).defect), itemStyle: { color: '#f56c6c' } },
    ],
  }
})

async function load() {
  loading.value = true
  try {
    const [s, t] = await Promise.all([stats(), trace({ limit: 100 })])
    overview.value = s
    records.value = t.records || []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  load()
  timer = setInterval(() => { feedStart.value += 1 }, 1500)
})

onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <div class="dash" v-loading="loading">
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-label">总拧紧记录</div>
        <div class="stat-value">{{ overview.total }}</div>
        <div class="stat-unit">条</div>
      </div>
      <div class="stat-card ok">
        <div class="stat-label">整体合格率</div>
        <div class="stat-value">{{ (overview.pass_rate * 100).toFixed(2) }}</div>
        <div class="stat-unit">%</div>
      </div>
      <div class="stat-card defect">
        <div class="stat-label">缺陷记录</div>
        <div class="stat-value">{{ overview.total - Math.round(overview.total * overview.pass_rate) }}</div>
        <div class="stat-unit">条</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">覆盖工位</div>
        <div class="stat-value">{{ Object.keys(overview.pass_rate_by_workstation || {}).length }}</div>
        <div class="stat-unit">个</div>
      </div>
    </div>

    <div class="dash-grid">
      <div class="panel">
        <div class="panel-title">缺陷类型分布</div>
        <ChartBox :option="labelPieOption" height="280px" />
      </div>
      <div class="panel">
        <div class="panel-title">工位合格率排行</div>
        <ChartBox :option="wsBarOption" height="280px" />
      </div>
    </div>

    <div class="dash-grid">
      <div class="panel">
        <div class="panel-title">质量趋势（按小时）</div>
        <ChartBox :option="trendOption" height="260px" />
      </div>
      <div class="panel">
        <div class="panel-title">实时拧紧记录（异常高亮）</div>
        <el-table :data="visibleFeed" size="small" height="260px" :show-header="true">
          <el-table-column prop="record_time" label="时间" width="150" />
          <el-table-column prop="id" label="记录ID" width="100" />
          <el-table-column prop="workstation_id" label="工位" width="90" />
          <el-table-column prop="spec" label="规格" width="70" />
          <el-table-column label="判定">
            <template #default="{ row }">
              <el-tag :type="row.label === 0 ? 'success' : 'danger'" size="small" effect="dark">
                {{ row.label_name }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dash { padding: 16px; background: #0d1b2a; min-height: 100%; }

.stat-card {
  background: linear-gradient(135deg, #12283f, #0d1b2a);
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  padding: 18px;
  color: #dbe7f3;
}
.stat-card.ok { border-color: #2e7d32; }
.stat-card.defect { border-color: #c62828; }
.stat-label { font-size: 13px; color: #7c9cbf; margin-bottom: 8px; }
.stat-value { font-size: 32px; font-weight: 700; color: #fff; }
.stat-unit { font-size: 12px; color: #7c9cbf; margin-top: 4px; }

.dash-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
.panel {
  background: #12283f;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  padding: 14px;
}
.panel-title {
  color: #dbe7f3;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
}
:deep(.el-table) { background: transparent; }
:deep(.el-table th) { background: #152c46; color: #a8c2dc; }
:deep(.el-table tr) { background: transparent; color: #dbe7f3; }
:deep(.el-table td) { border-bottom: 1px solid #1e3a5f; }

@media (max-width: 900px) {
  .dash-grid { grid-template-columns: 1fr; }
}
</style>
