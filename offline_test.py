#!/usr/bin/env python3
"""
离线模式测试脚本 - 不需要连接到API，直接使用本地文件生成B55图表
"""

import os
import sys
from PIL import Image, ImageDraw

def ensure_assets_dir():
    """确保assets目录存在"""
    if not os.path.exists('assets'):
        os.makedirs('assets')
        print("Created assets directory")

def create_default_avatar():
    """创建默认头像"""
    default_avatar_path = 'assets/default_avatar.webp'
    if not os.path.exists(default_avatar_path):
        try:
            # 创建一个100x100的灰色头像
            img = Image.new('RGB', (100, 100), (200, 200, 200))
            draw = ImageDraw.Draw(img)
            # 画一个圆形
            draw.ellipse((10, 10, 90, 90), fill=(150, 150, 150))
            # 保存
            img.save(default_avatar_path)
            print(f"Created default avatar: {default_avatar_path}")
        except Exception as e:
            print(f"Error creating default avatar: {e}")

def main():
    """主函数"""
    print("开始离线测试...")
    
    # 准备资源
    ensure_assets_dir()
    create_default_avatar()
    
    # 直接调用B55图表生成功能
    from b55_gram import main as generate_b55
    generate_b55()
    
    print("测试完成！")

if __name__ == "__main__":
    main() 