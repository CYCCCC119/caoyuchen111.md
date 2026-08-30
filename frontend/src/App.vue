<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <el-container class="app-shell">
    <el-aside width="220px" class="app-aside">
      <div class="brand">
        <span class="brand-icon">🔩</span>
        <span class="brand-text">拧紧质量智能检测</span>
      </div>
      <el-menu
        :default-active="route.path"
        router
        class="app-menu"
        background-color="#001529"
        text-color="#a6adb4"
        active-text-color="#ffffff"
      >
        <el-menu-item v-for="r in $router.options.routes.filter(x => x.meta)" :key="r.path" :index="r.path">
          <el-icon><component :is="r.meta.icon" /></el-icon>
          <span>{{ r.meta.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <span class="app-title">重型机械装配车间螺栓拧紧质量智能检测与工艺追溯系统</span>
        <span class="app-sub">制造智能技术 · 课程设计</span>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.app-shell {
  height: 100vh;
}
.app-aside {
  background: #001529;
  overflow-x: hidden;
}
.brand {
  height: var(--app-header-h);
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 8px;
  color: #fff;
  font-weight: 600;
  white-space: nowrap;
}
.brand-icon {
  font-size: 20px;
}
.brand-text {
  font-size: 14px;
}
.app-menu {
  border-right: none;
}
.app-menu .el-menu-item.is-active {
  background-color: #1677ff;
}
.app-header {
  height: var(--app-header-h);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
}
.app-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.app-sub {
  font-size: 12px;
  color: #909399;
}
.app-main {
  background: #f5f7fa;
  padding: 0;
  overflow-y: auto;
}
</style>
