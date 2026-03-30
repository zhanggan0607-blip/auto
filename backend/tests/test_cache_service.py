"""
缓存服务单元测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import override_settings

from utils.cache_service import (
    CacheService,
    DistributedLock,
    cache_result,
    CacheKeys,
)


class TestCacheService:
    """
    缓存服务测试
    """
    
    @pytest.fixture
    def cache_service(self):
        """
        创建缓存服务实例
        """
        return CacheService()
    
    @patch('utils.cache_service.cache')
    def test_get(self, mock_cache, cache_service):
        """
        测试获取缓存
        """
        mock_cache.get.return_value = 'test_value'
        
        result = cache_service.get('test_key')
        
        assert result == 'test_value'
        mock_cache.get.assert_called_once()
    
    @patch('utils.cache_service.cache')
    def test_set(self, mock_cache, cache_service):
        """
        测试设置缓存
        """
        cache_service.set('test_key', 'test_value', timeout=60)
        
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        assert 'test_key' in call_args[0][0]
        assert call_args[0][1] == 'test_value'
    
    @patch('utils.cache_service.cache')
    def test_delete(self, mock_cache, cache_service):
        """
        测试删除缓存
        """
        cache_service.delete('test_key')
        
        mock_cache.delete.assert_called_once()
    
    @patch('utils.cache_service.cache')
    def test_exists(self, mock_cache, cache_service):
        """
        测试检查缓存是否存在
        """
        mock_cache.get.return_value = 'value'
        
        result = cache_service.exists('test_key')
        
        assert result is True
    
    @patch('utils.cache_service.cache')
    def test_get_or_set_existing(self, mock_cache, cache_service):
        """
        测试获取或设置缓存（已存在）
        """
        mock_cache.get.return_value = 'existing_value'
        
        result = cache_service.get_or_set('test_key', 'new_value')
        
        assert result == 'existing_value'
        mock_cache.set.assert_not_called()
    
    @patch('utils.cache_service.cache')
    def test_get_or_set_not_existing(self, mock_cache, cache_service):
        """
        测试获取或设置缓存（不存在）
        """
        mock_cache.get.return_value = None
        
        result = cache_service.get_or_set('test_key', 'new_value')
        
        assert result == 'new_value'
        mock_cache.set.assert_called_once()
    
    @patch('utils.cache_service.cache')
    def test_get_or_set_with_callable(self, mock_cache, cache_service):
        """
        测试获取或设置缓存（使用callable）
        """
        mock_cache.get.return_value = None
        
        def compute_value():
            return 'computed_value'
        
        result = cache_service.get_or_set('test_key', compute_value)
        
        assert result == 'computed_value'


class TestDistributedLock:
    """
    分布式锁测试
    """
    
    @patch('utils.cache_service.cache')
    def test_acquire_success(self, mock_cache):
        """
        测试成功获取锁
        """
        mock_cache.add.return_value = True
        
        lock = DistributedLock('test_lock')
        result = lock.acquire(blocking=False)
        
        assert result is True
        assert lock.locked() is True
    
    @patch('utils.cache_service.cache')
    def test_acquire_fail(self, mock_cache):
        """
        测试获取锁失败
        """
        mock_cache.add.return_value = False
        
        lock = DistributedLock('test_lock')
        result = lock.acquire(blocking=False)
        
        assert result is False
        assert lock.locked() is False
    
    @patch('utils.cache_service.cache')
    def test_release(self, mock_cache):
        """
        测试释放锁
        """
        mock_cache.add.return_value = True
        
        lock = DistributedLock('test_lock')
        lock.acquire(blocking=False)
        lock.release()
        
        mock_cache.delete.assert_called_once()
        assert lock.locked() is False
    
    @patch('utils.cache_service.cache')
    def test_context_manager(self, mock_cache):
        """
        测试上下文管理器
        """
        mock_cache.add.return_value = True
        
        with DistributedLock('test_lock') as lock:
            assert lock.locked() is True
        
        mock_cache.delete.assert_called_once()


class TestCacheResult:
    """
    缓存结果装饰器测试
    """
    
    @patch('utils.cache_service.cache')
    def test_cache_miss(self, mock_cache):
        """
        测试缓存未命中
        """
        mock_cache.get.return_value = None
        
        @cache_result('test:{arg}', timeout=60)
        def test_func(arg):
            return f'result_{arg}'
        
        result = test_func('value')
        
        assert result == 'result_value'
        mock_cache.set.assert_called_once()
    
    @patch('utils.cache_service.cache')
    def test_cache_hit(self, mock_cache):
        """
        测试缓存命中
        """
        mock_cache.get.return_value = 'cached_result'
        
        @cache_result('test:{arg}', timeout=60)
        def test_func(arg):
            return f'result_{arg}'
        
        result = test_func('value')
        
        assert result == 'cached_result'
        mock_cache.set.assert_not_called()


class TestCacheKeys:
    """
    缓存键常量测试
    """
    
    def test_enterprise_detail_key(self):
        """
        测试企业详情缓存键
        """
        key = CacheKeys.ENTERPRISE_DETAIL.format(id=123)
        assert key == 'enterprise:detail:123'
    
    def test_tender_detail_key(self):
        """
        测试招标详情缓存键
        """
        key = CacheKeys.TENDER_DETAIL.format(id=456)
        assert key == 'tender:detail:456'
    
    def test_user_permissions_key(self):
        """
        测试用户权限缓存键
        """
        key = CacheKeys.USER_PERMISSIONS.format(user_id=1)
        assert key == 'user:permissions:1'
