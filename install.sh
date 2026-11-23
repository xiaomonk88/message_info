#!/usr/bin/env bash
# ==============================================================================
#  message_info 一键 Docker 安装 / 更新 / 管理脚本
#  仓库: https://github.com/xiaomonk88/message_info
#
#  一键安装 / 更新:
#    bash <(curl -fsSL https://raw.githubusercontent.com/xiaomonk88/message_info/main/install.sh)
#    或:
#    curl -fsSL https://raw.githubusercontent.com/xiaomonk88/message_info/main/install.sh | bash
#
#  支持环境变量自定义（非交互式部署）:
#    PORT=17500 ADMIN_USERNAME=admin ADMIN_PASSWORD=YourPassword123 \
#      bash <(curl -fsSL https://raw.githubusercontent.com/xiaomonk88/message_info/main/install.sh)
# ==============================================================================
set -euo pipefail

REPO_OWNER="xiaomonk88"
REPO_NAME="message_info"
RAW_BASE="https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/main"
DEFAULT_IMAGE="ghcr.io/${REPO_OWNER}/${REPO_NAME}:latest"

INSTALL_DIR="${INSTALL_DIR:-/opt/message_info}"
IMAGE="${IMAGE:-$DEFAULT_IMAGE}"
TZ_VAL="${TZ:-Asia/Shanghai}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

require_root() {
  if [ "${EUID:-$(id -u)}" -ne 0 ]; then
    if command -v sudo >/dev/null 2>&1; then
      exec sudo -E bash "$0" "$@"
    else
      err "请使用 root 用户运行此脚本（或先安装 sudo）。"
      exit 1
    fi
  fi
}

random_password() {
  local pwd=""
  if command -v openssl >/dev/null 2>&1; then
    pwd="$(openssl rand -base64 18 | tr -dc 'A-Za-z0-9' | head -c 14)"
  fi
  if [ "${#pwd}" -lt 10 ] && [ -r /dev/urandom ]; then
    pwd="$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 14 || true)"
  fi
  if [ "${#pwd}" -lt 10 ]; then
    pwd="Admin$(date +%s)"
  fi
  printf '%s' "$pwd"
}

ensure_docker() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    if ! docker info >/dev/null 2>&1; then
      info "正在启动 Docker 服务 ..."
      systemctl enable --now docker >/dev/null 2>&1 || service docker start >/dev/null 2>&1 || true
    fi
    ok "Docker 与 Docker Compose 已就绪"
    return 0
  fi

  info "未检测到完整的 Docker / Docker Compose 环境，正在自动安装 Docker ..."
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | sh
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- https://get.docker.com | sh
  else
    err "系统缺少 curl 或 wget，请先安装其中之一后重试。"
    exit 1
  fi

  systemctl enable --now docker >/dev/null 2>&1 || service docker start >/dev/null 2>&1 || true

  if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
    err "Docker 或 Docker Compose 插件安装失败，请检查系统源或网络。"
    exit 1
  fi
  ok "Docker 安装完成"
}

detect_ip() {
  local ip=""
  for url in "https://api.ipify.org" "https://ifconfig.me/ip" "https://icanhazip.com"; do
    ip="$(curl -4 -fsSL --max-time 3 "$url" 2>/dev/null | tr -d '[:space:]' || true)"
    if [[ "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
      printf '%s' "$ip"
      return 0
    fi
  done
  ip="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
  printf '%s' "${ip:-127.0.0.1}"
}

write_compose_file() {
  cat >"${INSTALL_DIR}/docker-compose.yml" <<'EOF'
services:
  app:
    image: ${IMAGE:-ghcr.io/xiaomonk88/message_info:latest}
    container_name: message_info
    restart: unless-stopped
    environment:
      - JWT_SECRET=${JWT_SECRET:-}
      - ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY:-}
      - TZ=${TZ:-Asia/Shanghai}
    volumes:
      - ./data:/data
    ports:
      - "${PORT:-17500}:8000"
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://127.0.0.1:8000/api/v1/system/health"]
      interval: 30s
      timeout: 5s
      retries: 3
EOF
}

install_cli_helper() {
  local target="${INSTALL_DIR}/manage.sh"
  if [ -f "$0" ] && grep -q "message_info 一键 Docker" "$0" 2>/dev/null; then
    cp "$0" "$target"
  else
    curl -fsSL "${RAW_BASE}/install.sh" -o "$target" 2>/dev/null || true
  fi
  if [ -s "$target" ]; then
    chmod +x "$target"
    if [ -d /usr/local/bin ]; then
      ln -sf "$target" /usr/local/bin/message-info
    fi
  fi
}

read_env_val() {
  local key="$1"
  local file="${INSTALL_DIR}/.env"
  if [ -f "$file" ]; then
    grep -E "^${key}=" "$file" | tail -n1 | cut -d'=' -f2-
  fi
}

wait_healthy() {
  local port="$1"
  info "正在等待服务启动就绪 ..."
  for _ in $(seq 1 30); do
    if curl -fsS "http://127.0.0.1:${port}/api/v1/system/health" >/dev/null 2>&1; then
      ok "服务健康检查通过！"
      return 0
    fi
    sleep 1
  done
  warn "服务仍在初始化中，可执行 'docker logs -f message_info' 查看实时日志。"
}

do_install() {
  require_root "$@"
  echo -e "\n${BOLD}=========================================================${NC}"
  echo -e "${BOLD}   message_info — 万能信息管理系统 Docker 一键部署${NC}"
  echo -e "${BOLD}=========================================================${NC}\n"

  ensure_docker

  mkdir -p "${INSTALL_DIR}/data/db" \
           "${INSTALL_DIR}/data/uploads" \
           "${INSTALL_DIR}/data/backups" \
           "${INSTALL_DIR}/data/secrets"

  local is_first_install=0
  local port_val="${PORT:-}"
  local admin_user="${ADMIN_USERNAME:-}"
  local admin_pass="${ADMIN_PASSWORD:-}"

  if [ ! -f "${INSTALL_DIR}/.env" ]; then
    is_first_install=1

    if [ -t 0 ]; then
      if [ -z "$port_val" ]; then
        read -r -p "请输入外部访问端口 [默认: 17500]: " input_port || true
        port_val="${input_port:-17500}"
      fi
      if [ -z "$admin_user" ]; then
        read -r -p "请输入初始管理员账号 [默认: admin]: " input_user || true
        admin_user="${input_user:-admin}"
      fi
      if [ -z "$admin_pass" ]; then
        read -r -p "请输入初始管理员密码 [留空自动生成随机强密码]: " input_pass || true
        admin_pass="${input_pass:-$(random_password)}"
      fi
    else
      port_val="${port_val:-17500}"
      admin_user="${admin_user:-admin}"
      admin_pass="${admin_pass:-$(random_password)}"
    fi

    if [ "${#admin_pass}" -lt 6 ]; then
      warn "密码长度不足 6 位，已自动改为生成随机强密码。"
      admin_pass="$(random_password)"
    fi

    cat >"${INSTALL_DIR}/.env" <<EOF
# 服务监听端口
PORT=${port_val}

# 镜像地址
IMAGE=${IMAGE}

# 初始管理员（仅首次初始化空数据库时生效）
ADMIN_USERNAME=${admin_user}
ADMIN_PASSWORD=${admin_pass}

# 留空时首次启动自动生成高强度随机密钥并持久化至 ./data/secrets/
JWT_SECRET=
ENCRYPTION_KEY=

# 时区
TZ=${TZ_VAL}
EOF
    chmod 600 "${INSTALL_DIR}/.env"
    ok "已创建配置文件 ${INSTALL_DIR}/.env"
  else
    info "检测到已有配置 ${INSTALL_DIR}/.env，保留原有配置与数据执行平滑更新"
    port_val="$(read_env_val PORT)"
    port_val="${port_val:-17500}"
    admin_user="$(read_env_val ADMIN_USERNAME)"
    admin_user="${admin_user:-admin}"
  fi

  write_compose_file
  install_cli_helper

  info "正在拉取最新镜像 ${IMAGE} ..."
  (
    cd "${INSTALL_DIR}"
    docker compose pull
    docker compose up -d --remove-orphans
  )

  wait_healthy "${port_val}"

  local ip
  ip="$(detect_ip)"

  echo ""
  echo -e "${GREEN}=========================================================${NC}"
  if [ "$is_first_install" -eq 1 ]; then
    echo -e "${GREEN} 🎉 message_info 安装并启动成功！${NC}"
  else
    echo -e "${GREEN} 🎉 message_info 更新并重启成功（数据完好保留）！${NC}"
  fi
  echo -e "${GREEN}=========================================================${NC}"
  echo -e " 访问地址   : ${BOLD}http://${ip}:${port_val}${NC}"
  echo -e " 接口文档   : http://${ip}:${port_val}/api/v1/docs"
  if [ "$is_first_install" -eq 1 ]; then
    echo -e " 管理员账号 : ${BOLD}${admin_user}${NC}"
    echo -e " 初始密码   : ${BOLD}${admin_pass}${NC}  ${YELLOW}(请登录后在「账号设置」及时修改)${NC}"
  else
    echo -e " 配置文件   : ${INSTALL_DIR}/.env"
  fi
  echo -e " 数据目录   : ${INSTALL_DIR}/data  ${YELLOW}(含数据库、上传文件与加密密钥，请定期备份)${NC}"
  echo -e "---------------------------------------------------------"
  echo -e " 常用管理命令:"
  echo -e "   message-info update     # 拉取最新镜像并平滑升级"
  echo -e "   message-info status     # 查看运行状态"
  echo -e "   message-info logs       # 查看实时日志"
  echo -e "   message-info restart    # 重启服务"
  echo -e "   message-info uninstall  # 卸载容器（默认保留数据）"
  echo -e "${GREEN}=========================================================${NC}\n"
}

do_update() {
  require_root "$@"
  if [ ! -d "${INSTALL_DIR}" ]; then
    err "未找到安装目录 ${INSTALL_DIR}，正在转为全新安装 ..."
    do_install "$@"
    return
  fi
  info "正在更新 message_info ..."
  write_compose_file
  (
    cd "${INSTALL_DIR}"
    docker compose pull
    docker compose up -d --remove-orphans
    docker image prune -f >/dev/null 2>&1 || true
  )
  local port_val
  port_val="$(read_env_val PORT)"
  wait_healthy "${port_val:-17500}"
  ok "更新完成，数据目录 ${INSTALL_DIR}/data 已完整保留。"
}

do_uninstall() {
  require_root "$@"
  if [ ! -d "${INSTALL_DIR}" ]; then
    warn "未检测到 ${INSTALL_DIR}，无需卸载。"
    exit 0
  fi
  info "正在停止并移除 message_info 容器 ..."
  (
    cd "${INSTALL_DIR}"
    docker compose down --remove-orphans || true
  )
  rm -f /usr/local/bin/message-info "${INSTALL_DIR}/docker-compose.yml" "${INSTALL_DIR}/manage.sh"

  local purge_data="n"
  if [ -t 0 ]; then
    read -r -p "是否同时彻底删除数据目录 ${INSTALL_DIR}/data（不可恢复）？[y/N]: " purge_data || true
  fi
  if [[ "${purge_data,,}" == "y" || "${purge_data,,}" == "yes" ]]; then
    rm -rf "${INSTALL_DIR}"
    ok "message_info 及全部数据已彻底删除。"
  else
    ok "容器已卸载，您的数据和密钥仍安全保留在 ${INSTALL_DIR}/data 与 ${INSTALL_DIR}/.env"
  fi
}

case "${1:-install}" in
  install)
    do_install "$@"
    ;;
  update|upgrade)
    do_update "$@"
    ;;
  restart)
    require_root "$@"
    (cd "${INSTALL_DIR}" && docker compose restart)
    ok "服务已重启"
    ;;
  stop)
    require_root "$@"
    (cd "${INSTALL_DIR}" && docker compose stop)
    ok "服务已停止"
    ;;
  start)
    require_root "$@"
    (cd "${INSTALL_DIR}" && docker compose up -d)
    ok "服务已启动"
    ;;
  status|ps)
    require_root "$@"
    (cd "${INSTALL_DIR}" && docker compose ps)
    ;;
  logs|log)
    require_root "$@"
    (cd "${INSTALL_DIR}" && docker compose logs -f --tail=100)
    ;;
  uninstall|remove)
    do_uninstall "$@"
    ;;
  *)
    echo "用法: $0 {install|update|start|stop|restart|status|logs|uninstall}"
    exit 1
    ;;
esac
