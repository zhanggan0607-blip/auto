import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'

import django
django.setup()

from django.db import connection

print('=' * 70)
print('Django 数据库配置详细检查')
print('=' * 70)

print('\n【当前加载的settings模块】')
print(f'  DJANGO_SETTINGS_MODULE: {os.environ.get("DJANGO_SETTINGS_MODULE")}')

print('\n【从.env文件读取的配置】')
print(f'  DB_NAME: {os.getenv("DB_NAME")}')
print(f'  DB_USER: {os.getenv("DB_USER")}')
print(f'  DB_PASSWORD: {os.getenv("DB_PASSWORD")}')
print(f'  DB_HOST: {os.getenv("DB_HOST")}')
print(f'  DB_PORT: {os.getenv("DB_PORT")}')

print('\n【Django connection.settings_dict】')
for key, value in connection.settings_dict.items():
    if key == 'PASSWORD':
        value = '***'  # 隐藏密码
    print(f'  {key}: {value}')

print('\n【连接测试】')
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        print(f'  ✓ 执行SELECT 1: {result}')

        cursor.execute('SELECT current_database(), current_user')
        db, user = cursor.fetchone()
        print(f'  ✓ 当前数据库: {db}')
        print(f'  ✓ 当前用户: {user}')

        cursor.execute('SHOW max_connections')
        max_conn = cursor.fetchone()[0]
        print(f'  ✓ 最大连接数: {max_conn}')

    print('\n  连接状态: 成功 ✓')
except Exception as e:
    print(f'\n  连接状态: 失败 ✗')
    print(f'  错误信息: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

print('\n【数据库统计信息】')
try:
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT
                numbackends,
                xact_commit,
                xact_rollback,
                blks_hit,
                blks_read,
                ROUND(100.0 * blks_hit / NULLIF(blks_hit + blks_read, 0), 2) AS cache_hit_ratio
            FROM pg_stat_database
            WHERE datname = current_database()
        ''')
        row = cursor.fetchone()
        print(f'  当前连接数: {row[0]}')
        print(f'  事务提交数: {row[1]}')
        print(f'  事务回滚数: {row[2]}')
        print(f'  缓存命中: {row[3]}')
        print(f'  磁盘读取: {row[4]}')
        print(f'  缓存命中率: {row[5]}%')
except Exception as e:
    print(f'  获取统计信息失败: {e}')

print('\n【活跃连接详情】')
try:
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT
                pid,
                application_name,
                state,
                query_start,
                ROUND(EXTRACT(EPOCH FROM (now() - query_start)), 2) AS duration_sec
            FROM pg_stat_activity
            WHERE datname = current_database()
            ORDER BY query_start
        ''')
        print(f'  {"PID":<6} {"应用":<15} {"状态":<8} {"开始时间":<28} {"时长(秒)":<10}')
        print(f'  {"-"*6} {"-"*15} {"-"*8} {"-"*28} {"-"*10}')
        for row in cursor.fetchall():
            print(f'  {row[0]:<6} {row[1] or "psql":<15} {row[2]:<8} {str(row[3]):<28} {row[4]:<10}')
except Exception as e:
    print(f'  获取活跃连接失败: {e}')

print('\n' + '=' * 70)
print('检查完成')
print('=' * 70)
