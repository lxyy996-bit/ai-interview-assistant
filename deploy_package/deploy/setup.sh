#!/bin/bash
# AI 面试助手 - 服务器初始化脚本
# 在服务器上执行此脚本完成环境配置

set -e

echo "========================================"
echo "  AI 面试助手 - 服务器部署脚本"
echo "========================================"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    log_error "请使用 root 权限运行此脚本"
    exit 1
fi

# 1. 更新系统
log_info "更新系统包..."
apt update && apt upgrade -y

# 2. 安装必要软件
log_info "安装必要软件..."
apt install -y \
    nginx \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    git \
    curl \
    wget \
    vim \
    ufw

# 3. 配置防火墙
log_info "配置防火墙..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable

# 4. 创建项目目录
log_info "创建项目目录..."
mkdir -p /opt/ai-interview-assistant

# 5. 配置 Nginx
log_info "配置 Nginx..."
cat > /etc/nginx/sites-available/interview-assistant << 'EOF'
server {
    listen 80;
    server_name _;

    access_log /var/log/nginx/interview-access.log;
    error_log /var/log/nginx/interview-error.log;

    location / {
        root /opt/ai-interview-assistant/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_set_header Host $host;
    }
}
EOF

# 启用配置
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/interview-assistant /etc/nginx/sites-enabled/

# 测试 Nginx 配置
nginx -t && systemctl restart nginx
systemctl enable nginx

# 6. 创建后端服务
log_info "创建后端服务..."
cat > /etc/systemd/system/interview-api.service << 'EOF'
[Unit]
Description=AI Interview Assistant API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ai-interview-assistant/backend
Environment="PATH=/opt/ai-interview-assistant/backend/venv/bin"
EnvironmentFile=/opt/ai-interview-assistant/backend/.env
ExecStart=/opt/ai-interview-assistant/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable interview-api

log_info "服务器初始化完成！"
echo ""
echo "========================================"
echo "  下一步操作："
echo "========================================"
echo "1. 将代码上传到 /opt/ai-interview-assistant/"
echo "2. 运行 /opt/ai-interview-assistant/deploy/deploy.sh 完成部署"
echo ""
echo "或者使用本地 deploy.sh 一键部署："
echo "  ./deploy.sh"
echo ""
