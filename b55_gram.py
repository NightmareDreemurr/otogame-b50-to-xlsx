import json
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import os
from concurrent.futures import ThreadPoolExecutor
import math

def calculate_constant(score, rating):
        rating = rating / 100  # 将rating转换为小数形式
        
        if score >= 1007500:
            constant = rating - 2.00
        elif score >= 1000000:
            # 线性内插: 1000000->+1.50, 1007500->+2.00
            position = (score - 1000000) / 7500
            bonus = 1.50 + position * 0.50
            constant = rating - bonus
        elif score >= 990000:
            # 线性内插: 990000->+1.00, 1000000->+1.50
            position = (score - 990000) / 10000
            bonus = 1.00 + position * 0.50
            constant = rating - bonus
        elif score >= 970000:
            # 线性内插: 970000->+0.00, 990000->+1.00
            position = (score - 970000) / 20000
            bonus = position
            constant = rating - bonus
        elif score >= 900000:
            # 线性内插: 900000->-4.00, 970000->+0.00
            position = (score - 900000) / 70000
            bonus = -4.00 + position * 4.00
            constant = rating - bonus
        elif score >= 800000:
            # 线性内插: 800000->-6.00, 900000->-4.00
            position = (score - 800000) / 100000
            bonus = -6.00 + position * 2.00
            constant = rating - bonus
        else:
            constant = rating  # 500000-800000区间为0加成

        # 将定数四舍五入到最近的0.1
        return round(constant * 10) / 10

class B55GramGenerator:
    def __init__(self):
        self.cell_width = 200
        self.cell_height = 100
        self.grid_width = 5  # 每行5首歌
        self.section_padding = 30  # 区段之间的padding
        self.font_size = 14
        self.title_font_size = 24
        self.profile_height = 120  # 头部玩家信息的高度
        
        # 创建缓存目录
        if not os.path.exists('cache'):
            os.makedirs('cache')
            
        # 创建assets目录和assets/cover子目录
        if not os.path.exists('assets'):
            os.makedirs('assets')
        if not os.path.exists('assets/cover'):
            os.makedirs('assets/cover')
            
        # 下载难度指示器图片
        self.difficulty_images = self.download_difficulty_images()
            
        # 尝试加载中日文字体
        try:
            # Windows 系统默认中日文字体
            if os.name == 'nt':
                self.font = ImageFont.truetype("C:\\Windows\\Fonts\\msyh.ttc", self.font_size)  # 微软雅黑
                self.title_font = ImageFont.truetype("C:\\Windows\\Fonts\\msyh.ttc", self.title_font_size)
                self.profile_font = ImageFont.truetype("C:\\Windows\\Fonts\\msyh.ttc", 20)  # 用于玩家信息
                self.rating_font = ImageFont.truetype("C:\\Windows\\Fonts\\msyh.ttc", 36)  # 用于Rating数值
            # macOS 系统默认中日文字体
            elif os.name == 'posix':
                self.font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", self.font_size)
                self.title_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", self.title_font_size)
                self.profile_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 20)
                self.rating_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 36)
            # Linux 系统默认中日文字体
            else:
                self.font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", self.font_size)
                self.title_font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", self.title_font_size)
                self.profile_font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 20)
                self.rating_font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 36)
        except Exception as e:
            print(f"Warning: Failed to load CJK font: {e}")
            print("Falling back to default font...")
            self.font = ImageFont.load_default()
            self.title_font = ImageFont.load_default()
            self.profile_font = ImageFont.load_default()
            self.rating_font = ImageFont.load_default()
        
        # 下载并缓存默认封面
        self.fallback_jacket = self.download_fallback_jacket()
        
    def calculate_constant(score, rating):
        rating = rating / 100  # 将rating转换为小数形式
        
        if score >= 1007500:
            constant = rating - 2.00
        elif score >= 1000000:
            # 线性内插: 1000000->+1.50, 1007500->+2.00
            position = (score - 1000000) / 7500
            bonus = 1.50 + position * 0.50
            constant = rating - bonus
        elif score >= 990000:
            # 线性内插: 990000->+1.00, 1000000->+1.50
            position = (score - 990000) / 10000
            bonus = 1.00 + position * 0.50
            constant = rating - bonus
        elif score >= 970000:
            # 线性内插: 970000->+0.00, 990000->+1.00
            position = (score - 970000) / 20000
            bonus = position
            constant = rating - bonus
        elif score >= 900000:
            # 线性内插: 900000->-4.00, 970000->+0.00
            position = (score - 900000) / 70000
            bonus = -4.00 + position * 4.00
            constant = rating - bonus
        elif score >= 800000:
            # 线性内插: 800000->-6.00, 900000->-4.00
            position = (score - 800000) / 100000
            bonus = -6.00 + position * 2.00
            constant = rating - bonus
        else:
            constant = rating  # 500000-800000区间为0加成

        # 将定数四舍五入到最近的0.1
        return round(constant * 10) / 10

    def download_difficulty_images(self):
        """下载所有难度指示器图片"""
        difficulty_types = ["basic", "advanced", "expert", "master", "lunatic"]
        difficulty_images = {}
        
        for diff_type in difficulty_types:
            image_path = f'assets/diff_{diff_type}.png'
            
            # 如果已经存在，直接加载
            if os.path.exists(image_path):
                difficulty_images[diff_type] = Image.open(image_path)
                continue
                
            # 下载图片
            url = f"https://u.otogame.net/img/ongeki/diff_{diff_type}.png"
            try:
                response = requests.get(url)
                response.raise_for_status()
                img = Image.open(io.BytesIO(response.content))
                # 保存到assets目录
                img.save(image_path)
                difficulty_images[diff_type] = img
                print(f"Downloaded and saved {diff_type} difficulty image")
            except Exception as e:
                print(f"Error downloading {diff_type} difficulty image: {e}")
                # 创建一个空白图片作为备用
                difficulty_images[diff_type] = Image.new('RGBA', (116, 15), (0, 0, 0, 0))
                
        return difficulty_images

    def download_fallback_jacket(self):
        """下载默认封面图片"""
        cache_path = 'cache/fallback.webp'
        assets_path = 'assets/cover/fallback.webp'
        
        # 首先检查assets目录
        if os.path.exists(assets_path):
            return Image.open(assets_path)
            
        # 然后检查缓存目录
        if os.path.exists(cache_path):
            img = Image.open(cache_path)
            # 保存到assets目录
            img.save(assets_path)
            return img
            
        url = "https://u.otogame.net/img/ongeki/musicjacket_fallback.webp"
        headers = {
            "Referer": "https://u.otogame.net/",
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
            # 保存到两个位置
            img.save(cache_path)
            img.save(assets_path)
            return img
        except Exception as e:
            print(f"Error downloading fallback jacket: {e}")
            # 创建一个纯黑色的图片作为最后的备选
            return Image.new('RGB', (self.cell_width, self.cell_height), (0, 0, 0))
        
    def download_jacket(self, music_id):
        """下载歌曲封面"""
        cache_path = f'cache/{music_id}.webp'
        assets_path = f'assets/cover/{music_id}.webp'
        
        # 首先检查assets目录
        if os.path.exists(assets_path):
            return Image.open(assets_path)
            
        # 然后检查缓存目录
        if os.path.exists(cache_path):
            img = Image.open(cache_path)
            # 保存到assets目录
            img.save(assets_path)
            return img
            
        url = f"https://oss.bemanicn.com/SDDT/cover/{music_id}.webp-thumbnail"
        headers = {
            "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "Referer": "https://u.otogame.net/",
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
            # 保存到两个位置
            img.save(cache_path)
            img.save(assets_path)
            return img
        except Exception as e:
            print(f"Warning: Using fallback jacket for {music_id}: {e}")
            return self.fallback_jacket

    def get_difficulty_color(self, difficulty):
        """获取难度对应的颜色"""
        colors = {
            0: "#41a147",  # Basic - 绿色
            1: "#f5c421",  # Advanced - 黄色
            2: "#f54521",  # Expert - 红色
            3: "#9021f5",  # Master - 紫色
            10: "#ffffff", # Lunatic - 白色
        }
        return colors.get(difficulty, "#888888")
        
    def get_difficulty_image(self, difficulty):
        """获取难度对应的图片"""
        difficulty_map = {
            0: "basic",
            1: "advanced",
            2: "expert",
            3: "master",
            10: "lunatic"
        }
        diff_name = difficulty_map.get(difficulty, "master")
        return self.difficulty_images.get(diff_name)

    def draw_song_cell(self, draw, x, y, song_data):
        """绘制单个歌曲格子"""
        # 下载并绘制封面
        jacket = self.download_jacket(song_data['music']['music_id'])
        if jacket:
            # 使用fill而不是stretch来调整图片大小
            # 首先创建一个空白画布
            jacket_canvas = Image.new('RGB', (self.cell_width, self.cell_height))
            
            # 计算缩放比例，确保覆盖整个单元格
            aspect_ratio = jacket.width / jacket.height
            target_ratio = self.cell_width / self.cell_height
            
            if aspect_ratio > target_ratio:
                # 图片比单元格更宽，基于高度调整
                new_height = self.cell_height
                new_width = int(new_height * aspect_ratio)
                resized_jacket = jacket.resize((new_width, new_height))
                
                # 计算居中位置
                left_offset = (new_width - self.cell_width) // 2
                jacket_canvas.paste(resized_jacket, (-left_offset, 0))
            else:
                # 图片比单元格更高，基于宽度调整
                new_width = self.cell_width
                new_height = int(new_width / aspect_ratio)
                resized_jacket = jacket.resize((new_width, new_height))
                
                # 计算居中位置
                top_offset = (new_height - self.cell_height) // 2
                jacket_canvas.paste(resized_jacket, (0, -top_offset))
                
            # 应用高斯模糊
            jacket_canvas = jacket_canvas.filter(ImageFilter.GaussianBlur(4))
            
            # 粘贴到主图像
            self.base_image.paste(jacket_canvas, (x, y))
            
        # 绘制半透明遮罩
        overlay = Image.new('RGBA', (self.cell_width, self.cell_height), (0, 0, 0, 128))
        self.base_image.paste(overlay, (x, y), overlay)
        # 绘制难度颜色条 - 放在左侧
        diff_color = self.get_difficulty_color(song_data['difficulty'])
        draw.rectangle([x, y, x + 5, y + self.cell_height], fill=diff_color)
        
        # 绘制难度图标 - 放在左上角
        diff_image = self.get_difficulty_image(song_data['difficulty'])
        if diff_image:
            diff_pos_x = x + 16  # 放在左上角，与颜色条有一点距离
            diff_pos_y = y + 5
            self.base_image.paste(diff_image, (diff_pos_x, diff_pos_y), diff_image if diff_image.mode == 'RGBA' else None)
        
        # 绘制文字信息 - 将所有文本下移，避免与难度指示器冲突
        text_x = x + 16
        text_y = y + 25  # 从25开始而不是5，给难度图标留出空间
        
        # 歌曲名称（限制长度并添加省略号）
        name = song_data['music']['name']
        max_chars = 20  # 最大字符数
        if len(name) > max_chars:
            name = name[:max_chars-2] + "..."
            
        draw.text((text_x, text_y), name, 
                 font=self.font, fill="white")
        
        # 分数和等级
        score = song_data['score']
        rating = song_data['rating'] / 100
        base = calculate_constant(song_data['score'], song_data['rating'])

        score_text = f"{score}"
        rating_text = f"Base: {base} -> {rating}"
        
        draw.text((text_x, text_y + 20), score_text, 
                 font=self.font, fill="white")
        draw.text((text_x, text_y + 40), rating_text, 
                 font=self.font, fill="white")

    def draw_section_title(self, draw, x, y, title, rating=None):
        """绘制区段标题"""
        draw.text((x, y - 17), title, font=self.title_font, fill="white")
        if rating is not None:
            rating_text = f"Rating: {rating:.2f}"
            # 计算标题宽度以便将rating放在右侧
            title_width = self.title_font.getsize(title)[0] if hasattr(self.title_font, 'getsize') else self.title_font.getbbox(title)[2]
            draw.text((x + title_width + 600, y-5), rating_text, font=self.font, fill="white")

    def draw_player_profile(self, draw, player_data):
        """绘制玩家个人信息"""
        # 加载用户头像
        avatar_path = player_data['data'].get('avatar_path')
        profile_bg_color = (255, 240, 100)  # 黄色背景
        
        # 绘制背景
        draw.rectangle([0, 0, self.cell_width * self.grid_width, self.profile_height], fill=profile_bg_color)
        
        # 尝试加载头像，如果失败则创建默认头像
        avatar = None
        if avatar_path and os.path.exists(avatar_path):
            try:
                avatar = Image.open(avatar_path)
            except Exception as e:
                print(f"Error loading avatar: {e}")
        
        if avatar is None:
            # 尝试加载默认头像，如果存在的话
            default_avatar_path = 'assets/default_avatar.webp'
            if os.path.exists(default_avatar_path):
                try:
                    avatar = Image.open(default_avatar_path)
                except Exception as e:
                    print(f"Error loading default avatar: {e}")
            
            # 如果仍然没有头像，则创建一个简单的默认头像
            if avatar is None:
                # 创建默认头像
                avatar = Image.new('RGB', (100, 100), (200, 200, 200))
                draw_avatar = ImageDraw.Draw(avatar)
                draw_avatar.ellipse((10, 10, 90, 90), fill=(150, 150, 150))
        
        # 调整头像大小为100x100并粘贴到图像上
        avatar = avatar.resize((100, 100))
        self.base_image.paste(avatar, (20, 10))
        
        # 绘制玩家名称
        user_name = player_data['data'].get('user_name', '未知玩家')
        level = player_data['data'].get('level', '??')
        draw.text((140, 25), f"Lv.{level}", font=self.profile_font, fill=(50, 50, 50))
        draw.text((140, 50), user_name, font=self.profile_font, fill=(50, 50, 50))
        
        # 绘制Rating
        player_rating = player_data['data'].get('player_rating', 0) / 100 if 'player_rating' in player_data['data'] else 0
        draw.text((500, 40), f"RATING", font=self.profile_font, fill=(50, 50, 50))
        draw.text((500, 65), f"{player_rating:.2f}", font=self.rating_font, fill=(200, 50, 50))

    def generate(self, json_data, player_data=None):
        """生成B55表格图像"""
        # 获取各个部分的数据
        best_scores = json_data['data']['best_rating_list']
        new_scores = json_data['data']['best_new_rating_list']
        recent_scores = json_data['data']['hot_rating_list']
        
        # 按rating值排序
        best_scores = sorted([s for s in best_scores if s['rating'] > 0], key=lambda x: x['rating'], reverse=True)
        new_scores = sorted([s for s in new_scores if s['rating'] > 0], key=lambda x: x['rating'], reverse=True)
        recent_scores = sorted([s for s in recent_scores if s['rating'] > 0], key=lambda x: x['rating'], reverse=True)
        
        # 计算每个部分最多显示多少歌曲（确保总共最多显示55首）
        max_best = min(30, len(best_scores))  # 最佳最多30首
        max_new = min(15, len(new_scores))    # 新曲最多15首
        max_recent = min(10, len(recent_scores))  # 最近最多10首
        
        # 计算每个部分需要的行数
        best_rows = math.ceil(max_best / self.grid_width)
        new_rows = math.ceil(max_new / self.grid_width)
        recent_rows = math.ceil(max_recent / self.grid_width)
        
        # 计算图像总高度（包括玩家信息、每部分标题和间距）
        total_height = (
            self.profile_height +  # 顶部玩家信息
            self.section_padding +  # 顶部留空
            self.title_font_size + 10 +  # "最佳"标题和间距
            best_rows * self.cell_height +
            self.section_padding +  # "最佳"与"新曲"之间的间距
            self.title_font_size + 10 +  # "新曲"标题和间距
            new_rows * self.cell_height +
            self.section_padding +  # "新曲"与"最近"之间的间距
            self.title_font_size + 10 +  # "最近"标题和间距
            recent_rows * self.cell_height +
            self.section_padding  # 底部留空
        )
        
        # 创建基础图像
        width = self.cell_width * self.grid_width
        self.base_image = Image.new('RGB', (width, total_height), (32, 32, 32))
        draw = ImageDraw.Draw(self.base_image)
        
        # 绘制玩家信息
        if player_data:
            self.draw_player_profile(draw, player_data)
            # 更新y偏移量，从玩家信息下方开始绘制歌曲
            y_offset_start = self.profile_height
        else:
            y_offset_start = 0
        
        # 获取rating值
        best_rating = json_data['data']['best_rating'] / 100
        new_rating = json_data['data']['best_new_rating'] / 100
        recent_rating = json_data['data']['hot_rating'] / 100
        
        # 绘制"最佳"部分
        y_offset = y_offset_start + self.section_padding
        self.draw_section_title(draw, 10, y_offset, "RATING对象曲（最佳）", best_rating)
        y_offset += self.title_font_size + 10
        
        for i, song_data in enumerate(best_scores[:max_best]):
            x = (i % self.grid_width) * self.cell_width
            y = y_offset + (i // self.grid_width) * self.cell_height
            self.draw_song_cell(draw, x, y, song_data)
        
        # 绘制"新曲"部分
        y_offset += best_rows * self.cell_height + self.section_padding
        self.draw_section_title(draw, 10, y_offset, "RATING对象曲（新曲）", new_rating)
        y_offset += self.title_font_size + 10
        
        for i, song_data in enumerate(new_scores[:max_new]):
            x = (i % self.grid_width) * self.cell_width
            y = y_offset + (i // self.grid_width) * self.cell_height
            self.draw_song_cell(draw, x, y, song_data)
        
        # 绘制"最近"部分
        y_offset += new_rows * self.cell_height + self.section_padding
        self.draw_section_title(draw, 10, y_offset, "RATING对象曲（最近）", recent_rating)
        y_offset += self.title_font_size + 10
        
        for i, song_data in enumerate(recent_scores[:max_recent]):
            x = (i % self.grid_width) * self.cell_width
            y = y_offset + (i // self.grid_width) * self.cell_height
            self.draw_song_cell(draw, x, y, song_data)
        
        # 在图片底部添加总Rating
        total_rating = json_data['data']['rating'] / 100
        y_offset += recent_rows * self.cell_height + 20
        draw.text((10, y_offset), f"总Rating: {total_rating:.2f}", font=self.font, fill="white")
        
        return self.base_image

def main():
    # 确保assets目录存在
    if not os.path.exists('assets'):
        os.makedirs('assets')
    
    # 创建默认头像如果不存在
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
    
    # 读取JSON文件 - 添加错误处理
    json_data = None
    try:
        with open('b50.json', 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except Exception as e:
        print(f"Error loading b50.json: {e}")
        print("Creating minimal json data structure")
        # 创建一个最小的JSON数据结构，以便程序能够继续
        json_data = {
            "data": {
                "rating": 0,
                "best_rating": 0,
                "best_new_rating": 0,
                "hot_rating": 0,
                "best_rating_list": [],
                "best_new_rating_list": [],
                "hot_rating_list": []
            }
        }
    
    # 读取玩家个人信息（如果存在）
    player_data = None
    if os.path.exists('player_profile.json'):
        try:
            with open('player_profile.json', 'r', encoding='utf-8') as f:
                player_data = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load player profile: {e}")
    
    # 生成图像
    generator = B55GramGenerator()
    image = generator.generate(json_data, player_data)
    
    # 保存图像
    image.save('b55_gram.png')
    print("B55-gram has been generated as 'b55_gram.png'")

if __name__ == "__main__":
    main() 