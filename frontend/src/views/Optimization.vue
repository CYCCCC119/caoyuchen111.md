<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { optimize, correlation, trace } from '../api'
import { SPECS, WEAR_NAMES } from '../utils/constants'
import ChartBox from '../components/ChartBox.vue'

const spec = ref('M20')
const loading = ref(false)
const optResult = ref(null)
const corr = ref({ param_vs_defect: [], param_vs_feature: [] })
const baseline = ref(null)

const PARAM_LABELS = {
  target_torque: '目标扭矩',
  speed: '拧紧转速',
  wear: '工具磨损',
  temp: '环境温度',
  grade_ordinal: '性能等级',
}

const FEATURE_LABELS = {
  final_torque: '最终扭矩',
  hold_fluctuation: '保持波动',
  angle_deviation: '转角偏差',
  total_angle: '总转角',
  avg_rate: '平均速率',
  rising_slope: '上升斜率',
}

async function load() {
  loading.value = true
  try {
    const [o, c, base] = await Promise.all([
      optimize(spec.value),
      correlation(),
      trace({ spec: spec.value, limit: 1 }),
    ])
    optResult.value = o
    corr.value = c
    baseline.value = base.summary.pass_rate
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

const recommended = computed(() => optResult.value?.recommended)
const improve = computed(() => {
  if (baseline.value == null || !recommended.value) return null
  return ((recommended.value.pass_rate - baseline.value) * 100).toFixed(2)
})

const paretoOption = computed(() => {
  const pts = optResult.value?.pareto_frontier || []
  return {
    tooltip: {
      trigger: 'item',
      formatter: (p) => `转速 ${p.value[0]} deg/s<br/>合格率 ${(p.value[1] * 100).toFixed(1)}%`,
    },
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'value', name: '平均转速 (deg/s)' },
    yAxis: { type: 'value', name: '合格率', axisLabel: { formatter: (v) => (v * 100).toFixed(0) + '%' } },
    series: [{
      type: 'scatter',
      symbolSize: 14,
      data: pts.map((p) => [p.mean_speed, p.pass_rate]),
      itemStyle: { color: '#67c23a' },
    }],
  }
})

const heatmapOption = computed(() => {
  const rows = Object.keys(PARAM_LABELS)
  const cols = Object.keys(FEATURE_LABELS)
  const data = []
  for (const r of corr.value.param_vs_feature || []) {
    const xi = rows.indexOf(r.param)
    const yi = cols.indexOf(r.feature)
    if (xi >= 0 && yi >= 0) data.push([yi, xi, r.corr])
  }
  return {
    tooltip: { formatter: (p) => `${PARAM_LABELS[rows[p.value[1]]]} × ${FEATURE_LABELS[cols[p.value[0]]]}: ${p.value[2]}` },
    grid: { left: 90, right: 20, top: 20, bottom: 60 },
    xAxis: { type: 'category', data: cols.map((c) => FEATURE_LABELS[c]), axisLabel: { rotate: 30 } },
    yAxis: { type: 'category', data: rows.map((r) => PARAM_LABELS[r]) },
    visualMap: {
      min: -1, max: 1, calculable: true, orient: 'horizontal', left: 'center', bottom: 0,
      inRange: { color: ['#409eff', '#f6f6f6', '#f56c6c'] },
    },
    series: [{
      type: 'heatmap',
      data,
      label: { show: true, formatter: (p) => p.value[2].toFixed(2) },
      itemStyle: { borderColor: '#fff', borderWidth: 1 },
    }],
  }
})

const defectBarOption = computed(() => {
  const rows = corr.value.param_vs_defect || []
  const classes = ['with_defect_rate', 'with_欠拧', 'with_过拧', 'with_滑牙', 'with_虚拧']
  const classLabels = ['总体缺陷', '欠拧', '过拧', '滑牙', '虚拧']
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: classLabels, bottom: 0 },
    grid: { left: 90, right: 20, top: 20, bottom: 60 },
    xAxis: { type: 'value', min: -1, max: 1 },
    yAxis: { type: 'category', data: rows.map((r) => PARAM_LABELS[r.param] || r.param) },
    series: classes.map((c, i) => ({
      name: classLabels[i],
      type: 'bar',
      data: rows.map((r) => r[c]),
      barMaxWidth: 14,
    })),
  }
})

onMounted(load)
</script>

<template>
  <div class="page">
    <h3 class="page-title">工艺参数优化</h3>

    <el-card shadow="never" class="card">
      <div class="toolbar">
        <span style="color: #606266">螺栓规格：</span>
        <el-select v-model="spec" style="width: 120px">
          <el-option v-for="s in SPECS" :key="s" :label="s" :value="s" />
        </el-select>
        <el-button type="primary" icon="MagicStick" :loading="loading" @click="load">生成优化方案</el-button>
      </div>
    </el-card>

    <template v-if="recommended">
      <div class="stat-grid">
        <el-card shadow="never">
          <div class="kpi-label">推荐目标扭矩对应工况 · 性能等级</div>
          <div class="kpi-value">{{ recommended.grade }}</div>
        </el-card>
        <el-card shadow="never">
          <div class="kpi-label">工具磨损状态</div>
          <div class="kpi-value">{{ WEAR_NAMES[recommended.wear] }}</div>
        </el-card>
        <el-card shadow="never">
          <div class="kpi-label">推荐转速区间</div>
          <div class="kpi-value" style="font-size: 20px">{{ recommended.speed_range }}</div>
        </el-card>
        <el-card shadow="never">
          <div class="kpi-label">环境温度</div>
          <div class="kpi-value">{{ recommended.temp }} ℃</div>
        </el-card>
      </div>

      <el-card shadow="never" class="card">
        <template #header>优化前后合格率对比（{{ spec }}）</template>
        <div style="display: flex; gap: 40px; align-items: center">
          <div>
            <div class="kpi-label">优化前（当前工况）</div>
            <div class="kpi-value" style="color: #909399">{{ baseline == null ? '—' : (baseline * 100).toFixed(2) + '%' }}</div>
          </div>
          <div>
            <div class="kpi-label">优化后（推荐配置）</div>
            <div class="kpi-value" style="color: #67c23a">{{ (recommended.pass_rate * 100).toFixed(2) + '%' }}</div>
          </div>
          <el-tag v-if="improve !== null" :type="improve >= 0 ? 'success' : 'warning'" size="large">
            提升 {{ improve >= 0 ? '+' : '' }}{{ improve }}%
          </el-tag>
        </div>
      </el-card>

      <div class="dash-grid">
        <el-card shadow="never">
          <template #header>Pareto 前沿（合格率 × 效率）</template>
          <ChartBox :option="paretoOption" height="280px" />
        </el-card>
        <el-card shadow="never">
          <template #header>Top 5 候选配置</template>
          <el-table :data="optResult.top_configs" size="small" border>
            <el-table-column prop="grade" label="等级" width="70" />
            <el-table-column prop="wear" label="磨损" width="90">
              <template #default="{ row }">{{ WEAR_NAMES[row.wear] }}</template>
            </el-table-column>
            <el-table-column prop="temp" label="温度℃" width="70" />
            <el-table-column prop="speed_range" label="转速区间" width="120" />
            <el-table-column prop="pass_rate" label="合格率" width="80">
              <template #default="{ row }">{{ (row.pass_rate * 100).toFixed(1) }}%</template>
            </el-table-column>
            <el-table-column prop="score" label="综合评分" width="80">
              <template #default="{ row }">{{ row.score.toFixed(3) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </template>

    <h4 style="margin: 16px 0 8px">工艺参数 - 质量关联分析</h4>
    <div class="dash-grid">
      <el-card shadow="never">
        <template #header>参数 × 关键质量特征 相关热力图</template>
        <ChartBox :option="heatmapOption" height="320px" />
      </el-card>
      <el-card shadow="never">
        <template #header>参数 × 缺陷类型 相关系数</template>
        <ChartBox :option="defectBarOption" height="320px" />
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.kpi-label { font-size: 13px; color: #909399; margin-bottom: 6px; }
.kpi-value { font-size: 26px; font-weight: 700; color: #303133; }
.dash-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
@media (max-width: 900px) {
  .dash-grid { grid-template-columns: 1fr; }
}
</style>
