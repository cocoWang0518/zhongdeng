# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 前端项目概述

这是债券信用风险预测系统的Vue.js前端应用，使用现代化的Vue 3 + TypeScript + Vite技术栈构建。

## 技术栈

- **Vue 3** + **TypeScript** + **Vite** - 核心框架
- **Vue Router** (auto-routes) - 文件系统路由
- **Pinia** - 状态管理
- **Naive UI** - UI组件库
- **UnoCSS** - 原子化CSS框架
- **VueUse** - Vue组合式工具库

## 常用命令

### 开发
```bash
pnpm dev              # 启动开发服务器 (端口: 3333)
pnpm build            # 构建生产版本
pnpm build:web        # 构建并复制到父目录的web文件夹
pnpm preview          # 预览构建结果
```

### 代码质量
```bash
pnpm lint             # ESLint代码检查和自动修复
pnpm typecheck        # TypeScript类型检查
pnpm test             # 运行Vitest单元测试
```

### 包管理
```bash
pnpm up               # 升级依赖包到主版本
```

## 项目架构

### 目录结构
- `src/pages/` - 页面组件（基于文件系统的自动路由）
- `src/components/` - 可复用组件
- `src/composables/` - Vue组合式函数
- `src/stores/` - Pinia状态管理
- `src/utils/` - 工具函数
- `src/styles/` - 样式文件

### 核心组件
- `PredictForm.vue` - 预测表单组件
- `ResultDisplay.vue` - 结果展示组件
- `ChatSidebar.vue` - 聊天侧边栏
- `tabs/` - 结果页面的各种标签页组件

### API代理配置
开发环境将 `/api` 路径代理到 `http://localhost:11232`（后端Flask服务）

### 自动导入配置
- Vue API和VueUse函数自动导入
- Naive UI组件自动导入
- `src/composables/` 下的组合式函数自动导入

## 开发约定

### 路由系统
使用 `unplugin-vue-router` 实现基于文件系统的自动路由：
- `src/pages/new.vue` → `/new`
- `src/pages/result/[hash].vue` → `/result/:hash`

### 状态管理
使用Pinia进行状态管理，stores位于 `src/stores/`

### 样式系统
- UnoCSS用于原子化CSS类
- 支持暗黑模式切换
- 使用Naive UI主题系统

### TypeScript配置
- 严格模式启用
- 自动生成类型声明文件（auto-imports.d.ts, components.d.ts等）

## 构建部署

### 生产构建
- `pnpm build` - 构建到 `dist/` 目录
- `pnpm build:web` - 构建后复制到父目录的 `web/` 文件夹供后端静态服务使用

### 测试
使用Vitest + jsdom环境进行单元测试，测试文件位于 `test/` 目录