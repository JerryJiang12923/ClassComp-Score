#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('classcomp.db')
conn.row_factory = sqlite3.Row

print("=== 检查重复评分情况 ===")
print("检查是否有多个检查者给同一个班级评分")

for grade in ['中预', '初一', '初二', '高一', '高二']:
    pairs = conn.execute('''
        SELECT target_class, evaluator_class, COUNT(*) as count
        FROM scores 
        WHERE target_grade=? 
        GROUP BY target_class, evaluator_class
        HAVING COUNT(*) > 1
    ''', (grade,)).fetchall()
    
    print(f"\n{grade} 年级重复评分: {len(pairs)}")
    for pair in pairs[:3]:
        print(f"  {pair['target_class']} 被 {pair['evaluator_class']} 评分 {pair['count']}次")

print("\n=== 每个班级的总评分者数量 ===")
for grade in ['中预', '初一', '初二', '高一', '高二']:
    stats = conn.execute('''
        SELECT target_class, COUNT(DISTINCT evaluator_class) as evaluators, COUNT(*) as scores
        FROM scores 
        WHERE target_grade=? 
        GROUP BY target_class
    ''', (grade,)).fetchall()
    
    print(f"\n{grade} 年级:")
    for stat in stats[:5]:
        print(f"  {stat['target_class']}: {stat['evaluators']}个检查者, {stat['scores']}条评分")

conn.close()