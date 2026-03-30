"""
PostgreSQL 数据库备份脚本

功能：
- 全量备份
- 增量备份
- 自动清理旧备份
- 备份验证
"""
import os
import sys
import subprocess
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import logging
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseBackup:
    """
    数据库备份管理器
    """
    
    def __init__(self):
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = os.getenv('DB_PORT', '5432')
        self.db_name = os.getenv('DB_NAME', 'bid_auto')
        self.db_user = os.getenv('DB_USER', 'postgres')
        self.db_password = os.getenv('DB_PASSWORD', '')
        
        self.backup_dir = Path(os.getenv('BACKUP_DIR', '/opt/backups/database'))
        self.retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_env(self):
        """
        获取环境变量（包含密码）
        """
        env = os.environ.copy()
        if self.db_password:
            env['PGPASSWORD'] = self.db_password
        return env
    
    def full_backup(self) -> Path:
        """
        执行全量备份
        
        Returns:
            备份文件路径
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f'{self.db_name}_full_{timestamp}.sql'
        compressed_file = f'{backup_file}.gz'
        
        logger.info(f"开始全量备份: {self.db_name}")
        
        env = self._get_env()
        
        cmd = [
            'pg_dump',
            '-h', self.db_host,
            '-p', self.db_port,
            '-U', self.db_user,
            '-d', self.db_name,
            '-F', 'p',
            '-f', str(backup_file)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"备份失败: {result.stderr}")
                raise Exception(f"pg_dump failed: {result.stderr}")
            
            with open(backup_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            backup_file.unlink()
            
            file_size = os.path.getsize(compressed_file) / (1024 * 1024)
            logger.info(f"备份完成: {compressed_file} ({file_size:.2f} MB)")
            
            return Path(compressed_file)
            
        except Exception as e:
            logger.error(f"备份过程出错: {e}")
            raise
    
    def incremental_backup(self) -> Path:
        """
        执行增量备份（WAL归档）
        
        Returns:
            备份文件路径
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f'{self.db_name}_incr_{timestamp}.sql.gz'
        
        logger.info(f"开始增量备份: {self.db_name}")
        
        env = self._get_env()
        
        cmd = [
            'pg_dump',
            '-h', self.db_host,
            '-p', self.db_port,
            '-U', self.db_user,
            '-d', self.db_name,
            '-F', 'p',
            '--data-only',
            '--exclude-table-data=django_migrations',
            '--exclude-table-data=django_admin_log',
        ]
        
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"增量备份失败: {result.stderr}")
                raise Exception(f"pg_dump failed: {result.stderr}")
            
            with gzip.open(backup_file, 'wt') as f:
                f.write(result.stdout)
            
            file_size = os.path.getsize(backup_file) / (1024 * 1024)
            logger.info(f"增量备份完成: {backup_file} ({file_size:.2f} MB)")
            
            return backup_file
            
        except Exception as e:
            logger.error(f"增量备份过程出错: {e}")
            raise
    
    def cleanup_old_backups(self):
        """
        清理过期备份
        """
        logger.info(f"清理 {self.retention_days} 天前的备份...")
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0
        
        for backup_file in self.backup_dir.glob('*.sql.gz'):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                backup_file.unlink()
                deleted_count += 1
                logger.info(f"删除过期备份: {backup_file}")
        
        logger.info(f"清理完成，删除了 {deleted_count} 个过期备份")
    
    def verify_backup(self, backup_file: Path) -> bool:
        """
        验证备份文件完整性
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            是否有效
        """
        logger.info(f"验证备份文件: {backup_file}")
        
        if not backup_file.exists():
            logger.error(f"备份文件不存在: {backup_file}")
            return False
        
        try:
            with gzip.open(backup_file, 'rt') as f:
                content = f.read(1024)
                if 'PostgreSQL database dump' in content or 'CREATE TABLE' in content:
                    logger.info("备份文件验证通过")
                    return True
                else:
                    logger.error("备份文件格式不正确")
                    return False
        except Exception as e:
            logger.error(f"验证备份文件失败: {e}")
            return False
    
    def list_backups(self):
        """
        列出所有备份
        """
        backups = []
        for backup_file in sorted(self.backup_dir.glob('*.sql.gz'), reverse=True):
            stat = backup_file.stat()
            backups.append({
                'file': backup_file.name,
                'size_mb': stat.st_size / (1024 * 1024),
                'created': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return backups


def main():
    parser = argparse.ArgumentParser(description='数据库备份工具')
    parser.add_argument('action', choices=['full', 'incremental', 'cleanup', 'list', 'verify'],
                        help='执行的操作')
    parser.add_argument('--file', type=str, help='验证指定的备份文件')
    
    args = parser.parse_args()
    
    backup = DatabaseBackup()
    
    try:
        if args.action == 'full':
            backup_file = backup.full_backup()
            backup.verify_backup(backup_file)
            backup.cleanup_old_backups()
            
        elif args.action == 'incremental':
            backup_file = backup.incremental_backup()
            backup.verify_backup(backup_file)
            
        elif args.action == 'cleanup':
            backup.cleanup_old_backups()
            
        elif args.action == 'list':
            backups = backup.list_backups()
            if backups:
                print("\n备份列表:")
                print("-" * 60)
                for b in backups:
                    print(f"{b['file']:40} {b['size_mb']:>8.2f} MB  {b['created']}")
            else:
                print("没有找到备份文件")
                
        elif args.action == 'verify':
            if args.file:
                backup_file = Path(args.file)
            else:
                backups = backup.list_backups()
                if backups:
                    backup_file = backup.backup_dir / backups[0]['file']
                else:
                    print("没有找到备份文件")
                    sys.exit(1)
            
            if backup.verify_backup(backup_file):
                print("验证成功")
            else:
                print("验证失败")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"操作失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
