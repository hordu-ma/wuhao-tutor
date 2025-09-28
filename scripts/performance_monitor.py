#!/usr/bin/env python3
"""
性能监控和管理脚本
提供系统性能监控、缓存管理和性能优化工具
"""

import asyncio
import argparse
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.config import get_settings
from src.core.monitoring import get_metrics_collector, get_system_collector
from src.core.security import get_rate_limiter
from src.core.performance import get_query_cache, get_query_monitor, get_database_optimizer
from src.core.database import get_db
from src.utils.cache import cache_manager


settings = get_settings()


class PerformanceMonitor:
    """性能监控管理器"""

    def __init__(self):
        self.metrics_collector = get_metrics_collector()
        self.rate_limiter = get_rate_limiter()
        self.query_cache = get_query_cache()
        self.query_monitor = get_query_monitor()
        self.db_optimizer = get_database_optimizer()

    async def show_system_status(self):
        """显示系统状态概览"""
        print("=" * 80)
        print("系统性能状态概览")
        print("=" * 80)
        print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"环境: {settings.ENVIRONMENT}")
        print(f"性能监控: {'启用' if settings.ENABLE_METRICS else '禁用'}")
        print(f"限流功能: {'启用' if settings.RATE_LIMIT_ENABLED else '禁用'}")

        # 系统指标
        print("\n系统指标:")
        print("-" * 40)
        system_stats = self.metrics_collector.get_system_stats()
        print(f"CPU使用率: {system_stats.get('cpu_percent', 0):.1f}%")
        print(f"内存使用率: {system_stats.get('memory_percent', 0):.1f}%")
        print(f"磁盘使用率: {system_stats.get('disk_usage_percent', 0):.1f}%")
        print(f"活跃连接数: {system_stats.get('active_connections', 0)}")
        print(f"运行时间: {system_stats.get('uptime_seconds', 0):.0f}秒")

        # 请求统计
        print("\n请求统计 (最近1小时):")
        print("-" * 40)
        request_stats = self.metrics_collector.get_request_stats(minutes=60)
        print(f"总请求数: {request_stats['total_requests']}")
        print(f"平均响应时间: {request_stats['avg_response_time']:.3f}s")
        print(f"最小响应时间: {request_stats['min_response_time']:.3f}s")
        print(f"最大响应时间: {request_stats['max_response_time']:.3f}s")
        print(f"错误率: {request_stats['error_rate']:.2f}%")
        print(f"请求频率: {request_stats['requests_per_minute']:.2f} req/min")

        # 缓存统计
        print("\n缓存统计:")
        print("-" * 40)
        cache_stats = self.query_cache.get_stats()
        print(f"缓存命中数: {cache_stats['hit_count']}")
        print(f"缓存未命中数: {cache_stats['miss_count']}")
        print(f"缓存命中率: {cache_stats['hit_rate']:.2f}%")
        print(f"缓存条目数: {cache_stats['cached_entries']}")

        # 限流统计
        print("\n限流统计:")
        print("-" * 40)
        print(f"活跃限流计数器: {len(self.rate_limiter.counters)}")
        print(f"活跃令牌桶: {len(self.rate_limiter.buckets)}")
        print(f"限流规则数: {len(self.rate_limiter.rules)}")

        print("=" * 80)

    async def show_performance_details(self):
        """显示详细性能信息"""
        print("=" * 80)
        print("详细性能分析")
        print("=" * 80)

        # 性能总结
        performance_summary = self.metrics_collector.get_performance_summary()

        print("\n最慢的端点:")
        print("-" * 40)
        slowest_endpoints = performance_summary.get('slowest_endpoints', [])
        if slowest_endpoints:
            for i, endpoint in enumerate(slowest_endpoints[:10], 1):
                print(f"{i:2d}. {endpoint['path']} - {endpoint['avg_response_time']:.3f}s")
        else:
            print("暂无数据")

        print("\n错误率最高的端点:")
        print("-" * 40)
        error_endpoints = performance_summary.get('error_endpoints', [])
        if error_endpoints:
            for i, endpoint in enumerate(error_endpoints[:10], 1):
                print(f"{i:2d}. {endpoint['path']} - {endpoint['error_rate']:.2f}%")
        else:
            print("暂无错误")

        # 查询性能
        print("\n数据库查询统计:")
        print("-" * 40)
        query_stats = self.query_monitor.get_query_stats()
        print(f"总查询数: {query_stats['total_queries']}")
        print(f"平均执行时间: {query_stats['avg_execution_time']:.3f}s")
        print(f"缓存命中率: {query_stats['cache_hit_rate']:.2f}%")

        if query_stats.get('query_types'):
            print("\n查询类型分布:")
            for query_type, count in query_stats['query_types'].items():
                print(f"  {query_type}: {count}")

        if query_stats.get('table_activity'):
            print("\n表活跃度 (前10):")
            for table, count in list(query_stats['table_activity'].items())[:10]:
                print(f"  {table}: {count}")

        # 慢查询
        print("\n慢查询 (前5):")
        print("-" * 40)
        slow_queries = self.query_monitor.get_slow_queries(limit=5)
        if slow_queries:
            for i, sq in enumerate(slow_queries, 1):
                print(f"{i}. 执行时间: {sq['execution_time']:.3f}s, 次数: {sq['count']}")
                print(f"   查询: {sq['query'][:100]}...")
                print()
        else:
            print("暂无慢查询")

        print("=" * 80)

    async def show_optimization_suggestions(self):
        """显示优化建议"""
        print("=" * 80)
        print("性能优化建议")
        print("=" * 80)

        # 获取数据库优化分析
        analysis = None
        try:
            async for db in get_db():
                analysis = await self.db_optimizer.analyze_performance(db)
                break
        except Exception as e:
            print(f"无法连接数据库进行分析: {e}")
            return

        suggestions = analysis.get('optimization_suggestions', []) if analysis else []

        if not suggestions:
            print("✅ 当前系统性能良好，暂无优化建议")
        else:
            print(f"发现 {len(suggestions)} 个优化建议:")
            print()

            for i, suggestion in enumerate(suggestions, 1):
                priority_icon = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(suggestion.get('priority', 'medium'), '⚪')

                print(f"{i}. {priority_icon} [{suggestion.get('priority', 'medium').upper()}] {suggestion.get('type', 'general').upper()}")
                print(f"   {suggestion.get('message', '')}")

                if suggestion.get('details'):
                    print("   详情:")
                    for detail in suggestion['details'][:3]:
                        print(f"     - {detail}")
                print()

        print("=" * 80)

    async def clear_cache(self, cache_type: str = "all"):
        """清理缓存"""
        print(f"清理缓存: {cache_type}")

        if cache_type in ["all", "query"]:
            await self.query_cache.clear_all()
            print("✅ 查询缓存已清理")

        if cache_type in ["all", "redis"]:
            try:
                # 清理Redis缓存
                pattern = f"{cache_manager.prefix}:*"
                keys = await cache_manager.redis_client.keys(pattern) if hasattr(cache_manager, 'redis_client') else []
                if keys:
                    for key in keys:
                        await cache_manager.delete(key)
                    print(f"✅ Redis缓存已清理 ({len(keys)} 个键)")
                else:
                    print("✅ Redis缓存为空")
            except Exception as e:
                print(f"❌ 清理Redis缓存失败: {e}")

        if cache_type in ["all", "metrics"]:
            self.metrics_collector.clear_old_metrics(hours=0)
            print("✅ 监控指标已清理")

        if cache_type in ["all", "slow_queries"]:
            self.query_monitor.clear_slow_queries()
            print("✅ 慢查询记录已清理")

    async def cleanup_old_data(self, hours: int = 24):
        """清理旧数据"""
        print(f"清理 {hours} 小时前的旧数据...")

        # 清理旧的监控数据
        self.metrics_collector.clear_old_metrics(hours=hours)

        # 清理旧的限流计数器
        self.rate_limiter.cleanup_old_counters()

        print("✅ 旧数据清理完成")

    async def export_metrics(self, output_file: str | None = None):
        """导出性能指标"""
        if not output_file:
            output_file = f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        print(f"导出性能指标到: {output_file}")

        # 收集所有指标
        metrics_data = {
            'timestamp': datetime.now().isoformat(),
            'system_stats': self.metrics_collector.get_system_stats(),
            'request_stats': self.metrics_collector.get_request_stats(),
            'path_stats': self.metrics_collector.get_path_stats(),
            'cache_stats': self.query_cache.get_stats(),
            'query_stats': self.query_monitor.get_query_stats(),
            'slow_queries': self.query_monitor.get_slow_queries(limit=20),
            'rate_limit_info': {
                'active_counters': len(self.rate_limiter.counters),
                'active_buckets': len(self.rate_limiter.buckets),
                'rules_count': len(self.rate_limiter.rules)
            }
        }

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False, default=str)
            print(f"✅ 指标导出完成: {output_file}")
        except Exception as e:
            print(f"❌ 导出失败: {e}")

    async def monitor_real_time(self, duration: int = 60, interval: int = 5):
        """实时监控"""
        print(f"开始实时监控 (持续 {duration} 秒, 每 {interval} 秒更新)")
        print("按 Ctrl+C 停止监控")
        print("=" * 80)

        start_time = time.time()

        try:
            while time.time() - start_time < duration:
                # 清屏 (在支持的终端上)
                os.system('clear' if os.name == 'posix' else 'cls')

                # 显示实时状态
                print(f"实时监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 50)

                # 系统资源
                system_stats = self.metrics_collector.get_system_stats()
                print(f"CPU: {system_stats.get('cpu_percent', 0):5.1f}% | ", end="")
                print(f"内存: {system_stats.get('memory_percent', 0):5.1f}% | ", end="")
                print(f"活跃连接: {system_stats.get('active_connections', 0):3d}")

                # 最近请求统计
                recent_stats = self.metrics_collector.get_request_stats(minutes=1)
                print(f"请求/分钟: {recent_stats['requests_per_minute']:6.1f} | ", end="")
                print(f"平均响应时间: {recent_stats['avg_response_time']:6.3f}s | ", end="")
                print(f"错误率: {recent_stats['error_rate']:5.2f}%")

                # 缓存状态
                cache_stats = self.query_cache.get_stats()
                print(f"缓存命中率: {cache_stats['hit_rate']:5.1f}% | ", end="")
                print(f"缓存条目: {cache_stats['cached_entries']:4d}")

                print("-" * 50)

                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            print("\n监控已停止")

    async def health_check(self):
        """健康检查"""
        print("执行系统健康检查...")
        print("=" * 60)

        checks = []

        # 检查系统资源
        system_stats = self.metrics_collector.get_system_stats()
        cpu_usage = system_stats.get('cpu_percent', 0)
        memory_usage = system_stats.get('memory_percent', 0)

        checks.append({
            'name': 'CPU使用率',
            'status': 'OK' if cpu_usage < 80 else 'WARNING' if cpu_usage < 95 else 'CRITICAL',
            'value': f"{cpu_usage:.1f}%",
            'threshold': '< 80% (OK), < 95% (WARNING)'
        })

        checks.append({
            'name': '内存使用率',
            'status': 'OK' if memory_usage < 80 else 'WARNING' if memory_usage < 95 else 'CRITICAL',
            'value': f"{memory_usage:.1f}%",
            'threshold': '< 80% (OK), < 95% (WARNING)'
        })

        # 检查响应时间
        request_stats = self.metrics_collector.get_request_stats(minutes=60)
        avg_response_time = request_stats['avg_response_time']

        checks.append({
            'name': '平均响应时间',
            'status': 'OK' if avg_response_time < 1.0 else 'WARNING' if avg_response_time < 3.0 else 'CRITICAL',
            'value': f"{avg_response_time:.3f}s",
            'threshold': '< 1.0s (OK), < 3.0s (WARNING)'
        })

        # 检查错误率
        error_rate = request_stats['error_rate']

        checks.append({
            'name': '错误率',
            'status': 'OK' if error_rate < 1.0 else 'WARNING' if error_rate < 5.0 else 'CRITICAL',
            'value': f"{error_rate:.2f}%",
            'threshold': '< 1% (OK), < 5% (WARNING)'
        })

        # 检查缓存命中率
        cache_stats = self.query_cache.get_stats()
        hit_rate = cache_stats['hit_rate']

        checks.append({
            'name': '缓存命中率',
            'status': 'OK' if hit_rate > 70 else 'WARNING' if hit_rate > 50 else 'CRITICAL',
            'value': f"{hit_rate:.2f}%",
            'threshold': '> 70% (OK), > 50% (WARNING)'
        })

        # 显示结果
        ok_count = sum(1 for check in checks if check['status'] == 'OK')
        warning_count = sum(1 for check in checks if check['status'] == 'WARNING')
        critical_count = sum(1 for check in checks if check['status'] == 'CRITICAL')

        print(f"健康检查结果: {ok_count} OK, {warning_count} WARNING, {critical_count} CRITICAL")
        print()

        for check in checks:
            status_icon = {'OK': '✅', 'WARNING': '⚠️', 'CRITICAL': '❌'}[check['status']]
            print(f"{status_icon} {check['name']:<20} {check['value']:<15} ({check['threshold']})")

        print("=" * 60)

        overall_status = 'CRITICAL' if critical_count > 0 else 'WARNING' if warning_count > 0 else 'OK'
        print(f"整体状态: {overall_status}")

        return overall_status == 'OK'


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="性能监控和管理工具")
    parser.add_argument('command', choices=[
        'status', 'details', 'suggestions', 'clear-cache', 'cleanup',
        'export', 'monitor', 'health'
    ], help='执行的命令')
    parser.add_argument('--cache-type', choices=['all', 'query', 'redis', 'metrics', 'slow_queries'],
                       default='all', help='缓存类型 (用于 clear-cache)')
    parser.add_argument('--hours', type=int, default=24, help='清理小时数 (用于 cleanup)')
    parser.add_argument('--output', help='输出文件 (用于 export)')
    parser.add_argument('--duration', type=int, default=60, help='监控持续时间秒数 (用于 monitor)')
    parser.add_argument('--interval', type=int, default=5, help='监控更新间隔秒数 (用于 monitor)')

    args = parser.parse_args()

    monitor = PerformanceMonitor()

    try:
        if args.command == 'status':
            await monitor.show_system_status()
        elif args.command == 'details':
            await monitor.show_performance_details()
        elif args.command == 'suggestions':
            await monitor.show_optimization_suggestions()
        elif args.command == 'clear-cache':
            await monitor.clear_cache(args.cache_type)
        elif args.command == 'cleanup':
            await monitor.cleanup_old_data(args.hours)
        elif args.command == 'export':
            await monitor.export_metrics(args.output)
        elif args.command == 'monitor':
            await monitor.monitor_real_time(args.duration, args.interval)
        elif args.command == 'health':
            healthy = await monitor.health_check()
            sys.exit(0 if healthy else 1)

    except KeyboardInterrupt:
        print("\n操作被用户中断")
    except Exception as e:
        print(f"执行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
