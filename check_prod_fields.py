import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        host='pgm-bp1ce0sp88j6ha90.pg.rds.aliyuncs.com',
        port=5432,
        user='horsdu_ma',
        password='MA-keit13',
        database='wuhao_tutor'
    )
    
    rows = await conn.fetch("""
        SELECT id, COALESCE(title, '无标题'), mastery_status, source
        FROM mistake_records
        WHERE subject='数学'
        ORDER BY created_at DESC
    """)
    
    print(f'\n找到 {len(rows)} 条数学错题:\n')
    for i, row in enumerate(rows, 1):
        title = row[1][:30]
        print(f"{i}. {title:<30} | mastery={row[2]:<10} | source={row[3]:<15}")
    
    # 统计
    stats = await conn.fetch("""
        SELECT mastery_status, COUNT(*)
        FROM mistake_records
        WHERE subject='数学'
        GROUP BY mastery_status
    """)
    print('\nmastery_status分布:')
    for row in stats:
        print(f'  {row[0]}: {row[1]} 条')
    
    stats = await conn.fetch("""
        SELECT source, COUNT(*)
        FROM mistake_records
        WHERE subject='数学'
        GROUP BY source
    """)
    print('\nsource分布:')
    for row in stats:
        print(f'  {row[0]}: {row[1]} 条')
    
    await conn.close()

asyncio.run(main())
