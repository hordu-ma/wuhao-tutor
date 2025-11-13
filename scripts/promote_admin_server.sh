#!/bin/bash
# 在生产服务器上执行此脚本，将张小明提升为管理员

PHONE="18888333726"

echo "=========================================="
echo "五好伴学 - 管理员提升工具"
echo "=========================================="
echo ""
echo "目标用户: $PHONE (张小明)"
echo ""

# 加载生产环境变量
if [ -f /opt/wuhao-tutor/.env.production ]; then
    source /opt/wuhao-tutor/.env.production
    echo "✅ 已加载生产环境配置"
else
    echo "❌ 找不到 .env.production 文件"
    exit 1
fi

# 提取数据库连接信息
DB_HOST=$(echo $SQLALCHEMY_DATABASE_URI | sed -n 's/.*@\(.*\):.*/\1/p')
DB_PORT=$(echo $SQLALCHEMY_DATABASE_URI | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_NAME=$(echo $SQLALCHEMY_DATABASE_URI | sed -n 's/.*\/\(.*\)/\1/p')
DB_USER=$POSTGRES_USER
DB_PASS=$POSTGRES_PASSWORD

echo ""
echo "📋 1. 查询当前用户信息..."
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT id, phone, nickname, role 
FROM users 
WHERE phone = '$PHONE';
"

echo ""
echo "🔄 2. 更新为管理员角色..."
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
UPDATE users 
SET role = 'admin' 
WHERE phone = '$PHONE';
"

echo ""
echo "✅ 3. 验证更新结果..."
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT phone, nickname, role, updated_at
FROM users 
WHERE phone = '$PHONE';
"

echo ""
echo "📊 4. 显示所有管理员..."
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT phone, nickname, role 
FROM users 
WHERE role = 'admin' 
ORDER BY created_at;
"

echo ""
echo "=========================================="
echo "✅ 操作完成！"
echo "=========================================="
