"""
阿里云OCR服务
"""
import logging
from typing import Dict, Any, Optional
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ocr_api20210707 import models as ocr_models
from alibabacloud_ocr_api20210707.client import Client
from alibabacloud_tea_util import models as util_models
from django.conf import settings

logger = logging.getLogger(__name__)


class AliyunOCRService:
    """
    阿里云OCR识别服务
    """
    def __init__(self):
        self.config = settings.ALIYUN_OCR_CONFIG
        self.client = self._create_client()

    def _create_client(self) -> Optional[Client]:
        """
        创建OCR客户端
        """
        try:
            config = open_api_models.Config(
                access_key_id=self.config.get('ACCESS_KEY_ID'),
                access_key_secret=self.config.get('ACCESS_KEY_SECRET'),
            )
            config.endpoint = self.config.get('ENDPOINT', 'ocr-api.cn-hangzhou.aliyuncs.com')
            return Client(config)
        except Exception as e:
            logger.error(f"创建阿里云OCR客户端失败: {str(e)}")
            return None

    def recognize_general(self, image_url: str = None, image_content: bytes = None) -> Dict[str, Any]:
        """
        通用文字识别
        """
        if not self.client:
            return {'success': False, 'error': 'OCR客户端未初始化'}

        try:
            request = ocr_models.RecognizeGeneralRequest()
            
            if image_url:
                request.url = image_url
            elif image_content:
                import base64
                request.body = image_content
            
            runtime = util_models.RuntimeOptions()
            response = self.client.recognize_general_with_options(request, runtime)
            
            if response.status_code == 200:
                result = response.body
                return {
                    'success': True,
                    'content': result.data.content if hasattr(result.data, 'content') else '',
                    'blocks': self._parse_blocks(result.data) if hasattr(result.data, 'prism_wordsInfo') else []
                }
            else:
                return {
                    'success': False,
                    'error': f'识别失败: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"通用文字识别失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def recognize_id_card(self, image_url: str = None, image_content: bytes = None, side: str = 'face') -> Dict[str, Any]:
        """
        身份证识别
        """
        if not self.client:
            return {'success': False, 'error': 'OCR客户端未初始化'}

        try:
            request = ocr_models.RecognizeIdcardRequest()
            
            if image_url:
                request.url = image_url
            elif image_content:
                request.body = image_content
            
            runtime = util_models.RuntimeOptions()
            response = self.client.recognize_idcard_with_options(request, runtime)
            
            if response.status_code == 200:
                result = response.body
                card_data = result.data if hasattr(result, 'data') else {}
                
                return {
                    'success': True,
                    'name': card_data.get('name', ''),
                    'gender': card_data.get('sex', ''),
                    'nationality': card_data.get('nationality', ''),
                    'birth_date': card_data.get('birthDate', ''),
                    'address': card_data.get('address', ''),
                    'id_number': card_data.get('idNumber', ''),
                    'side': side
                }
            else:
                return {
                    'success': False,
                    'error': f'识别失败: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"身份证识别失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def recognize_business_license(self, image_url: str = None, image_content: bytes = None) -> Dict[str, Any]:
        """
        营业执照识别
        """
        if not self.client:
            return {'success': False, 'error': 'OCR客户端未初始化'}

        try:
            request = ocr_models.RecognizeBusinessLicenseRequest()
            
            if image_url:
                request.url = image_url
            elif image_content:
                request.body = image_content
            
            runtime = util_models.RuntimeOptions()
            response = self.client.recognize_business_license_with_options(request, runtime)
            
            if response.status_code == 200:
                result = response.body
                license_data = result.data if hasattr(result, 'data') else {}
                
                return {
                    'success': True,
                    'company_name': license_data.get('name', ''),
                    'credit_code': license_data.get('regNum', ''),
                    'legal_person': license_data.get('person', ''),
                    'registered_capital': license_data.get('capital', ''),
                    'establish_date': license_data.get('establishDate', ''),
                    'business_term': license_data.get('business', ''),
                    'address': license_data.get('address', ''),
                    'business_scope': license_data.get('businessScope', ''),
                }
            else:
                return {
                    'success': False,
                    'error': f'识别失败: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"营业执照识别失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def recognize_bank_card(self, image_url: str = None, image_content: bytes = None) -> Dict[str, Any]:
        """
        银行卡识别
        """
        if not self.client:
            return {'success': False, 'error': 'OCR客户端未初始化'}

        try:
            request = ocr_models.RecognizeBankCardRequest()
            
            if image_url:
                request.url = image_url
            elif image_content:
                request.body = image_content
            
            runtime = util_models.RuntimeOptions()
            response = self.client.recognize_bank_card_with_options(request, runtime)
            
            if response.status_code == 200:
                result = response.body
                card_data = result.data if hasattr(result, 'data') else {}
                
                return {
                    'success': True,
                    'card_number': card_data.get('cardNumber', ''),
                    'bank_name': card_data.get('bankName', ''),
                    'card_type': card_data.get('cardType', ''),
                    'valid_date': card_data.get('validDate', ''),
                }
            else:
                return {
                    'success': False,
                    'error': f'识别失败: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"银行卡识别失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def recognize_captcha(self, image_url: str = None, image_content: bytes = None) -> Dict[str, Any]:
        """
        验证码识别
        """
        result = self.recognize_general(image_url, image_content)
        
        if result.get('success'):
            content = result.get('content', '').strip()
            content = ''.join(filter(str.isalnum, content))
            result['captcha'] = content
        
        return result

    def _parse_blocks(self, data) -> list:
        """
        解析文字块
        """
        blocks = []
        if hasattr(data, 'prism_wordsInfo'):
            for item in data.prism_wordsInfo:
                blocks.append({
                    'word': item.word if hasattr(item, 'word') else '',
                    'position': item.pos if hasattr(item, 'pos') else []
                })
        return blocks
