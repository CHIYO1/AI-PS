<template>
  <el-container style="min-height: 100vh;">
    <el-header>
      <h2>AI 增强的进程管理系统</h2>
    </el-header>
    <el-main>
      <ProcessTable />
    </el-main>
  </el-container>
</template>

<script setup>
import ProcessTable from './components/ProcessTable.vue'
</script>

<style>
.el-header {
  background: #2467b2;
  color: white;
  font-weight: bold;
  font-size: 1.6rem;
  text-align: center;
}
</style>