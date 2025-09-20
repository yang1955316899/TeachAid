<template>
  <el-breadcrumb separator="/">
    <el-breadcrumb-item
      v-for="(item, index) in breadcrumbList"
      :key="index"
      :to="item.path ? { path: item.path } : null"
    >
      {{ item.title }}
    </el-breadcrumb-item>
  </el-breadcrumb>
</template>

<script>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

export default {
  name: 'Breadcrumb',
  setup() {
    const route = useRoute()

    const breadcrumbNameMap = {
      '/admin': '管理员中心',
      '/admin/dashboard': '仪表盘',
      '/admin/users': '用户列表',
      '/admin/users/create': '创建用户',
      '/admin/classes': '班级列表',
      '/admin/classes/create': '创建班级',
      '/admin/teaching-assignments': '授课安排',
      '/admin/homeworks': '作业管理',
      '/admin/questions': '题目管理',
      '/admin/settings': '系统设置',
      '/admin/permissions': '权限管理',
      '/admin/analytics/overview': '数据概览',
      '/admin/analytics/users': '用户分析',
      '/admin/analytics/content': '内容分析',
      '/admin/profile': '个人信息'
    }

    const breadcrumbList = computed(() => {
      const pathArray = route.path.split('/').filter(path => path)
      const breadcrumbs = []

      let currentPath = ''
      pathArray.forEach((path, index) => {
        currentPath += `/${path}`
        const title = breadcrumbNameMap[currentPath]

        if (title) {
          breadcrumbs.push({
            title,
            path: index === pathArray.length - 1 ? null : currentPath
          })
        }
      })

      return breadcrumbs
    })

    return {
      breadcrumbList
    }
  }
}
</script>

<style scoped>
:deep(.el-breadcrumb__inner) {
  color: #606266;
}

:deep(.el-breadcrumb__inner.is-link) {
  color: #409EFF;
}

:deep(.el-breadcrumb__inner.is-link:hover) {
  color: #66b1ff;
}
</style>