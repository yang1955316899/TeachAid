# GitHub Actions部署说明

本项目包含以下GitHub Actions工作流：

## 1. CI/CD Pipeline (`.github/workflows/ci-cd.yml`)

**触发条件：**
- 推送到 `master`, `main`, `develop` 分支
- 创建针对 `master`, `main` 分支的Pull Request
- 手动触发

**包含任务：**
- **测试**: 在Python 3.11和3.12环境下运行测试
- **构建**: 构建Python包并上传artifacts
- **安全扫描**: 使用safety和bandit进行安全检查
- **Docker构建**: 构建并推送Docker镜像到Docker Hub

## 2. Database Migration (`.github/workflows/database-migration.yml`)

**触发条件：**
- 数据库相关文件变更
- 手动触发

**功能：**
- 自动运行数据库迁移
- 验证迁移状态

## 3. Code Quality (`.github/workflows/code-quality.yml`)

**触发条件：**
- 推送到任何分支
- 创建Pull Request

**包含检查：**
- 代码格式化 (Black, isort)
- 静态类型检查 (mypy)
- 代码复杂度分析 (radon)
- 测试覆盖率报告

## 所需环境变量

在GitHub仓库设置中配置以下secrets：

```bash
DOCKERHUB_USERNAME=your_dockerhub_username
DOCKERHUB_TOKEN=your_dockerhub_token
DATABASE_URL=your_production_database_url
```

## Docker部署

项目支持Docker部署，构建的镜像会自动推送到Docker Hub。

**本地测试：**
```bash
docker-compose up -d
```

**生产部署：**
```bash
docker pull your_dockerhub_username/teachaid:latest
docker run -p 50002:50002 your_dockerhub_username/teachaid:latest
```