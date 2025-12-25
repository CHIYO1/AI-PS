<template>
  <el-card>
    <div style="display:flex;align-items:center;justify-content:space-between;">
      <span style="font-size:1.2em;">进程总览</span>
      <el-input v-model="filter" placeholder="搜索进程名/标签" style="width:200px"/>
    </div>
    <el-table :data="filteredProcesses" style="width:100%; margin-top:10px;" @row-click="showDetail">
      <el-table-column prop="pid" label="PID" width="80"/>
      <el-table-column prop="process_name" label="名称" />
      <el-table-column prop="cpu_usage" label="CPU(%)" width="90"/>
      <el-table-column prop="memory_usage" label="内存(%)" width="90"/>
      <el-table-column prop="category" label="分类" width="120">
        <template #default="scope">
          <el-tag>{{ scope.row.category }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="tags" label="标签" width="140">
        <template #default="scope">
          <el-tag v-for="tag in scope.row.tags" :key="tag" type="info">{{ tag }}</el-tag>
          <!-- 只读展示 manual_labels -->
          <el-tag v-for="label in scope.row.manual_labels" :key="label" type="success">{{ label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="anomaly" label="异常" width="90">
        <template #default="scope">
          <el-tag v-if="scope.row.anomaly" type="danger">异常</el-tag>
          <el-tag v-else type="success">正常</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="scope">
          <el-button size="mini" @click.stop="showDetail(scope.row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <ProcessDetail v-if="detailVisible" :proc="selectedProc" @close="detailVisible=false"/>
  </el-card>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import ProcessDetail from './ProcessDetail.vue'
import { ElMessage } from 'element-plus'

const processApi = '/api/classify_processes?limit=50'

const processes = ref([])
const filter = ref('')
const detailVisible = ref(false)
const selectedProc = ref(null)

const fetchData = async () => {
  try {
    const res = await fetch(processApi)
    const data = await res.json()
    processes.value = data.processes || []
  } catch (e) {
    ElMessage.error('获取进程数据失败')
  }
}

const filteredProcesses = computed(() => {
  if (!filter.value) return processes.value
  return processes.value.filter(
    p =>
      (p.process_name && p.process_name.toLowerCase().includes(filter.value.toLowerCase())) ||
      (Array.isArray(p.manual_labels) && p.manual_labels.join(',').toLowerCase().includes(filter.value.toLowerCase())) ||
      (Array.isArray(p.tags) && p.tags.join(',').toLowerCase().includes(filter.value.toLowerCase()))
  )
})

function showDetail(row) {
  selectedProc.value = row
  detailVisible.value = true
}

onMounted(fetchData)
</script>