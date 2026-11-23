# message_info

万能信息管理系统 — 动态字段 / 板块化管理 / 敏感字段加密 / SFTP 异地备份 / Docker 一键部署。

[![Build & Publish Docker Image](https://github.com/xiaomonk88/message_info/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/xiaomonk88/message_info/actions/workflows/docker-publish.yml)

## 特性

- 🧱 **元数据驱动**：全局字段库 + 动态分类与板块，按需勾选复用字段、配置计算字段与数值汇总
- 🔐 **安全可靠**：JWT 登录认证 + 密码/敏感字段 Fernet (AES) 加密落盘 + 多用户权限控制
- 📦 **Docker 一键部署**：GitHub Actions 自动构建 `amd64` / `arm64` 多架构镜像，小内存 VPS 免编译秒装，数据挂载宿主机升级零丢失
- 🗂 **分类 / 板块 / 字段** 三级结构，支持拖拽排序与丰富图标选择
- ♻️ **回收站**：软删除与一键恢复
- 📝 **审计日志与多重备份**：支持数据库快照备份、含附件的完整 ZIP 备份、定时自动备份及 **SFTP 异地同步备份**
- 🖼 **丰富字段类型**：`text` / `textarea` / `number` / `boolean` / `date` / `datetime` / `select` / `multiselect` / `url` / `email` / `password` / `image` / `file` / `json`
- 🚀 **轻量技术栈**：FastAPI + SQLite (WAL) + Vue 3 + TypeScript + Vite

---

## 一、Linux / VPS 一键 Docker 安装部署（推荐）

无需提前安装 Git、Python 或 Node.js（若服务器未装 Docker，脚本会自动安装 Docker 与 Compose 插件，并拉取预构建镜像启动）：

### 交互式一键安装（可自定义端口与密码）

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/xiaomonk88/message_info/main/install.sh)
```

### 全自动静默安装（自动生成随机强密码并在终端展示）

```bash
curl -fsSL https://raw.githubusercontent.com/xiaomonk88/message_info/main/install.sh | bash
```

也可以通过环境变量指定端口与初始管理员账号密码：

```bash
PORT=17500 ADMIN_USERNAME=admin ADMIN_PASSWORD=YourStrongPassword123 \
  bash <(curl -fsSL https://raw.githubusercontent.com/xiaomonk88/message_info/main/install.sh)
```

### 日常管理命令

安装完成后，可直接在服务器任意目录执行 `message-info` 命令：

```bash
message-info update      # 拉取最新镜像并平滑升级（保留全部数据与密钥）
message-info status      # 查看容器运行状态
message-info logs        # 查看实时日志
message-info restart     # 重启服务
message-info stop        # 停止服务
message-info uninstall   # 卸载容器（默认保留 /opt/message_info/data 数据目录）
```

> 默认数据与配置文件位于 `/opt/message_info/`，首次启动会自动生成高强度 `jwt_secret` 与 `encryption_key` 保存于 `/opt/message_info/data/secrets/`。

---

## 二、使用 Docker Compose 手动部署

### 方式 A：直接拉取官方预构建镜像（免编译，秒启动）

```bash
mkdir -p message_info && cd message_info
curl -fsSLO https://raw.githubusercontent.com/xiaomonk88/message_info/main/docker-compose.yml
curl -fsSL https://raw.githubusercontent.com/xiaomonk88/message_info/main/.env.example -o .env
# 按需修改 .env 中的 PORT、ADMIN_USERNAME、ADMIN_PASSWORD
docker compose up -d
```

访问：`http://<服务器IP>:17500`

更新版本：

```bash
docker compose pull && docker compose up -d
```

### 方式 B：克隆源码本地构建镜像

如果你修改了前后端代码，想在本地重新编译打包镜像：

```bash
git clone https://github.com/xiaomonk88/message_info.git
cd message_info
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --build
```

---

## 三、本地开发与运行（Windows）

### 准备

- Python 3.10+
- Node.js 18+

### 🚀 一键单窗口启动

双击 **`start.bat`** 即可：自动创建虚拟环境、安装依赖、按需打包前端，并由后端在同一端口托管页面和接口，就绪后自动打开浏览器。

- 访问：`http://localhost:8010`
- 停止：关闭窗口、按 `Ctrl+C`，或双击 `stop.bat`
- 默认账号：`admin` / `admin123`（可在 `.env` 修改）

**开发前端热更新（HMR）** 时双击 `dev.bat`（访问 `http://localhost:5173`，接口自动代理至 `:8010`）。

---

## 四、目录结构与数据备份

```text
message_info/
├── backend/                  FastAPI 后端源码
├── frontend/                 Vue 3 + TypeScript 前端源码
├── data/                     ⚠️ 数据持久化目录（宿主机挂载卷）
│   ├── db/app.db             SQLite 数据库
│   ├── uploads/              上传的图片与附件
│   ├── backups/              自动/手动备份文件 (.db / .zip)
│   └── secrets/              自动生成的 JWT 与 Fernet 加密密钥
├── install.sh                Linux 一键安装/升级/卸载脚本
├── Dockerfile                多阶段构建定义
├── docker-compose.yml        生产环境 Compose 配置（拉取 GHCR 镜像）
├── docker-compose.build.yml  本地源码构建覆盖配置
└── .env.example              环境变量模板
```

### 备份与恢复建议

1. **系统内置备份与迁移**：「系统运维 → 数据备份」支持：
   - **导出并下载到本地**：一键打包完整 `.zip` 备份（含 SQLite 数据库、上传附件与字段加密密钥）直接下载到本地电脑。
   - **从本地上传恢复**：支持拖拽或选择本地 `.zip` / `.db` 备份文件上传并立即恢复，跨服务器迁移时加密字段亦可无损解密。
   - **定时与异地备份**：支持按小时周期自动备份与 **SFTP 远程异地自动上传**。
2. **宿主机打包备份**（强烈建议连同 `secrets/` 一起备份）：
   ```bash
   tar czf message_info_backup_$(date +%Y%m%d).tar.gz -C /opt/message_info data .env
   ```
   > ⚠️ **重要提醒**：`data/secrets/encryption_key`（或 `.env` 中的 `ENCRYPTION_KEY`）用于解密密码/加密字段，请务必与数据库一同妥善备份，切勿丢失或随意更换。

---

## License

MIT
