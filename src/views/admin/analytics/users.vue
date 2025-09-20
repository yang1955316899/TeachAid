<template>
  <div class="analytics-users">
    <div class="header">
      <h2>用户分析</h2>
    </div>

    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>用户分析数据</span>
            </div>
          </template>
          <div class="placeholder">
            用户分析页面 - 开发中
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
// 这是一个占位页面，后续可以扩展
</script>

<style scoped>
.analytics-users {
  padding: 20px;
}

.header {
  margin-bottom: 20px;
}

.placeholder {
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 18px;
}
</style>