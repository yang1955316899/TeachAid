# TeachAid 数据库表命名规范

## 当前问题分析

由于多个agent分批次开发，导致数据库表命名不一致：

### 现有命名方式
1. **无前缀**: `tutor_sessions`, `tutor_messages`, `student_progress`
2. **data_前缀**: `data_classes`, `data_questions`, `data_homeworks`
3. **edu_前缀**: `edu_teaching`, `edu_grades`, `edu_subjects`
4. **config_前缀**: `config_users`, `config_organizations`
5. **log_前缀**: `log_system`, `log_login`, `log_audit`

## 统一命名规范

### 前缀分类标准

#### 1. **业务数据表 (biz_前缀)**
- 核心业务逻辑相关的数据
- **现有表映射**:
  - `data_classes` → `biz_classes`
  - `data_questions` → `biz_questions`
  - `data_homeworks` → `biz_homeworks`
  - `data_student_homeworks` → `biz_student_homeworks`
  - `data_notes` → `biz_notes`
  - `data_chat_sessions` → `biz_chat_sessions`
  - `data_chat_messages` → `biz_chat_messages`
  - `data_file_uploads` → `biz_file_uploads`

#### 2. **AI教学表 (ai_前缀)**
- AI智能教学相关功能
- **现有表映射**:
  - `tutor_sessions` → `ai_tutor_sessions`
  - `tutor_messages` → `ai_tutor_messages`
  - `student_progress` → `ai_student_progress`
  - `data_prompt_templates` → `ai_prompt_templates`

#### 3. **教务基础表 (edu_前缀)** ✅ 保持不变
- 教育体系基础数据
- **现有表**:
  - `edu_grades`
  - `edu_subjects`
  - `edu_chapters`
  - `edu_teaching`

#### 4. **配置表 (cfg_前缀)**
- 系统配置相关
- **现有表映射**:
  - `config_users` → `cfg_users`
  - `config_organizations` → `cfg_organizations`
  - `config_permissions` → `cfg_permissions`
  - `config_role_permissions` → `cfg_role_permissions`
  - `config_security_policies` → `cfg_security_policies`
  - `config_notifications` → `cfg_notifications`
  - `system_settings` → `cfg_system_settings`

#### 5. **日志表 (log_前缀)** ✅ 保持不变
- 系统日志记录
- **现有表**:
  - `log_system`
  - `log_login`
  - `log_audit`

#### 6. **关联表 (rel_前缀)**
- 多对多关系表
- **现有表映射**:
  - `data_class_students` → `rel_class_students`
  - `data_question_chapters` → `rel_question_chapters`

## 实施方案

### 第一阶段: 创建迁移脚本
1. 生成表重命名的SQL迁移脚本
2. 更新所有外键引用
3. 更新索引和约束名称

### 第二阶段: 更新代码
1. 修改所有模型的`__tablename__`
2. 更新外键引用
3. 更新查询代码中的表名

### 第三阶段: 验证测试
1. 运行所有测试用例
2. 验证数据完整性
3. 检查应用功能正常

## 命名约定细则

### 表名规则
- 前缀 + 下划线 + 描述性名称
- 使用复数形式
- 英文小写，单词用下划线分隔
- 最大长度不超过63字符

### 字段名规则
- 英文小写，单词用下划线分隔
- 主键统一使用 `id`
- 外键使用 `{关联表}_id` 格式
- 布尔字段使用 `is_` 或 `has_` 前缀
- 时间字段使用 `_time` 或 `_at` 后缀

### 索引命名
- `idx_{表名}_{字段名}` - 普通索引
- `uq_{表名}_{字段名}` - 唯一索引
- `fk_{表名}_{字段名}` - 外键约束

## 迁移时间表

### 优先级1 (立即执行)
- 创建命名规范文档 ✅
- 生成迁移脚本草案

### 优先级2 (近期执行)
- 更新核心业务表 (biz_*, ai_*)
- 更新配置表 (cfg_*)

### 优先级3 (后续执行)
- 更新关联表 (rel_*)
- 完善文档和规范

## 风险评估

### 低风险
- 新表命名规范应用
- 文档更新

### 中风险
- 现有表重命名
- 代码引用更新

### 高风险
- 生产环境迁移
- 数据完整性保证

## 回滚计划

1. 保留原表结构作为备份
2. 准备反向迁移脚本
3. 监控应用运行状态
4. 异常时快速回滚

---
**制定时间**: 2025-09-27
**负责人**: Claude Code Optimizer
**状态**: 规范制定完成，等待实施