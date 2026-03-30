"""
OPENCLAW采集任务测试脚本 (最终版)
测试采集功能 - 不使用关键词过滤
"""
import os
import sys
import django
import asyncio
import logging

sys.path.insert(0, r'd:\共享文件\AUTO\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
os.environ.setdefault('DB_PASSWORD', '123456')

django.setup()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_tender_collector_no_keywords():
    """测试政府采购信息采集 - 不使用关键词过滤"""
    from openclaw.skill_registry import skill_registry

    logger.info("=" * 60)
    logger.info("测试 OPENCLAW 政府采购信息采集 (无关键词过滤)")
    logger.info("=" * 60)

    try:
        result = await skill_registry.execute_skill(
            'government_tender_collector',
            source='china_gov',
            notice_types=['gkzb'],
            page=1,
            page_size=5
        )

        logger.info(f"\n执行结果:")
        logger.info(f"  成功: {result.success}")
        logger.info(f"  数据条数: {len(result.data) if result.data else 0}")
        logger.info(f"  执行时间: {result.execution_time:.2f}秒")

        if result.error:
            logger.error(f"  错误: {result.error}")

        if result.data:
            logger.info(f"\n采集到的公告:")
            for i, item in enumerate(result.data[:5], 1):
                logger.info(f"  {i}. {item.get('title', 'N/A')[:60]}")
                logger.info(f"     日期: {item.get('publish_date', 'N/A')}")
                logger.info(f"     地域: {item.get('region', 'N/A')}")
                logger.info(f"     采购人: {item.get('purchaser_name', 'N/A')}")

        return result

    except Exception as e:
        logger.error(f"采集任务执行失败: {str(e)}", exc_info=True)
        return None


async def test_tender_with_keywords():
    """测试政府采购信息采集 - 使用实际存在的关键词"""
    from openclaw.skill_registry import skill_registry

    logger.info("\n" + "=" * 60)
    logger.info("测试 OPENCLAW 政府采购信息采集 (使用实际关键词)")
    logger.info("=" * 60)

    try:
        result = await skill_registry.execute_skill(
            'government_tender_collector',
            source='china_gov',
            keywords=['系统', '设备', '采购'],
            notice_types=['gkzb'],
            page=1,
            page_size=5
        )

        logger.info(f"\n执行结果:")
        logger.info(f"  成功: {result.success}")
        logger.info(f"  数据条数: {len(result.data) if result.data else 0}")

        if result.data:
            for i, item in enumerate(result.data[:3], 1):
                logger.info(f"  {i}. {item.get('title', 'N/A')[:50]}...")

        return result

    except Exception as e:
        logger.error(f"采集失败: {str(e)}", exc_info=True)
        return None


async def main():
    """主函数"""
    logger.info("\n" + "#" * 60)
    logger.info("# OPENCLAW 采集功能最终测试")
    logger.info("#" * 60)

    await test_tender_collector_no_keywords()
    await test_tender_with_keywords()

    logger.info("\n" + "#" * 60)
    logger.info("# 测试完成")
    logger.info("#" * 60)


if __name__ == '__main__':
    asyncio.run(main())
