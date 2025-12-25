<template>
  <el-dialog :model-value="true" width="600px" :title="'进程详情 - ' + proc.process_name" @close="onClose">
    <el-descriptions :column="1" border>
      <el-descriptions-item label="PID">{{ proc.pid }}</el-descriptions-item>
      <el-descriptions-item label="分类">{{ proc.category }}</el-descriptions-item>
      <el-descriptions-item label="CPU(%)">{{ proc.cpu_usage }}</el-descriptions-item>
      <el-descriptions-item label="内存(%)">{{ proc.memory_usage }}</el-descriptions-item>
      <el-descriptions-item label="标签">
        <el-tag v-for="tag in proc.tags" :key="tag" type="info">{{ tag }}</el-tag>
        <el-tag v-for="label in proc.manual_labels" :key="label" type="success">{{ label }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="异常">
        <el-tag v-if="proc.anomaly" type="danger">异常</el-tag>
        <el-tag v-else type="success">正常</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="置信度">{{ proc.confidence }}</el-descriptions-item>
      <el-descriptions-item v-if="proc.reasons && proc.reasons.length" label="异常解释">
        <ul>
          <li v-for="r in proc.reasons" :key="r">{{ r }}</li>
        </ul>
      </el-descriptions-item>
    </el-descriptions>

    <div style="margin-top:22px;">
      <el-tabs v-model="tab" style="margin-bottom:6px;">
        <el-tab-pane label="CPU预测" name="cpu"></el-tab-pane>
        <el-tab-pane label="内存预测" name="mem"></el-tab-pane>
      </el-tabs>
      <div style="min-height: 220px;">
        <el-button type="primary" size="small" @click="getPrediction" :loading="loading" style="margin-bottom:10px;">
          获取{{tab==='cpu'?'CPU':'内存'}}预测
        </el-button>
        <div v-if="forecastData.length">
          <div ref="chartDom" style="width:100%;height:220px;"/>
        </div>
        <div v-else-if="predictMessage" style="color:gray;text-align:center;padding:40px 0;">
          {{ predictMessage }}
        </div>
        <div v-else style="color:gray;text-align:center;padding:40px 0;">
          暂无预测数据
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="onClose">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  proc: Object
})
const emit = defineEmits(['close'])

const tab = ref('cpu')
const loading = ref(false)
const forecastData = ref([])
const predictMessage = ref('')
const chartDom = ref(null)
let chartInstance = null

// 自动初始化或清理echarts实例
import { nextTick } from 'vue'

async function drawChart() {
  await nextTick()
  if(chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  if(chartDom.value && forecastData.value.length) {
    chartInstance = echarts.init(chartDom.value)
    chartInstance.setOption({
      title: { text: tab.value.toUpperCase() + ' 用量预测', left: 'center', top: 8, textStyle: {fontSize: 15} },
      xAxis: { type: 'category', data: forecastData.value.map(item => item.ds.split('T')[1].split('.')[0]) },
      yAxis: { type: 'value', name: tab.value === 'cpu' ? 'CPU%' : '内存%' },
      series: [
        { name: '预测', type: 'line', smooth: true, data: forecastData.value.map(item => item.yhat) },
        { name: '下界', type: 'line', smooth: true, symbol: 'none', lineStyle: { type: 'dotted' }, data: forecastData.value.map(item => item.yhat_lower) },
        { name: '上界', type: 'line', smooth: true, symbol: 'none', lineStyle: { type: 'dotted' }, data: forecastData.value.map(item => item.yhat_upper) },
      ],
      legend: { top: 28 },
      grid: { left: 40, right: 10, top: 58, bottom: 35 }
    })
  }
}

watch(
  [forecastData, tab],
  () => { drawChart() }
)

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

const getPrediction = async () => {
  loading.value = true
  forecastData.value = []
  predictMessage.value = ''
  try {
    const res = await fetch(`/predict/${props.proc.pid}?metric=${tab.value}`)
    const data = await res.json()
    if (Array.isArray(data.predictions)) {
      forecastData.value = data.predictions
    } else if (data.status === 'waiting') {
      predictMessage.value = data.message
    } else if (data.message) {
      predictMessage.value = data.message
    } else {
      forecastData.value = []
    }
  } catch(e) {
    predictMessage.value = '获取预测数据失败'
    forecastData.value = []
  }
  loading.value = false
}
function onClose() {
  emit('close')
}
</script>