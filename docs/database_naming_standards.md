# TeachAid 数据库命名规范

## 表命名规范

### 表前缀分类
- **config_xxx** - 配置相关表（用户、组织、权限、系统配置等）
- **log_xxx** - 日志相关表（登录日志、操作日志、审计日志等）
- **system_xxx** - 系统相关表（系统设置、系统状态、系统监控等）
- **data_** - 业务数据表（题目、作业、对话等）

### 表命名示例
```sql
-- 配置表
config_users          -- 用户配置表
config_organizations  -- 机构配置表
config_permissions    -- 权限配置表
config_roles          -- 角色配置表

-- 日志表
log_login            -- 登录日志表
log_operation        -- 操作日志表
log_audit            -- 审计日志表
log_error            -- 错误日志表

-- 系统表
system_settings      -- 系统设置表
system_status        -- 系统状态表
system_monitor       -- 系统监控表

-- 业务表
data_questions            -- 题目表
data_homeworks            -- 作业表
chat_sessions        -- 对话会话表
```

## 字段命名规范

### 主键字段
- **config_xxx表**: `{表名单数}_id` (如：user_id, organization_id)
- **log_xxx表**: `log_id`
- **system_xxx表**: `system_id`
- **业务表**: `id`

### 时间字段（统一命名）
```sql
-- 标准时间字段命名
created_at     DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
updated_at     DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
deleted_at     DATETIME NULL COMMENT '软删除时间'

-- 特殊时间字段
started_at     DATETIME COMMENT '开始时间'
ended_at       DATETIME COMMENT '结束时间'
expired_at     DATETIME COMMENT '过期时间'
logged_in_at   DATETIME COMMENT '登录时间'
last_seen_at   DATETIME COMMENT '最后活跃时间'
```

### 状态字段
```sql
-- 布尔状态字段
is_active      BOOLEAN DEFAULT TRUE COMMENT '是否激活'
is_deleted     BOOLEAN DEFAULT FALSE COMMENT '是否删除'
is_public      BOOLEAN DEFAULT FALSE COMMENT '是否公开'
is_verified    BOOLEAN DEFAULT FALSE COMMENT '是否已验证'

-- 枚举状态字段
status         VARCHAR(20) DEFAULT 'active' COMMENT '状态'
user_status    VARCHAR(20) DEFAULT 'active' COMMENT '用户状态'
```

### 外键字段
- **关联config表**: `{表名单数}_id` (如：user_id 关联 config_users)
- **关联业务表**: `{表名单数}_id` (如：question_id 关联 questions)

### 常用字段命名
```sql
-- 基础信息字段
name           VARCHAR(100) NOT NULL COMMENT '名称'
title          VARCHAR(200) COMMENT '标题'
description    TEXT COMMENT '描述'
content        TEXT COMMENT '内容'

-- 用户相关字段
user_name      VARCHAR(50) NOT NULL COMMENT '用户名'
user_email     VARCHAR(255) NOT NULL COMMENT '邮箱'
user_phone     VARCHAR(20) COMMENT '电话'
full_name      VARCHAR(100) COMMENT '真实姓名'
display_name   VARCHAR(100) COMMENT '显示名称'

-- 系统字段
version        INT DEFAULT 1 COMMENT '版本号'
sort_order     INT DEFAULT 0 COMMENT '排序'
metadata       JSON COMMENT '元数据'
settings       JSON COMMENT '设置信息'
```

## 索引命名规范

### 索引类型与命名
```sql
-- 主键索引（自动生成）
PRIMARY KEY (user_id)

-- 唯一索引
UNIQUE KEY uk_{表名}_{字段名} (field_name)
-- 示例: uk_users_email (user_email)

-- 普通索引
KEY idx_{表名}_{字段名} (field_name)
-- 示例: idx_users_status (user_status)

-- 复合索引
KEY idx_{表名}_{字段1}_{字段2} (field1, field2)
-- 示例: idx_login_user_time (user_id, logged_in_at)

-- 外键索引
KEY fk_{表名}_{关联表名} (foreign_key_field)
-- 示例: fk_users_organization (organization_id)
```

## 字段类型规范

### 字符串类型
```sql
-- ID字段
VARCHAR(36)        -- UUID
BIGINT UNSIGNED    -- 数字ID

-- 短文本
VARCHAR(20)        -- 状态、类型字段
VARCHAR(50)        -- 用户名、代码
VARCHAR(100)       -- 名称、标题
VARCHAR(255)       -- 邮箱、URL

-- 长文本
TEXT               -- 描述、内容
LONGTEXT           -- 大量文本内容
```

### 数值类型
```sql
TINYINT            -- 小整数 (0-255)
INT                -- 整数
BIGINT             -- 大整数
DECIMAL(10,2)      -- 精确小数（金额）
FLOAT              -- 浮点数
```

### 时间类型
```sql
DATETIME           -- 标准时间格式
TIMESTAMP          -- 时间戳（推荐用DATETIME）
DATE               -- 仅日期
TIME               -- 仅时间
```

### JSON类型
```sql
JSON               -- JSON数据
```

## 注释规范

### 表注释
```sql
CREATE TABLE config_users (
    ...
) COMMENT='用户配置表 - 统一的用户管理';
```

### 字段注释
```sql
user_name VARCHAR(50) NOT NULL COMMENT '用户名',
user_status VARCHAR(20) DEFAULT 'active' COMMENT '用户状态: active-激活, inactive-未激活, locked-锁定',
created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
```

## 命名约定总结

1. **表名**: 使用下划线命名法，全小写
2. **字段名**: 使用下划线命名法，全小写
3. **索引名**: 使用前缀+下划线命名法
4. **时间字段**: 统一使用 `_at` 后缀
5. **状态字段**: 布尔字段使用 `is_` 前缀
6. **外键字段**: 使用 `{表名单数}_id` 格式
7. **注释**: 所有表和字段都必须有中文注释
8. **字符集**: 统一使用 `utf8mb4`
9. **排序规则**: 统一使用 `utf8mb4_unicode_ci`

这套规范确保了数据库设计的一致性和可维护性。