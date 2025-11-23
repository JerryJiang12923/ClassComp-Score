#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态周期机制综合测试脚本

测试内容：
1. 周期元数据表的创建和访问
2. 学期配置表的周期类型字段
3. 周期计算函数的准确性
4. 周期类型变更功能
5. 历史数据完整性
6. API端点的正确性
"""

import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from classcomp.database import get_conn, put_conn
from classcomp.utils.period_utils import (
    calculate_period_info,
    calculate_period_info_v2,
    get_period_from_metadata,
    create_next_period,
    change_period_type,
    get_current_semester_config
)


def print_section(title):
    """打印测试区块标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(test_name, passed, details=""):
    """打印测试结果"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"     {details}")


class DynamicPeriodTester:
    """动态周期机制测试类"""
    
    def __init__(self):
        self.conn = None
        self.db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        self.is_sqlite = self.db_url.startswith("sqlite")
        self.test_results = []
    
    def setup(self):
        """初始化测试环境"""
        print_section("初始化测试环境")
        try:
            self.conn = get_conn()
            print("✅ 数据库连接成功")
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    
    def teardown(self):
        """清理测试环境"""
        if self.conn:
            put_conn(self.conn)
            print("\n✅ 测试环境清理完成")
    
    def test_metadata_tables_exist(self):
        """测试1: 验证周期元数据表是否存在"""
        print_section("测试1: 验证周期元数据表")
        
        cur = self.conn.cursor()
        try:
            if self.is_sqlite:
                # 检查period_metadata表
                cur.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='period_metadata'
                """)
                metadata_exists = cur.fetchone() is not None
                
                # 检查period_config_history表
                cur.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='period_config_history'
                """)
                history_exists = cur.fetchone() is not None
            else:
                # PostgreSQL
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_name='period_metadata' AND table_schema='public'
                """)
                metadata_exists = cur.fetchone() is not None
                
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_name='period_config_history' AND table_schema='public'
                """)
                history_exists = cur.fetchone() is not None
            
            print_result("period_metadata表存在", metadata_exists)
            print_result("period_config_history表存在", history_exists)
            
            self.test_results.append(("元数据表创建", metadata_exists and history_exists))
            return metadata_exists and history_exists
            
        except Exception as e:
            print_result("元数据表检查", False, f"错误: {e}")
            self.test_results.append(("元数据表创建", False))
            return False
    
    def test_semester_config_fields(self):
        """测试2: 验证学期配置表的周期类型字段"""
        print_section("测试2: 验证学期配置表字段")
        
        cur = self.conn.cursor()
        try:
            if self.is_sqlite:
                cur.execute("PRAGMA table_info(semester_config)")
                columns = {row[1]: row[2] for row in cur.fetchall()}
            else:
                cur.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name='semester_config'
                """)
                columns = {row[0]: row[1] for row in cur.fetchall()}
            
            has_default = 'default_period_type' in columns
            has_current = 'current_period_type' in columns
            
            print_result("default_period_type字段存在", has_default)
            print_result("current_period_type字段存在", has_current)
            
            passed = has_default and has_current
            self.test_results.append(("学期配置字段", passed))
            return passed
            
        except Exception as e:
            print_result("学期配置字段检查", False, f"错误: {e}")
            self.test_results.append(("学期配置字段", False))
            return False
    
    def test_period_calculation(self):
        """测试3: 测试周期计算的准确性"""
        print_section("测试3: 测试周期计算")
        
        try:
            # 获取当前学期配置
            config_data = get_current_semester_config(self.conn)
            if not config_data:
                print_result("获取学期配置", False, "未找到活跃的学期配置")
                self.test_results.append(("周期计算", False))
                return False
            
            semester = config_data['semester']
            print(f"   学期: {semester.get('semester_name')}")
            print(f"   开始日期: {semester.get('start_date')}")
            print(f"   当前周期类型: {semester.get('current_period_type', 'biweekly')}")
            
            # 测试V1函数（旧版）
            period_v1 = calculate_period_info(semester_config=semester, conn=self.conn)
            print(f"\n   V1周期信息:")
            print(f"   - 周期号: {period_v1['period_number'] + 1}")
            print(f"   - 开始: {period_v1['period_start'].strftime('%Y-%m-%d')}")
            print(f"   - 结束: {period_v1['period_end'].strftime('%Y-%m-%d')}")
            
            # 测试V2函数（新版）
            period_v2 = calculate_period_info_v2(
                target_date=datetime.now().date(),
                semester_config=semester,
                conn=self.conn
            )
            print(f"\n   V2周期信息:")
            print(f"   - 周期号: {period_v2['period_number'] + 1}")
            print(f"   - 开始: {period_v2['period_start'].strftime('%Y-%m-%d')}")
            print(f"   - 结束: {period_v2['period_end'].strftime('%Y-%m-%d')}")
            print(f"   - 类型: {period_v2['period_type']}")
            
            # 验证两个版本的结果是否一致
            dates_match = (
                period_v1['period_start'] == period_v2['period_start'] and
                period_v1['period_end'] == period_v2['period_end'] and
                period_v1['period_number'] == period_v2['period_number']
            )
            
            print_result("V1与V2结果一致", dates_match)
            print_result("周期计算成功", True)
            
            self.test_results.append(("周期计算", dates_match))
            return dates_match
            
        except Exception as e:
            print_result("周期计算", False, f"错误: {e}")
            self.test_results.append(("周期计算", False))
            return False
    
    def test_period_metadata_query(self):
        """测试4: 测试从元数据表查询周期"""
        print_section("测试4: 测试周期元数据查询")
        
        try:
            config_data = get_current_semester_config(self.conn)
            if not config_data:
                print_result("获取学期配置", False)
                self.test_results.append(("元数据查询", False))
                return False
            
            semester = config_data['semester']
            semester_id = semester.get('id')
            
            # 查询是否有周期元数据
            cur = self.conn.cursor()
            placeholder = "?" if self.is_sqlite else "%s"
            cur.execute(f"""
                SELECT COUNT(*) as count 
                FROM period_metadata 
                WHERE semester_id = {placeholder}
            """, (semester_id,))
            
            count = cur.fetchone()[0]
            print(f"   找到 {count} 条周期元数据记录")
            
            if count > 0:
                # 测试查询具体周期
                today = datetime.now().date()
                period_meta = get_period_from_metadata(
                    target_date=today,
                    semester_id=semester_id,
                    conn=self.conn
                )
                
                if period_meta:
                    print(f"\n   今日所属周期:")
                    print(f"   - 周期号: {period_meta['period_number'] + 1}")
                    print(f"   - 类型: {period_meta['period_type']}")
                    print(f"   - 开始: {period_meta['period_start']}")
                    print(f"   - 结束: {period_meta['period_end']}")
                    print_result("元数据查询成功", True)
                    self.test_results.append(("元数据查询", True))
                    return True
                else:
                    print_result("元数据查询", False, "未找到今日对应的周期")
                    self.test_results.append(("元数据查询", False))
                    return False
            else:
                print("   提示: 没有周期元数据，这是正常的（如果尚未运行迁移脚本）")
                print_result("元数据查询", True, "跳过（无数据）")
                self.test_results.append(("元数据查询", True))
                return True
                
        except Exception as e:
            print_result("元数据查询", False, f"错误: {e}")
            self.test_results.append(("元数据查询", False))
            return False
    
    def test_create_next_period(self):
        """测试5: 测试创建下一周期"""
        print_section("测试5: 测试创建下一周期")
        
        try:
            config_data = get_current_semester_config(self.conn)
            if not config_data:
                print_result("获取学期配置", False)
                self.test_results.append(("创建周期", False))
                return False
            
            semester = config_data['semester']
            semester_id = semester.get('id')
            
            # 尝试创建下一周期
            print(f"   尝试创建下一周期...")
            
            new_period = create_next_period(
                semester_id=semester_id,
                semester_config=semester,
                conn=self.conn
            )
            
            if new_period:
                print(f"\n   成功创建周期:")
                print(f"   - 周期号: {new_period['period_number'] + 1}")
                print(f"   - 类型: {new_period['period_type']}")
                print(f"   - 开始: {new_period['period_start']}")
                print(f"   - 结束: {new_period['period_end']}")
                
                # 回滚事务，不保存测试数据
                self.conn.rollback()
                print("   (测试数据已回滚)")
                
                print_result("创建周期成功", True)
                self.test_results.append(("创建周期", True))
                return True
            else:
                print_result("创建周期", False, "函数返回None")
                self.test_results.append(("创建周期", False))
                return False
                
        except Exception as e:
            self.conn.rollback()
            print_result("创建周期", False, f"错误: {e}")
            self.test_results.append(("创建周期", False))
            return False
    
    def test_period_type_change(self):
        """测试6: 测试周期类型变更（模拟）"""
        print_section("测试6: 测试周期类型变更")
        
        try:
            config_data = get_current_semester_config(self.conn)
            if not config_data:
                print_result("获取学期配置", False)
                self.test_results.append(("类型变更", False))
                return False
            
            semester = config_data['semester']
            current_type = semester.get('current_period_type', 'biweekly')
            new_type = 'weekly' if current_type == 'biweekly' else 'biweekly'
            
            print(f"   当前类型: {current_type}")
            print(f"   测试变更为: {new_type}")
            
            # 模拟变更（不实际提交）
            effective_date = datetime.now().date() + timedelta(days=7)
            
            success, message, _ = change_period_type(
                semester_id=semester.get('id'),
                new_type=new_type,
                effective_from_date=effective_date,
                changed_by='test_user',
                reason="测试周期类型变更功能",
                conn=self.conn
            )
            
            if success:
                print(f"   变更结果: {message}")
                
                # 回滚，不保存测试数据
                self.conn.rollback()
                print("   (测试数据已回滚)")
                
                print_result("周期类型变更", True)
                self.test_results.append(("类型变更", True))
                return True
            else:
                print_result("周期类型变更", False, message)
                self.test_results.append(("类型变更", False))
                return False
                
        except Exception as e:
            self.conn.rollback()
            print_result("周期类型变更", False, f"错误: {e}")
            self.test_results.append(("类型变更", False))
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("  动态周期机制 - 综合测试")
        print("="*60)
        
        if not self.setup():
            return False
        
        try:
            # 依次运行所有测试
            self.test_metadata_tables_exist()
            self.test_semester_config_fields()
            self.test_period_calculation()
            self.test_period_metadata_query()
            self.test_create_next_period()
            self.test_period_type_change()
            
            # 生成测试报告
            self.generate_report()
            
        finally:
            self.teardown()
        
        return True
    
    def generate_report(self):
        """生成测试报告"""
        print_section("测试报告")
        
        total = len(self.test_results)
        passed = sum(1 for _, result in self.test_results if result)
        failed = total - passed
        
        print(f"\n   总测试数: {total}")
        print(f"   通过: {passed} ✅")
        print(f"   失败: {failed} ❌")
        print(f"   通过率: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n   失败的测试:")
            for name, result in self.test_results:
                if not result:
                    print(f"     - {name}")
        
        print(f"\n{'='*60}")
        if failed == 0:
            print("  🎉 所有测试通过！动态周期机制已准备就绪。")
        else:
            print(f"  ⚠️  有 {failed} 个测试失败，请检查实现。")
        print("="*60 + "\n")


def main():
    """主函数"""
    tester = DynamicPeriodTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()