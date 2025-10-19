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
NGINX_CONF="/etc/nginx/conf.d/${APP_NAME}.conf"  # ✅ 修正：实际路径是 conf.d
APP_DIR="/opt/wuhao-tutor"  # ✅ 已确认实际路径
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
    
    log_warn "⚠️  注意: 此脚本会在现有配置基础上添加域名支持"
    log_warn "⚠️  不会完全覆盖现有配置（保留限流、安全头等）"
    
    # 备份当前配置（再次确认）
    if [[ -f "$NGINX_CONF" ]]; then
        cp "$NGINX_CONF" "${NGINX_CONF}.pre-domain-migration"
        log_info "✓ 配置已备份到 ${NGINX_CONF}.pre-domain-migration"
    fi
    
    # 检查当前配置中是否已包含域名
    if grep -q "server_name.*${DOMAIN}" "$NGINX_CONF"; then
        log_info "✓ 配置中已包含域名 ${DOMAIN}，跳过修改"
        return
    fi
    
    # 使用 sed 在现有配置中添加域名
    log_info "正在更新 server_name..."
    
    # 更新 HTTP server 块的 server_name（添加域名）
    sed -i "s/server_name 121.199.173.244 localhost;/server_name ${DOMAIN} ${ROOT_DOMAIN} 121.199.173.244 localhost;/g" "$NGINX_CONF"
    
    log_info "✓ Nginx 配置已更新（添加域名到 server_name）"
    
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
    
    # 检查是否已有 Let's Encrypt 证书
    if [[ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]]; then
        log_info "✓ Let's Encrypt 证书已存在，跳过申请"
        log_info "如需重新申请，请先删除: rm -rf /etc/letsencrypt/live/${DOMAIN}"
        return
    fi
    
    # 创建 certbot 目录
    mkdir -p /var/www/certbot
    
    # 检查 certbot 是否安装
    if ! command -v certbot &> /dev/null; then
        log_info "正在安装 Certbot..."
        apt update
        apt install -y certbot python3-certbot-nginx
    fi
    
    log_info "正在申请 SSL 证书..."
    log_warn "请输入你的邮箱 (用于证书到期提醒，直接回车使用默认): "
    read -p "邮箱: " USER_EMAIL
    EMAIL=${USER_EMAIL:-$EMAIL}
    
    # 验证邮箱格式
    if [[ ! "$EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        log_warn "邮箱格式无效，使用默认邮箱: admin@${ROOT_DOMAIN}"
        EMAIL="admin@${ROOT_DOMAIN}"
    fi
    
    log_info "使用邮箱: $EMAIL"
    
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
        
        # 更新 Nginx 配置，移除自签名证书配置（Certbot 会自动更新）
        log_info "✓ Certbot 已自动更新 Nginx 配置使用 Let's Encrypt 证书"
    else
        log_error "✗ SSL 证书申请失败"
        log_warn "可能的原因："
        log_warn "  1. DNS 尚未完全生效，请等待后重试"
        log_warn "  2. 80 端口未开放或被占用"
        log_warn "  3. Nginx 配置有误"
        log_warn ""
        log_warn "手动申请命令: certbot --nginx -d $DOMAIN -d $ROOT_DOMAIN --email $EMAIL"
        read -p "是否继续（跳过 SSL 配置）？[y/N] " CONTINUE
        if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
            exit 1
        fi
        return
    fi
    
    # 测试自动续期
    log_info "测试证书自动续期..."
    if certbot renew --dry-run &>/dev/null; then
        log_info "✓ 自动续期配置正常"
    else
        log_warn "⚠ 自动续期测试失败，请手动检查"
    fi
    
    log_info "✓ SSL 证书配置完成"
}

# 步骤 6: 更新应用配置
update_app_config() {
    log_info "步骤 6: 更新应用配置..."
    
    if [[ -f "${APP_DIR}/.env.production" ]]; then
        # 备份环境变量文件
        cp "${APP_DIR}/.env.production" "${APP_DIR}/.env.production.backup-$(date +%Y%m%d_%H%M%S)"
        
        # 更新 BASE_URL
        if grep -q "^BASE_URL=" "${APP_DIR}/.env.production"; then
            sed -i "s|^BASE_URL=.*|BASE_URL=https://${DOMAIN}|g" "${APP_DIR}/.env.production"
            log_info "✓ BASE_URL 已更新为: https://${DOMAIN}"
        else
            echo "BASE_URL=https://${DOMAIN}" >> "${APP_DIR}/.env.production"
            log_info "✓ 已添加 BASE_URL=https://${DOMAIN}"
        fi
        
        # 更新 CORS 配置（添加域名到现有列表）
        if grep -q "^BACKEND_CORS_ORIGINS=" "${APP_DIR}/.env.production"; then
            # 读取当前的 CORS 配置
            CURRENT_CORS=$(grep "^BACKEND_CORS_ORIGINS=" "${APP_DIR}/.env.production" | cut -d= -f2-)
            
            # 如果不包含新域名，则添加
            if ! echo "$CURRENT_CORS" | grep -q "${DOMAIN}"; then
                # 构建新的 CORS 列表（添加域名）
                NEW_CORS="'[\"https://${DOMAIN}\",\"http://${DOMAIN}\",\"https://${ROOT_DOMAIN}\",\"http://${ROOT_DOMAIN}\",\"https://121.199.173.244\",\"http://121.199.173.244\"]'"
                sed -i "s|^BACKEND_CORS_ORIGINS=.*|BACKEND_CORS_ORIGINS=${NEW_CORS}|g" "${APP_DIR}/.env.production"
                log_info "✓ CORS 配置已更新，添加域名支持"
            else
                log_info "✓ CORS 配置已包含域名，无需修改"
            fi
        fi
        
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
