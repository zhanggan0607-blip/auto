"""
废弃文件清理脚本
自动备份并删除项目中已废弃的文件

使用方法:
    python cleanup_deprecated_files.py [--dry-run] [--no-backup]

参数:
    --dry-run    仅显示将要删除的文件，不实际执行
    --no-backup  不创建备份（不推荐）
"""
import os
import shutil
import argparse
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).parent


DEPRECATED_FILES = [
    "apps/documents/models.py::CompanyInfo",
    "openclaw/llm_service.py",
    "openclaw/base_agent.py",
    "crawler/shanghai_gov_crawler.py",
    "apps/enterprise/services_v2.py",
    "apps/enterprise/views_v2.py",
    "apps/enterprise/urls_v2.py",
    "db.sqlite3",
    "REFACTOR_PLAN.py",
    "create_admin.py",
    "create_db.py",
    "create_shanghai_source.py",
    "init_saas_modules.py",
]


DEPRECATED_DIRS = [
]


UNUSED_API_MODULES = [
    "apps/search_config",
]


def create_backup():
    """
    创建备份目录
    """
    backup_dir = BASE_DIR / "cleanup_backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ 备份目录创建成功: {backup_dir}")
    return backup_dir


def backup_file(file_path: Path, backup_dir: Path):
    """
    备份单个文件
    """
    if file_path.exists():
        relative_path = file_path.relative_to(BASE_DIR)
        backup_path = backup_dir / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        print(f"  📦 已备份: {relative_path}")
        return True
    return False


def delete_file(file_path: Path, is_dry_run: bool = True):
    """
    删除文件
    """
    if not file_path.exists():
        print(f"  ⚠️ 文件不存在: {file_path.relative_to(BASE_DIR)}")
        return False
    
    relative_path = file_path.relative_to(BASE_DIR)
    
    if is_dry_run:
        print(f"  🔍 [DRY-RUN] 将删除: {relative_path}")
    else:
        file_path.unlink()
        print(f"  🗑️ 已删除: {relative_path}")
    return True


def delete_dir(dir_path: Path, is_dry_run: bool = True):
    """
    删除目录
    """
    if not dir_path.exists():
        print(f"  ⚠️ 目录不存在: {dir_path.relative_to(BASE_DIR)}")
        return False
    
    relative_path = dir_path.relative_to(BASE_DIR)
    
    if is_dry_run:
        print(f"  🔍 [DRY-RUN] 将删除目录: {relative_path}")
    else:
        shutil.rmtree(dir_path)
        print(f"  🗑️ 已删除目录: {relative_path}")
    return True


def remove_company_info_model(file_path: Path, backup_dir: Path, is_dry_run: bool = True):
    """
    从documents/models.py中移除CompanyInfo模型
    """
    if not file_path.exists():
        print(f"  ⚠️ 文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'class CompanyInfo' not in content:
        print(f"  ℹ️ CompanyInfo模型已不存在")
        return True
    
    lines = content.split('\n')
    new_lines = []
    skip = False
    indent_level = 0
    
    for i, line in enumerate(lines):
        if 'class CompanyInfo(models.Model):' in line:
            skip = True
            indent_level = len(line) - len(line.lstrip())
            print(f"  🔍 找到CompanyInfo模型定义在第 {i+1} 行")
            continue
        
        if skip:
            current_indent = len(line) - len(line.lstrip()) if line.strip() else indent_level + 1
            if line.strip() and current_indent <= indent_level and not line.strip().startswith('#'):
                skip = False
                new_lines.append(line)
            continue
        
        new_lines.append(line)
    
    new_content = '\n'.join(new_lines)
    
    if is_dry_run:
        print(f"  🔍 [DRY-RUN] 将从 {file_path.name} 中移除 CompanyInfo 模型")
    else:
        backup_file(file_path, backup_dir)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  ✂️ 已从 {file_path.name} 中移除 CompanyInfo 模型")
    
    return True


def main():
    parser = argparse.ArgumentParser(description='清理废弃文件')
    parser.add_argument('--dry-run', action='store_true', help='仅显示将要删除的文件')
    parser.add_argument('--no-backup', action='store_true', help='不创建备份')
    args = parser.parse_args()
    
    print("=" * 60)
    print("🗑️ 废弃文件清理脚本")
    print("=" * 60)
    
    if args.dry_run:
        print("\n⚠️ DRY-RUN 模式 - 不会实际删除文件\n")
    
    backup_dir = None
    if not args.no_backup and not args.dry_run:
        backup_dir = create_backup()
    
    print("\n📋 处理废弃文件:")
    print("-" * 40)
    
    for file_item in DEPRECATED_FILES:
        if '::' in file_item:
            file_path, class_name = file_item.split('::')
            file_path = BASE_DIR / file_path
            if class_name == 'CompanyInfo':
                remove_company_info_model(file_path, backup_dir, args.dry_run)
        else:
            file_path = BASE_DIR / file_item
            if not args.dry_run and backup_dir:
                backup_file(file_path, backup_dir)
            delete_file(file_path, args.dry_run)
    
    print("\n📋 处理废弃目录:")
    print("-" * 40)
    
    for dir_item in DEPRECATED_DIRS:
        dir_path = BASE_DIR / dir_item
        if not args.dry_run and backup_dir:
            for f in dir_path.rglob('*'):
                if f.is_file():
                    backup_file(f, backup_dir)
        delete_dir(dir_path, args.dry_run)
    
    print("\n📋 未使用的API模块 (可选删除):")
    print("-" * 40)
    print("  ⚠️ 以下模块前端未调用，但可能用于未来功能:")
    for module in UNUSED_API_MODULES:
        print(f"  - {module}/")
    print("  如需删除，请手动执行或在脚本中启用")
    
    print("\n" + "=" * 60)
    if args.dry_run:
        print("✅ DRY-RUN 完成 - 未实际删除任何文件")
        print("   移除 --dry-run 参数以执行实际删除")
    else:
        print("✅ 清理完成!")
        if backup_dir:
            print(f"   备份位置: {backup_dir}")
    print("=" * 60)
    
    print("\n📝 后续步骤:")
    print("   1. 运行 python manage.py makemigrations")
    print("   2. 运行 python manage.py migrate")
    print("   3. 检查应用是否正常运行")
    print("   4. 提交代码更改")


if __name__ == '__main__':
    main()
