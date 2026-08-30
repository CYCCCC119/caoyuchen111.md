<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { detect, detectBatch, ingestFile } from '../api'
import { LABEL_NAMES, LABEL_COLORS, DEFECT_LEVELS, SPECS, LABEL_TAG_TYPE } from '../utils/constants'
import { SAMPLE_CURVES } from '../utils/sampleCurves'
import ChartBox from '../components/ChartBox.vue'

// ---- 单条检测 ----
const spec = ref('M20')
const mode = ref('sample') // sample | csv | manual
const sampleKey = ref('0')
const angleText = ref('')
const torqueText = ref('')
const csvFile = ref(null)

const detecting = ref(false)
const result = ref(null)
// 记录本次输入的原始曲线（后端仅返回特征，绘图需用输入曲线）
const inputCurve = ref({ angle: [], torque: [] })

// ---- 批量检测 ----
const batchDetecting = ref(false)
const batchResults = ref([])

function sampleOptions() {
  return Object.keys(SAMPLE_CURVES).map((k) => ({
    value: k,
    label: SAMPLE_CURVES[k].label_name,
  }))
}

function applySample() {
  const s = SAMPLE_CURVES[sampleKey.value]
  if (s) {
    spec.value = s.spec
    angleText.value = s.angle.join(', ')
    torqueText.value = s.torque.join(', ')
  }
}

function parseNumbers(text) {
  return text
    .split(/[,，\s]+/)
    .map((x) => x.trim())
    .filter(Boolean)
    .map(Number)
}

function buildCurve() {
  const angle = parseNumbers(angleText.value)
  const torque = parseNumbers(torqueText.value)
  if (!angle.length || !torque.length) throw new Error('请输入转角与力矩序列')
  if (angle.length !== torque.length) throw new Error('转角与力矩序列长度不一致')
  return { spec: spec.value, angle, torque }
}

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/)
  if (lines.length < 2) throw new Error('CSV 内容为空')
  const header = lines[0].split(',').map((h) => h.trim())
  const ai = header.indexOf('angle')
  const ti = header.indexOf('torque')
  if (ai < 0 || ti < 0) throw new Error('CSV 需包含 angle、torque 两列')
  const angle = []
  const torque = []
  for (let i = 1; i < lines.length; i++) {
    const parts = lines[i].split(',').map((x) => parseFloat(x.trim()))
    if (!isNaN(parts[ai])) angle.push(parts[ai])
    if (!isNaN(parts[ti])) torque.push(parts[ti])
  }
  return { angle, torque }
}

async function onCsvChange(file) {
  csvFile.value = file.raw
  try {
    const text = await file.raw.text()
    inputCurve.value = parseCsv(text)
  } catch { /* 解析失败时交由后端校验提示 */ }
}

async function runSingle() {
  detecting.value = true
  result.value = null
  try {
    if (mode.value === 'csv') {
      if (!csvFile.value) throw new Error('请先选择 CSV 文件')
      result.value = await ingestFile(spec.value, csvFile.value)
    } else {
      const curve = buildCurve()
      inputCurve.value = { angle: curve.angle, torque: curve.torque }
      result.value = await detect(curve)
    }
    ElMessage.success('检测完成')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    detecting.value = false
  }
}

async function runBatch() {
  batchDetecting.value = true
  batchResults.value = []
  try {
    const curves = Object.values(SAMPLE_CURVES).map((s) => ({
      spec: s.spec,
      angle: s.angle,
      torque: s.torque,
      record_id: `示例-${s.label_name}`,
      _truth: s.label,
    }))
    const resp = await detectBatch(curves)
    batchResults.value = resp.results.map((r, i) => ({ ...r, _truth: curves[i]._truth }))
    ElMessage.success(`批量检测完成，共 ${batchResults.value.length} 条`)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    batchDetecting.value = false
  }
}

const batchAccuracy = computed(() => {
  if (!batchResults.value.length) return null
  const ok = batchResults.value.filter((r) => r.label === r._truth).length
  return ((ok / batchResults.value.length) * 100).toFixed(1)
})

const curveOption = computed(() => {
  if (!result.value || !inputCurve.value.angle.length) return null
  const { angle, torque } = inputCurve.value
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'value', name: '转角 (deg)' },
    yAxis: { type: 'value', name: '力矩 (N·m)' },
    series: [{
      type: 'line',
      showSymbol: false,
      smooth: true,
      data: angle.map((a, i) => [a, torque[i]]),
      itemStyle: { color: '#409eff' },
      areaStyle: { opacity: 0.1 },
    }],
  }
})

const probs = computed(() => {
  if (!result.value) return []
  const p = result.value.probabilities
  return Object.keys(LABEL_NAMES).map((k) => {
    const name = LABEL_NAMES[k]
    return {
      name,
      value: +(p[name] !== undefined ? p[name] * 100 : 0).toFixed(2),
      color: LABEL_COLORS[name],
    }
  })
})
</script>

<template>
  <div class="page">
    <h3 class="page-title">质量检测分析</h3>

    <el-tabs type="border-card">
      <!-- ============ 单条检测 ============ -->
      <el-tab-pane label="单条曲线检测">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form label-width="90px" size="default">
              <el-form-item label="螺栓规格">
                <el-select v-model="spec" style="width: 100%">
                  <el-option v-for="s in SPECS" :key="s" :label="s" :value="s" />
                </el-select>
              </el-form-item>
              <el-form-item label="输入方式">
                <el-radio-group v-model="mode">
                  <el-radio-button value="sample">示例曲线</el-radio-button>
                  <el-radio-button value="csv">上传CSV</el-radio-button>
                  <el-radio-button value="manual">手动输入</el-radio-button>
                </el-radio-group>
              </el-form-item>

              <el-form-item v-if="mode === 'sample'" label="选择示例">
                <div style="display: flex; gap: 8px; width: 100%">
                  <el-select v-model="sampleKey" style="flex: 1">
                    <el-option v-for="o in sampleOptions()" :key="o.value" :label="o.label" :value="o.value" />
                  </el-select>
                  <el-button @click="applySample">填充</el-button>
                </div>
              </el-form-item>

              <el-form-item v-if="mode === 'csv'" label="CSV文件">
                <el-upload
                  :auto-upload="false"
                  :limit="1"
                  accept=".csv"
                  :on-change="onCsvChange"
                  style="width: 100%"
                >
                  <el-button icon="Upload">选择 angle,torque 两列 CSV</el-button>
                </el-upload>
              </el-form-item>

              <template v-if="mode === 'manual'">
                <el-form-item label="转角序列">
                  <el-input v-model="angleText" type="textarea" :rows="3" placeholder="逗号分隔，如 0, 1.8, 3.6, ..." />
                </el-form-item>
                <el-form-item label="力矩序列">
                  <el-input v-model="torqueText" type="textarea" :rows="3" placeholder="逗号分隔，如 -0.6, 1.3, ..." />
                </el-form-item>
              </template>

              <el-form-item>
                <el-button type="primary" :loading="detecting" icon="Cpu" @click="runSingle">开始检测</el-button>
              </el-form-item>
            </el-form>
          </el-col>

          <el-col :span="16">
            <el-empty v-if="!result" description="填写左侧输入后点击「开始检测」" />
            <div v-else>
              <el-card shadow="never" style="margin-bottom: 12px">
                <div style="display: flex; align-items: center; gap: 24px">
                  <div>
                    <div style="font-size: 13px; color: #909399">检测结果</div>
                    <el-tag :type="LABEL_TAG_TYPE[result.label]" size="large" effect="dark">
                      {{ result.label_name }}
                    </el-tag>
                  </div>
                  <div>
                    <div style="font-size: 13px; color: #909399">置信度</div>
                    <div style="font-size: 22px; font-weight: 700; color: #303133">
                      {{ (result.confidence * 100).toFixed(2) }}%
                    </div>
                  </div>
                  <div>
                    <div style="font-size: 13px; color: #909399">缺陷等级</div>
                    <div style="font-size: 16px; font-weight: 600; color: #e6a23c">
                      {{ DEFECT_LEVELS[result.defect_level] }}
                    </div>
                  </div>
                </div>
              </el-card>

              <el-card shadow="never" style="margin-bottom: 12px">
                <template #header>力矩 - 转角曲线</template>
                <ChartBox :option="curveOption" height="220px" />
              </el-card>

              <el-card shadow="never">
                <template #header>各类别概率</template>
                <div v-for="p in probs" :key="p.name" style="margin-bottom: 6px">
                  <el-progress
                    :percentage="p.value"
                    :color="p.color"
                    :stroke-width="14"
                    :format="() => `${p.name} ${p.value}%`"
                  />
                </div>
              </el-card>
            </div>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- ============ 批量检测 ============ -->
      <el-tab-pane label="批量检测报告">
        <div class="toolbar">
          <el-button type="primary" :loading="batchDetecting" icon="DataLine" @click="runBatch">
            加载 5 类示例并批量检测
          </el-button>
          <el-tag v-if="batchAccuracy" type="success" size="large">
            与已知标签一致性 {{ batchAccuracy }}%
          </el-tag>
        </div>

        <el-table :data="batchResults" border size="default" v-loading="batchDetecting">
          <el-table-column prop="record_id" label="记录" width="130" />
          <el-table-column prop="label_name" label="检测判定" width="110">
            <template #default="{ row }">
              <el-tag :type="LABEL_TAG_TYPE[row.label]" size="small" effect="dark">{{ row.label_name }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="已知标签" width="110">
            <template #default="{ row }">
              <el-tag type="info" size="small">{{ LABEL_NAMES[row._truth] }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="置信度" width="110">
            <template #default="{ row }">{{ (row.confidence * 100).toFixed(2) }}%</template>
          </el-table-column>
          <el-table-column label="缺陷等级" width="100">
            <template #default="{ row }">{{ DEFECT_LEVELS[row.defect_level] }}</template>
          </el-table-column>
          <el-table-column label="关键特征" min-width="240">
            <template #default="{ row }">
              <span style="font-size: 12px; color: #606266">
                final_torque={{ row.features.final_torque?.toFixed(1) }}
                &nbsp; total_angle={{ row.features.total_angle?.toFixed(1) }}
                &nbsp; angle_dev={{ row.features.angle_deviation?.toFixed(1) }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
