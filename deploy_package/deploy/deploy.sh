#!/bin/bash
# AI 面试助手 - 本地一键部署脚本
# 在本地运行此脚本，自动部署到服务器

set -e

# ==================== 配置区域 ====================
SERVER_IP="vocabot.cn"
SERVER_USER="root"
PROJECT_NAME="ai-interview-assistant"
REMOTE_PATH="/opt/${PROJECT_NAME}"
# =================================================

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

echo "========================================"
echo "  AI 面试助手 - 一键部署脚本"
echo "  服务器: ${SERVER_IP}"
echo "========================================"
echo ""

# 检查是否在项目根目录
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    log_error "请在项目根目录运行此脚本"
    exit 1
fi

# 步骤 1: 构建前端
log_step "步骤 1/5: 构建前端项目..."
cd frontend
if [ ! -d "node_modules" ]; then
    log_info "安装前端依赖..."
    npm install
fi
npm run build
if [ ! -d "dist" ]; then
    log_error "前端构建失败，dist 目录不存在"
    exit 1
fi
log_info "前端构建完成"
cd ..

# 步骤 2: 上传代码到服务器
log_step "步骤 2/5: 上传代码到服务器..."

# 创建临时目录，排除不需要的文件
log_info "准备部署文件..."
mkdir -p .deploy_temp
cp -r backend .deploy_temp/
cp -r frontend/dist .deploy_temp/frontend/
cp -r deploy .deploy_temp/

# 上传文件
log_info "上传到服务器 ${SERVER_IP}..."
scp -r .deploy_temp/* ${SERVER_USER}@${SERVER_IP}:${REMOTE_PATH}/

# 清理临时目录
rm -rf .deploy_temp

# 步骤 3: 在服务器上部署后端
log_step "步骤 3/5: 部署后端服务..."
ssh ${SERVER_USER}@${SERVER_IP} << EOF
    set -e
    
    echo "[远程] 创建 Python 虚拟环境..."
    cd ${REMOTE_PATH}/backend
    python3 -m venv venv 2>/dev/null || true
    
    echo "[远程] 安装 Python 依赖..."
    source venv/bin/activate
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    
    # 检查环境变量文件
    if [ ! -f ".env" ]; then
        echo "[远程] 创建默认环境变量文件..."
        cp ../deploy/.env.example .env
        echo "[远程] 警告: 请编辑 ${REMOTE_PATH}/backend/.env 文件，配置 API 密钥"
    fi
    
    echo "[远程] 重启后端服务..."
    systemctl restart interview-api || systemctl start interview-api
    
    echo "[远程] 检查服务状态..."
    sleep 2
    if systemctl is-active --quiet interview-api; then
        echo "[远程] 后端服务运行正常"
    else
        echo "[远程] 后端服务启动失败，请检查日志: journalctl -u interview-api -n 50"
        exit 1
    fi
EOF

# 步骤 4: 配置 Nginx
log_step "步骤 4/5: 配置 Nginx..."
ssh ${SERVER_USER}@${SERVER_IP} << EOF
    set -e
    
    # 确保前端文件存在
    if [ ! -d "${REMOTE_PATH}/frontend/dist" ]; then
        echo "[远程] 错误: 前端文件不存在"
        exit 1
    fi
    
    # 重启 Nginx
    nginx -t && systemctl restart nginx
    
    echo "[远程] Nginx 配置完成"
EOF

# 步骤 5: 验证部署
log_step "步骤 5/5: 验证部署..."
sleep 3

# 检查前端
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://${SERVER_IP}/ || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
    log_info "前端访问正常 (HTTP 200)"
else
    log_warn "前端返回状态码: $HTTP_STATUS"
fi

# 检查后端 API
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://${SERVER_IP}/api/v1/sessions || echo "000")
if [ "$API_STATUS" = "405" ] || [ "$API_STATUS" = "200" ]; then
    log_info "后端 API 正常 (HTTP $API_STATUS)"
else
    log_warn "后端 API 返回状态码: $API_STATUS"
fi

# 部署完成
echo ""
echo "========================================"
echo -e "${GREEN}  部署完成！${NC}"
echo "========================================"
echo ""
echo "访问地址:"
echo "  - 前端页面: http://${SERVER_IP}"
echo "  - API 文档: http://${SERVER_IP}/docs"
echo "  - API 接口: http://${SERVER_IP}/api/"
echo ""
echo "常用命令:"
echo "  # 查看后端日志"
echo "  ssh ${SERVER_USER}@${SERVER_IP} 'journalctl -u interview-api -f'"
echo ""
echo "  # 重启后端服务"
echo "  ssh ${SERVER_USER}@${SERVER_IP} 'systemctl restart interview-api'"
echo ""
echo "  # 查看 Nginx 日志"
echo "  ssh ${SERVER_USER}@${SERVER_IP} 'tail -f /var/log/nginx/interview-error.log'"
echo ""

# 检查是否需要配置 API 密钥
ssh ${SERVER_USER}@${SERVER_IP} << EOF
    if grep -q "your_openai_api_key_here" ${REMOTE_PATH}/backend/.env 2>/dev/null; then
        echo -e "${YELLOW}⚠️  警告: 请配置 API 密钥${NC}"
        echo "   编辑文件: ${REMOTE_PATH}/backend/.env"
        echo "   然后重启服务: systemctl restart interview-api"
    fi
EOF
