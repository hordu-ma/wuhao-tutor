#!/bin/bash
# 小程序测试前配置检查脚本

echo "🔍 五好伴学小程序测试前配置检查"
echo "=================================="

PROJECT_ROOT="/Users/liguoma/my-devs/python/wuhao-tutor"
MINIPROGRAM_PATH="$PROJECT_ROOT/miniprogram"

# 检查项目路径
echo "📁 检查项目路径..."
if [ -d "$MINIPROGRAM_PATH" ]; then
    echo "   ✅ 小程序目录存在: $MINIPROGRAM_PATH"
else
    echo "   ❌ 小程序目录不存在: $MINIPROGRAM_PATH"
    exit 1
fi

# 检查关键文件
echo ""
echo "📄 检查关键文件..."

files=(
    "app.js"
    "app.json" 
    "config/index.js"
    "utils/request.js"
    "utils/auth.js"
    "pages/login/index.js"
    "pages/index/index.js"
)

for file in "${files[@]}"; do
    if [ -f "$MINIPROGRAM_PATH/$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (缺失)"
    fi
done

# 检查配置文件
echo ""
echo "⚙️  检查配置..."

if [ -f "$MINIPROGRAM_PATH/config/index.js" ]; then
    echo "   📋 API配置检查:"
    
    # 检查API地址
    api_url=$(grep "baseUrl:" "$MINIPROGRAM_PATH/config/index.js" | head -1 | sed "s/.*baseUrl: *['\"]\\([^'\"]*\\)['\"].*/\\1/")
    if [ "$api_url" = "https://121.199.173.244" ]; then
        echo "   ✅ API地址正确: $api_url"
    else
        echo "   ⚠️  API地址: $api_url (请确认是否正确)"
    fi
    
    # 检查环境配置
    env=$(grep "environment:" "$MINIPROGRAM_PATH/config/index.js" | head -1 | sed "s/.*environment: *['\"]\\([^'\"]*\\)['\"].*/\\1/")
    echo "   📊 当前环境: $env"
    
    # 检查超时配置
    timeout=$(grep "timeout:" "$MINIPROGRAM_PATH/config/index.js" | head -1 | sed "s/.*timeout: *\\([0-9]*\\).*/\\1/")
    echo "   ⏱️  请求超时: ${timeout}ms"
fi

# 检查页面配置
echo ""
echo "📱 检查页面配置..."

if [ -f "$MINIPROGRAM_PATH/app.json" ]; then
    # 检查首页配置
    first_page=$(grep -A 1 '"pages"' "$MINIPROGRAM_PATH/app.json" | tail -1 | sed 's/[^"]*"\\([^"]*\\)".*/\\1/')
    echo "   🏠 首页: $first_page"
    
    # 检查Tab配置
    if grep -q '"tabBar"' "$MINIPROGRAM_PATH/app.json"; then
        echo "   📋 TabBar: 已配置"
    else
        echo "   📋 TabBar: 未配置"
    fi
fi

# 检查依赖项
echo ""
echo "📦 检查依赖项..."

if [ -f "$MINIPROGRAM_PATH/package.json" ]; then
    echo "   ✅ package.json 存在"
    
    if [ -d "$MINIPROGRAM_PATH/node_modules" ]; then
        echo "   ✅ node_modules 存在"
    else
        echo "   ⚠️  node_modules 不存在，可能需要运行 npm install"
    fi
else
    echo "   ➖ 无 package.json (小程序可能不需要)"
fi

# 生成测试建议
echo ""
echo "💡 测试建议:"
echo "   1. 启动微信开发者工具"
echo "   2. 导入项目: $MINIPROGRAM_PATH"
echo "   3. 在详情->本地设置中勾选'不校验合法域名'"
echo "   4. 使用测试账号: 13800000001 / password123"
echo "   5. 按照测试清单逐项验证"

# 检查后端API状态
echo ""
echo "🌐 检查后端API状态..."
api_status=$(curl -k -s -o /dev/null -w "%{http_code}" "https://121.199.173.244/api/v1/health/" 2>/dev/null)

if [ "$api_status" = "200" ]; then
    echo "   ✅ 后端API正常 (HTTP $api_status)"
else
    echo "   ⚠️  后端API异常 (HTTP $api_status)"
    echo "   请先确保后端服务正常运行"
fi

echo ""
echo "🚀 配置检查完成！准备开始测试..."
echo ""
echo "📋 快速测试清单:"
echo "   □ 启动微信开发者工具"
echo "   □ 导入小程序项目"
echo "   □ 配置不校验域名"
echo "   □ 编译并启动小程序"
echo "   □ 测试登录功能"
echo "   □ 测试核心功能"
echo ""
echo "📖 详细测试指南请查看:"
echo "   - MINIPROGRAM_TESTING_GUIDE.md (完整流程)"
echo "   - MINIPROGRAM_TESTING_CHECKLIST.md (快速清单)"