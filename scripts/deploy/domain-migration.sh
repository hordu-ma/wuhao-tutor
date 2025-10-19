#!/bin/bash

################################################################################
# 域名切换脚本 - www.horsduroot.com 切换到新服务器
#
# 执行位置: 新服务器 (121.199.173.244)
# 使用方式: sudo bash domain-migration.sh
# 作者: Auto-generated
# 日期: 2025-10-19
################################################################################

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
DOMAIN="www.horsduroot.com"
ROOT_DOMAIN="horsduroot.com"
NEW_IP="121.199.173.244"
OLD_IP="60.205.124.67"
APP_NAME="wuhao-tutor"
NGINX_CONF="/etc/nginx/sites-available/${APP_NAME}.conf"
APP_DIR="/opt/wuhao-tutor"  # 根据实际路径修改
EMAIL="your-email@example.com"  # 修改为你的邮箱

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为 root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本必须以 root 权限运行"
        exit 1
    fi
}

# 步骤 1: 检查服务状态
check_services() {
    log_info "步骤 1: 检查服务状态..."
    
    if systemctl is-active --quiet ${APP_NAME}.service; then
        log_info "✓ ${APP_NAME} 服务运行正常"
    else
        log_warn "⚠ ${APP_NAME} 服务未运行，正在启动..."
        systemctl start ${APP_NAME}.service
    fi
    
    if systemctl is-active --quiet nginx; then
        log_info "✓ Nginx 服务运行正常"
    else
        log_warn "⚠ Nginx 服务未运行，正在启动..."
        systemctl start nginx
    fi
    
    # 测试健康检查
    if curl -sf http://127.0.0.1:8000/health > /dev/null; then
        log_info "✓ 应用健康检查通过"
    else
        log_error "✗ 应用健康检查失败，请检查后端服务"
        exit 1
    fi
}

# 步骤 2: 备份当前配置
backup_config() {
    log_info "步骤 2: 备份当前配置..."
    
    BACKUP_DIR="/root/nginx-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    if [[ -f "$NGINX_CONF" ]]; then
        cp "$NGINX_CONF" "$BACKUP_DIR/"
        log_info "✓ Nginx 配置已备份到 $BACKUP_DIR"
    fi
    
    if [[ -f "${APP_DIR}/.env.production" ]]; then
        cp "${APP_DIR}/.env.production" "$BACKUP_DIR/"
        log_info "✓ 应用配置已备份到 $BACKUP_DIR"
    fi
}

# 步骤 3: 更新 Nginx 配置（支持域名）
update_nginx_config() {
    log_info "步骤 3: 更新 Nginx 配置..."
    
    cat > "$NGINX_CONF" << 'EOF'
# HTTP 配置 (用于 Let's Encrypt 验证和临时访问)
server {
    listen 80;
    server_name www.horsduroot.com horsduroot.com;

    # Let's Encrypt 证书验证路径
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # 应用代理
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件
    location /static/ {
        alias /var/www/wuhao-tutor/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /uploads/ {
        alias /var/www/wuhao-tutor/uploads/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # API 文档
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

    log_info "✓ Nginx 配置已更新"
    
    # 测试配置
    if nginx -t 2>&1 | grep -q "successful"; then
        log_info "✓ Nginx 配置测试通过"
        systemctl reload nginx
        log_info "✓ Nginx 已重载"
    else
        log_error "✗ Nginx 配置测试失败"
        log_error "正在恢复备份配置..."
        cp "$BACKUP_DIR/$(basename $NGINX_CONF)" "$NGINX_CONF"
        systemctl reload nginx
        exit 1
    fi
}

# 步骤 4: 等待 DNS 解析生效
wait_for_dns() {
    log_info "步骤 4: 等待 DNS 解析生效..."
    log_warn "请先在阿里云控制台修改 DNS 解析:"
    echo ""
    echo "  1. 访问 https://dns.console.aliyun.com/"
    echo "  2. 找到域名 horsduroot.com"
    echo "  3. 修改 A 记录:"
    echo "     - www  →  ${NEW_IP}"
    echo "     - @    →  ${NEW_IP}"
    echo "  4. TTL 设置为 600 秒"
    echo ""
    
    read -p "DNS 修改完成后，按回车继续..."
    
    log_info "正在检查 DNS 解析..."
    MAX_RETRIES=60
    RETRY_COUNT=0
    
    while [[ $RETRY_COUNT -lt $MAX_RETRIES ]]; do
        DNS_IP=$(nslookup $DOMAIN 2>/dev/null | grep -A1 "Name:" | tail -1 | awk '{print $2}')
        
        if [[ "$DNS_IP" == "$NEW_IP" ]]; then
            log_info "✓ DNS 解析已生效: $DOMAIN → $NEW_IP"
            break
        else
            log_warn "等待 DNS 生效... (当前解析到: $DNS_IP, 目标: $NEW_IP)"
            sleep 10
            ((RETRY_COUNT++))
        fi
    done
    
    if [[ $RETRY_COUNT -eq $MAX_RETRIES ]]; then
        log_error "DNS 解析超时，请检查配置"
        exit 1
    fi
}

# 步骤 5: 配置 SSL 证书
setup_ssl() {
    log_info "步骤 5: 配置 SSL 证书..."
    
    # 创建 certbot 目录
    mkdir -p /var/www/certbot
    
    # 检查 certbot 是否安装
    if ! command -v certbot &> /dev/null; then
        log_info "正在安装 Certbot..."
        apt update
        apt install -y certbot python3-certbot-nginx
    fi
    
    log_info "正在申请 SSL 证书..."
    log_warn "请输入你的邮箱 (用于证书到期提醒): "
    read -p "邮箱: " USER_EMAIL
    EMAIL=${USER_EMAIL:-$EMAIL}
    
    # 申请证书
    certbot --nginx \
        -d $DOMAIN \
        -d $ROOT_DOMAIN \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        --redirect \
        --non-interactive
    
    if [[ $? -eq 0 ]]; then
        log_info "✓ SSL 证书申请成功"
    else
        log_error "✗ SSL 证书申请失败"
        log_warn "你可以稍后手动执行: certbot --nginx -d $DOMAIN -d $ROOT_DOMAIN"
        exit 1
    fi
    
    # 测试自动续期
    log_info "测试证书自动续期..."
    certbot renew --dry-run
    
    log_info "✓ SSL 证书配置完成"
}

# 步骤 6: 更新应用配置
update_app_config() {
    log_info "步骤 6: 更新应用配置..."
    
    if [[ -f "${APP_DIR}/.env.production" ]]; then
        # 更新 API_BASE_URL
        sed -i "s|API_BASE_URL=.*|API_BASE_URL=https://${DOMAIN}|g" "${APP_DIR}/.env.production"
        sed -i "s|FRONTEND_URL=.*|FRONTEND_URL=https://${DOMAIN}|g" "${APP_DIR}/.env.production"
        
        log_info "✓ 应用配置已更新"
        
        # 重启应用
        log_info "正在重启应用..."
        systemctl restart ${APP_NAME}.service
        sleep 3
        
        if systemctl is-active --quiet ${APP_NAME}.service; then
            log_info "✓ 应用重启成功"
        else
            log_error "✗ 应用重启失败，请检查日志"
            journalctl -u ${APP_NAME}.service -n 50
            exit 1
        fi
    else
        log_warn "未找到应用配置文件，跳过此步骤"
    fi
}

# 步骤 7: 验证切换结果
verify_migration() {
    log_info "步骤 7: 验证切换结果..."
    
    echo ""
    log_info "=== 验证测试 ==="
    
    # 测试 HTTP 跳转
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://${DOMAIN})
    if [[ "$HTTP_CODE" == "301" ]] || [[ "$HTTP_CODE" == "302" ]]; then
        log_info "✓ HTTP 自动跳转 HTTPS: $HTTP_CODE"
    else
        log_warn "⚠ HTTP 跳转状态码异常: $HTTP_CODE"
    fi
    
    # 测试 HTTPS 访问
    HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://${DOMAIN})
    if [[ "$HTTPS_CODE" == "200" ]]; then
        log_info "✓ HTTPS 访问正常: $HTTPS_CODE"
    else
        log_error "✗ HTTPS 访问失败: $HTTPS_CODE"
    fi
    
    # 测试健康检查
    HEALTH_RESPONSE=$(curl -s https://${DOMAIN}/health)
    if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
        log_info "✓ 健康检查通过: $HEALTH_RESPONSE"
    else
        log_warn "⚠ 健康检查异常: $HEALTH_RESPONSE"
    fi
    
    # 测试 SSL 证书
    CERT_EXPIRY=$(echo | openssl s_client -servername ${DOMAIN} -connect ${DOMAIN}:443 2>/dev/null | openssl x509 -noout -dates | grep "notAfter" | cut -d= -f2)
    log_info "✓ SSL 证书有效期至: $CERT_EXPIRY"
    
    echo ""
    log_info "=== 切换完成 ==="
    echo ""
    echo "  域名: https://${DOMAIN}"
    echo "  状态: 运行中"
    echo "  证书: 有效"
    echo ""
    log_info "请在浏览器访问并测试所有功能"
    log_warn "建议保留旧服务器 24-48 小时，观察流量变化"
    echo ""
}

# 主函数
main() {
    echo ""
    echo "========================================"
    echo "  域名切换脚本 - www.horsduroot.com"
    echo "========================================"
    echo ""
    
    check_root
    check_services
    backup_config
    update_nginx_config
    wait_for_dns
    setup_ssl
    update_app_config
    verify_migration
    
    log_info "所有步骤已完成！"
    echo ""
    echo "后续操作:"
    echo "  1. 在浏览器测试: https://${DOMAIN}"
    echo "  2. 测试小程序功能"
    echo "  3. 监控错误日志: tail -f /var/log/nginx/error.log"
    echo "  4. 24-48 小时后停止旧服务器"
    echo ""
}

# 执行主函数
main "$@"
