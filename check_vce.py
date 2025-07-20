from db import get_conn, put_conn

conn = get_conn()
try:
    cur = conn.cursor()
    
    # 检查VCE年级数据
    cur.execute("SELECT DISTINCT target_grade FROM scores WHERE target_grade LIKE '%VCE%' ORDER BY target_grade")
    vce_grades = [row[0] for row in cur.fetchall()]
    print('VCE年级数据:', vce_grades)
    
    # 测试新的年级统计查询
    cur.execute('''
        SELECT 
            CASE 
                WHEN target_grade LIKE '%VCE%' THEN 'VCE'
                ELSE target_grade 
            END as display_grade,
            COUNT(*) as count, 
            AVG(total) as avg_score
        FROM scores 
        GROUP BY 
            CASE 
                WHEN target_grade LIKE '%VCE%' THEN 'VCE'
                ELSE target_grade 
            END
        ORDER BY 
            CASE 
                WHEN target_grade LIKE '%VCE%' THEN 'VCE'
                ELSE target_grade 
            END
    ''')
    
    stats = cur.fetchall()
    print('年级统计结果:')
    for stat in stats:
        print(f"  {stat[0]}: 数量={stat[1]}, 平均分={stat[2]:.2f}")
        
finally:
    put_conn(conn)
