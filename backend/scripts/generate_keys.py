"""
密钥生成工具

用于生成安全的密钥和密码
"""
import secrets
import string
import argparse


def generate_secret_key(length: int = 50) -> str:
    """
    生成Django SECRET_KEY
    
    Args:
        length: 密钥长度
        
    Returns:
        安全的随机密钥
    """
    chars = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(chars) for _ in range(length))


def generate_password(length: int = 24) -> str:
    """
    生成安全密码
    
    Args:
        length: 密码长度
        
    Returns:
        安全的随机密码
    """
    chars = string.ascii_letters + string.digits + '!@#$%^&*'
    password = ''.join(secrets.choice(chars) for _ in range(length))
    return password


def generate_api_key(length: int = 32) -> str:
    """
    生成API密钥
    
    Args:
        length: 密钥长度
        
    Returns:
        安全的API密钥
    """
    return secrets.token_hex(length)


def main():
    parser = argparse.ArgumentParser(description='生成安全密钥')
    parser.add_argument('--type', choices=['secret', 'password', 'api'], 
                        default='secret', help='密钥类型')
    parser.add_argument('--length', type=int, default=50, 
                        help='密钥长度')
    
    args = parser.parse_args()
    
    if args.type == 'secret':
        key = generate_secret_key(args.length)
        print(f"Django SECRET_KEY:\n{key}\n")
    elif args.type == 'password':
        key = generate_password(args.length)
        print(f"安全密码:\n{key}\n")
    elif args.type == 'api':
        key = generate_api_key(args.length // 2)
        print(f"API密钥:\n{key}\n")
    
    print("请妥善保管以上密钥，不要提交到版本控制系统！")


if __name__ == '__main__':
    main()
