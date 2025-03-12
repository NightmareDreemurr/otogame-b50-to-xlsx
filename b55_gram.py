import json
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import os
from concurrent.futures import ThreadPoolExecutor
import math
from threading import Lock
import queue
import time
from concurrent.futures import wait

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
        self.cell_width = 400  # 原200*2
        self.cell_height = 200  # 原100*2
        self.grid_width = 5  # 每行5首歌
        self.section_padding = 60  # 原30*2
        self.font_size = 28  # 原14*2
        self.title_font_size = 60  # 原30*2
        self.profile_height = 280  # 原130*2
        
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
        
        # 加载等级图标
        self.rank_images = self.load_rank_images()
            
        # 初始化线程池和缓存
        self.executor = ThreadPoolExecutor(max_workers=10)  # 最多10个并发下载线程
        self.image_cache = {}
        self.cache_lock = Lock()
        self.download_queue = queue.Queue()
        
        # 下载并缓存默认封面
        self.fallback_jacket = self.download_fallback_jacket()
        
        # 尝试加载中日文字体
        try:
            # Windows 系统默认中日文字体
            if os.name == 'nt':
                self.font = ImageFont.truetype("assets/fonts/combined.ttf", self.font_size)  # NP-R
                self.title_font = ImageFont.truetype("assets/fonts/combined.ttf", self.title_font_size)
                self.profile_font = ImageFont.truetype("assets/fonts/BIZ-UDGOTHICB.TTC", 40)  # 原20*2
                self.rating_font = ImageFont.truetype("assets/fonts/BIZ-UDGOTHICB.TTC", 72)  # 原36*2
            # macOS 系统默认中日文字体
            elif os.name == 'posix':
                self.font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", self.font_size)
                self.title_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", self.title_font_size)
                self.profile_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 40)
                self.rating_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 72)
            # Linux 系统默认中日文字体
            else:
                self.font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", self.font_size)
                self.title_font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", self.title_font_size)
                self.profile_font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 40)
                self.rating_font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 72)
        except Exception as e:
            print(f"Warning: Failed to load CJK font: {e}")
            print("Falling back to default font...")
            self.font = ImageFont.load_default()
            self.title_font = ImageFont.load_default()
            self.profile_font = ImageFont.load_default()
            self.rating_font = ImageFont.load_default()
        
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
        
    def _download_single_jacket(self, music_id, max_retries=2, timeout=5):
        """下载单个封面的内部方法"""
        cache_path = f'cache/{music_id}.webp'
        assets_path = f'assets/cover/{music_id}.webp'
        
        # 如果已经在缓存中，直接返回
        with self.cache_lock:
            if music_id in self.image_cache:
                return self.image_cache[music_id]
        
        # 如果文件已存在，加载并缓存
        if os.path.exists(assets_path):
            try:
                img = Image.open(assets_path)
                with self.cache_lock:
                    self.image_cache[music_id] = img
                return img
            except Exception as e:
                print(f"Warning: Failed to load existing cover {music_id}: {e}")
                # 如果加载失败，继续尝试下载
            
        url = f"https://oss.bemanicn.com/SDDT/cover/{music_id}.webp-thumbnail"
        headers = {
            "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "Referer": "https://u.otogame.net/",
        }
        
        for retry in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()
                img = Image.open(io.BytesIO(response.content))
                
                # 保存到缓存和assets目录
                try:
                    img.save(cache_path)
                    img.save(assets_path)
                except Exception as e:
                    print(f"Warning: Failed to save cover {music_id}: {e}")
                
                # 添加到内存缓存
                with self.cache_lock:
                    self.image_cache[music_id] = img
                return img
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    print(f"404 error downloading cover {music_id}, no retry")
                    return self.fallback_jacket
                else:
                    if retry < max_retries - 1:
                        print(f"HTTP error downloading cover {music_id}: {e}, retrying...")
                        continue
                    print(f"HTTP error downloading cover {music_id}: {e}, using fallback")
                    return self.fallback_jacket
                
            except requests.Timeout:
                if retry < max_retries - 1:
                    print(f"Timeout downloading cover {music_id}, retrying...")
                    continue
                print(f"Timeout downloading cover {music_id}, using fallback")
                return self.fallback_jacket
                
            except Exception as e:
                if retry < max_retries - 1:
                    print(f"Error downloading cover {music_id}: {e}, retrying...")
                    continue
                print(f"Failed to download cover {music_id}: {e}, using fallback")
                return self.fallback_jacket
        
        return self.fallback_jacket

    def preload_jackets(self, music_list):
        """预加载所有歌曲封面"""
        print("开始预加载封面...")
        start_time = time.time()
        
        # 收集所有需要下载的music_id
        music_ids = []
        for song in music_list:
            music_id = song['music']['music_id']
            # 如果封面已经在缓存或assets目录中，跳过
            if music_id in self.image_cache or os.path.exists(f'assets/cover/{music_id}.webp'):
                continue
            music_ids.append(music_id)
        
        if not music_ids:
            print("所有封面已缓存")
            return
            
        total = len(music_ids)
        completed = 0
        failed = 0
        
        def download_with_progress(music_id):
            nonlocal completed, failed
            try:
                self._download_single_jacket(music_id)
                with self.cache_lock:
                    completed += 1
                    if completed % 5 == 0 or completed + failed == total:
                        success_rate = (completed / (completed + failed)) * 100 if completed + failed > 0 else 0
                        print(f"下载进度: {completed + failed}/{total} (成功率: {success_rate:.1f}%)")
            except Exception as e:
                with self.cache_lock:
                    failed += 1
                print(f"下载失败 {music_id}: {e}")
        
        # 使用线程池并发下载
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for music_id in music_ids:
                future = executor.submit(download_with_progress, music_id)
                futures.append(future)
            
            # 等待所有下载完成，但设置总超时时间
            try:
                done, not_done = wait(futures, timeout=60)  # 设置60秒总超时
                if not_done:
                    print(f"警告: {len(not_done)}个封面下载超时")
                    for future in not_done:
                        future.cancel()
            except Exception as e:
                print(f"预加载过程出错: {e}")
        
        end_time = time.time()
        print(f"封面预加载完成，耗时: {end_time - start_time:.2f}秒")
        print(f"成功: {completed}, 失败: {failed}, 总计: {total}")

    def download_jacket(self, music_id):
        """下载歌曲封面的公共方法"""
        try:
            return self._download_single_jacket(music_id)
        except Exception as e:
            print(f"Error downloading jacket {music_id}: {e}")
            return self.fallback_jacket

    def get_difficulty_color(self, difficulty):
        """获取难度对应的颜色"""
        colors = {
            0: "#41a147",  # Basic - 绿色
            1: "#f5c421",  # Advanced - 黄色
            2: "#fe0d89",  # Expert - 红色
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

    def load_rank_images(self):
        """加载等级图标"""
        rank_images = {}
        rank_path = 'assets/ranks'
        
        # 等级对应关系
        rank_map = {
            1007500: 'sssplus',
            1000000: 'sss',
            990000: 'ss',
            970000: 's',
            940000: 'aaa',
            900000: 'aa',
            850000: 'a',
            800000: 'bbb',
            750000: 'bb',
            700000: 'b',
            500000: 'c',
            0: 'd'
        }
        
        # 加载所有等级图标
        for score, rank in rank_map.items():
            image_path = os.path.join(rank_path, f'score_tr_{rank}.png')
            try:
                if os.path.exists(image_path):
                    img = Image.open(image_path)
                    rank_images[score] = img
                else:
                    print(f"Warning: Rank image not found: {image_path}")
            except Exception as e:
                print(f"Error loading rank image {rank}: {e}")
        
        return rank_images
        
    def get_rank_image(self, score):
        """获取对应分数的等级图标"""
        thresholds = sorted(self.rank_images.keys(), reverse=True)
        for threshold in thresholds:
            if score >= threshold:
                return self.rank_images[threshold]
        return self.rank_images[0]  # 返回D等级图标作为默认值

    def draw_song_cell(self, draw, x, y, song_data):
        """绘制单个歌曲格子"""
        # 获取封面（不会重复下载，因为已经在preload阶段完成）
        music_id = song_data['music']['music_id']
        jacket = None
        
        # 首先检查内存缓存
        with self.cache_lock:
            jacket = self.image_cache.get(music_id)
            
        # 如果内存缓存中没有，检查文件系统
        if not jacket:
            assets_path = f'assets/cover/{music_id}.webp'
            if os.path.exists(assets_path):
                try:
                    jacket = Image.open(assets_path)
                    # 加入内存缓存
                    with self.cache_lock:
                        self.image_cache[music_id] = jacket
                except Exception as e:
                    print(f"Error loading cover from file for {music_id}: {e}")
                    jacket = self.fallback_jacket
            else:
                print(f"Warning: Cover for {music_id} not found in cache or filesystem, using fallback")
                jacket = self.fallback_jacket
                
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
        draw.rectangle([x, y, x + 10, y + self.cell_height], fill=diff_color)  # 原5*2
        
        # 绘制难度图标 - 放在左上角
        diff_image = self.get_difficulty_image(song_data['difficulty'])
        if diff_image:
            # 调整难度图标大小
            diff_size = (232, 30)  # 原(116, 15)*2
            diff_image = diff_image.resize(diff_size)
            diff_pos_x = x + 32  # 原16*2
            diff_pos_y = y + 20  # 原10*2
            self.base_image.paste(diff_image, (diff_pos_x, diff_pos_y), diff_image if diff_image.mode == 'RGBA' else None)
        
        # 绘制文字信息 - 将所有文本下移，避免与难度指示器冲突
        text_x = x + 32  # 原16*2
        text_y = y + 60  # 原30*2
        
        # 歌曲名称（限制长度并添加省略号）
        name = song_data['music']['name']
        max_chars = 20  # 最大字符数
        if len(name) > max_chars:
            name = name[:max_chars-2] + "..."
            
        draw.text((text_x, text_y+3), name, 
                 font=self.font, fill="white")
        
        # 分数和等级
        score = song_data['score']
        rating = song_data['rating'] / 100
        base = calculate_constant(song_data['score'], song_data['rating'])

        score_text = f"{score}"
        rating_text = f"Base: {base} -> {rating}"
        
        score_text = "{:,}".format(int(score_text))  # Add commas to separate every three digits
        draw.text((text_x, text_y + 30), score_text,  # 原16*2
                 font=ImageFont.truetype("assets/fonts/Torus-SemiBold.otf", 46), fill="white")  # 原23*2
        draw.text((text_x, text_y + 93), rating_text,  # 原45*2
                 font=ImageFont.truetype("assets/fonts/combined.ttf", 30), fill="white")  # 原15*2
                 
        # 绘制等级图标 - 放在右下角
        rank_image = self.get_rank_image(score)
        if rank_image:
            # 调整等级图标大小
            rank_size = (100, 50)  # 原(50, 25)*2
            rank_image = rank_image.resize(rank_size)
            rank_pos_x = x + self.cell_width - rank_size[0] - 14  # 原7*2
            rank_pos_y = y + self.cell_height - rank_size[1] - 54  # 原30*2
            self.base_image.paste(rank_image, (rank_pos_x, rank_pos_y), rank_image if rank_image.mode == 'RGBA' else None)
       

    def draw_section_title(self, draw, x, y, title, rating=None):
        """绘制区段标题"""
        draw.text((x, y - 34), title, font=self.title_font, fill="white")  # 原17*2
        if rating is not None:
            rating_text = f"{rating:.2f}"
            # 计算标题宽度以便将rating放在右侧
            title_width = self.title_font.getsize(title)[0] if hasattr(self.title_font, 'getsize') else self.title_font.getbbox(title)[2]
            # 从右往左对齐，空30pc
            rating_width = self.title_font.getsize(rating_text)[0] if hasattr(self.title_font, 'getsize') else self.title_font.getbbox(rating_text)[2]
            draw.text((x + 1800, y - 34), rating_text, font=self.title_font, fill="white")  # 原900*2, 17*2

    def get_rating_color(self, rating):
        """根据rating值返回对应的颜色"""
        if rating >= 15.00:
            return None  # 特殊处理彩虹色
        elif rating >= 14.50:
            return "#fffacd"  # 铂金色
        elif rating >= 14.00:
            return "#FFD100"  # 金色
        elif rating >= 13.00:
            return "#E3E3E3"  # 银色
        elif rating >= 12.00:
            return "#EF845C"  # 铜色
        elif rating >= 10.00:
            return "#C000C0"  # 紫色
        elif rating >= 7.00:
            return "#CC0000"  # 红色
        elif rating >= 4.00:
            return "#F58000"  # 橙色
        elif rating >= 2.00:
            return "#10C010"  # 绿色
        else:
            return "#30D0D0"  # 天蓝色

    

    def create_rainbow_text_v4(self, text, font, width, height):
        """使用更简单的方法创建彩虹渐变文字，带有黑色描边效果"""
        # 创建三个不同颜色的文字图层
        colors = [
            (247, 254, 18),    # 黄色 #f7fe12
            (0, 255, 255),     # 青色 #0ff
            (254, 112, 211)    # 粉色 #fe70d3
        ]
        
        # 创建基础文字图层
        text_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_layer)
        
        # 获取文字大小并计算居中位置
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # 创建描边层
        outline_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        outline_draw = ImageDraw.Draw(outline_layer)
        
        # 绘制描边（通过在四个方向各偏移1px来实现）
        offsets = [(0, 1), (0, -1), (1, 0), (-1, 0),  # 上下左右
                  (1, 1), (1, -1), (-1, 1), (-1, -1)]  # 对角线
        for offset_x, offset_y in offsets:
            outline_draw.text((x + offset_x, y + offset_y), text, font=font, fill=(70, 70, 70, 255))
        
        # 绘制主文字
        draw.text((x, y), text, font=font, fill="white")
        
        # 创建渐变图层
        gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        gradient_draw = ImageDraw.Draw(gradient)
        
        # 绘制渐变
        offset = -3  # 添加偏移量，与create_rainbow_gradient_test保持一致
        for y_pos in range(height):
            # 计算当前位置的相对高度
            rel_pos = (y_pos + offset) / height
            
            seperation = 0.45
            # 确定当前位置的颜色
            if rel_pos < seperation:  # 0-40% 黄色
                color = colors[0]
            else:
                ratio = (rel_pos - seperation) / (.6 - seperation)
                color = tuple(int(colors[1][i] * (1 - ratio) + colors[2][i] * ratio) for i in range(3))
            
            gradient_draw.line([(0, y_pos), (width, y_pos)], fill=color + (255,))
        
        # 创建最终结果图层
        result = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        # 首先粘贴描边
        result.paste(outline_layer, (0, 0), outline_layer)
        
        # 然后粘贴带渐变的文字
        gradient_text = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        gradient_text.paste(gradient, (0, 0), text_layer)
        result.paste(gradient_text, (0, 0), gradient_text)
        
        return result

    
    def draw_player_profile(self, draw, player_data):
        """绘制玩家个人信息"""
        # 加载用户头像
        avatar_path = player_data['data'].get('avatar_path')
        
        # 创建一个新的图层用于渐变效果
        gradient = Image.new('RGBA', (self.cell_width * self.grid_width, self.profile_height))
        gradient_draw = ImageDraw.Draw(gradient)
        
        # 定义颜色
        white = (255, 255, 255)
        pink = (255, 255, 255)
        
        # 创建渐变效果
        for x in range(self.cell_width * self.grid_width):
            # 在800px处开始渐变，持续400px
            if x < 800:  # 原400*2
                color = white
            elif x < 1200:  # 原600*2
                # 线性插值计算颜色
                ratio = (x - 800) / 400.0  # 原(400, 200)*2
                r = int(white[0] * (1 - ratio) + pink[0] * ratio)
                g = int(white[1] * (1 - ratio) + pink[1] * ratio)
                b = int(white[2] * (1 - ratio) + pink[2] * ratio)
                color = (r, g, b)
            else:
                color = pink
            gradient_draw.line([(x, 0), (x, self.profile_height)], fill=color)
        
        # 将渐变图层粘贴到主图像
        self.base_image.paste(gradient, (0, 0))
        
        # 为玩家昵称绘制背景
        draw.rectangle((274, 100, 724, 180), fill=(50, 50, 50, 255))  # 原(137, 50, 362, 90)*2
        
        # 尝试加载头像，如果失败则创建默认头像
        avatar = None
        if avatar_path and os.path.exists(avatar_path):
            try:
                avatar = Image.open(avatar_path)
                # 如果图片模式不是RGBA，转换为RGBA
                if avatar.mode != 'RGBA':
                    avatar = avatar.convert('RGBA')
            except Exception as e:
                print(f"Error loading avatar: {e}")
        
        if avatar is None:
            # 尝试加载默认头像，如果存在的话
            default_avatar_path = 'assets/default_avatar.webp'
            if os.path.exists(default_avatar_path):
                try:
                    avatar = Image.open(default_avatar_path)
                    # 如果图片模式不是RGBA，转换为RGBA
                    if avatar.mode != 'RGBA':
                        avatar = avatar.convert('RGBA')
                except Exception as e:
                    print(f"Error loading default avatar: {e}")
            
            # 如果仍然没有头像，则创建一个简单的默认头像
            if avatar is None:
                # 创建默认头像（使用RGBA模式）
                avatar = Image.new('RGBA', (200, 200), (0, 0, 0, 0))  # 原(100, 100)*2
                draw_avatar = ImageDraw.Draw(avatar)
                # 绘制圆形头像
                draw_avatar.ellipse((20, 20, 180, 180), fill=(150, 150, 150, 255))  # 原(10, 10, 90, 90)*2
        
        # 调整头像大小为200x200
        avatar = avatar.resize((200, 200), Image.Resampling.LANCZOS)  # 原(100, 100)*2
        
        # 创建一个圆形蒙版
        mask = Image.new('L', (200, 200), 0)  # 原(100, 100)*2
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, 200, 200), fill=255)  # 原(0, 0, 100, 100)*2
        
        # 创建一个新的RGBA图像用于头像
        avatar_with_mask = Image.new('RGBA', (200, 200), (0, 0, 0, 0))  # 原(100, 100)*2
        # 使用圆形蒙版粘贴头像
        avatar_with_mask.paste(avatar, (0, 0), mask)
        
        # 粘贴到主图像，使用alpha通道作为蒙版
        self.base_image.paste(avatar_with_mask, (40, 20), avatar_with_mask)  # 原(20, 10)*2
        
        # 绘制玩家名称
        user_name = player_data['data'].get('user_name', '未知玩家')
        level = player_data['data'].get('level', '??') + player_data['data'].get('reincarnation_num', '??') * 100
        draw.text((280, 30), f"Lv.{level}", font=ImageFont.truetype("assets/fonts/combined.ttf", 60), fill=(50, 50, 50))  # 原(140, 10)*2, 30*2
        draw.text((284, 120), user_name, font=ImageFont.truetype("assets/fonts/combined.ttf", 60), fill=(255, 255, 255))  # 原(142, 55)*2, 30*2
        
        # 绘制Rating
        player_rating = player_data['data'].get('player_rating', 0) / 100 if 'player_rating' in player_data['data'] else 0
        rating_font = ImageFont.truetype("assets/fonts/combined.ttf", 70)  # 原30*2
        
        # 绘制"RATING"文字
        draw.text((280, 215), f"RATING", font=ImageFont.truetype("assets/fonts/combined.ttf", 46), fill=(50, 50, 50))  # 原(140, 100)*2, 23*2
        
        # 创建彩虹渐变文字
        rating_text = f"{player_rating:.2f}"
        rainbow_text = self.create_rainbow_text_v4(rating_text, rating_font, 430, 130)  # 原(200, 40)*2
        self.base_image.paste(rainbow_text, (420, 155), rainbow_text)  # 原(170, 83)*2

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
        
        # 预加载所有需要的封面
        all_songs = best_scores[:30] + new_scores[:15] + recent_scores[:10]
        self.preload_jackets(all_songs)
        
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
            self.section_padding + 40  # 底部留空
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
        self.draw_section_title(draw, 40, y_offset + 10, "BEST", best_rating)
        y_offset += self.title_font_size + 10
        
        for i, song_data in enumerate(best_scores[:max_best]):
            x = (i % self.grid_width) * self.cell_width
            y = y_offset + (i // self.grid_width) * self.cell_height
            self.draw_song_cell(draw, x, y, song_data)
        
        # 绘制"新曲"部分
        y_offset += best_rows * self.cell_height + self.section_padding
        self.draw_section_title(draw, 40, y_offset + 10, "NEW", new_rating)
        y_offset += self.title_font_size + 10
        
        for i, song_data in enumerate(new_scores[:max_new]):
            x = (i % self.grid_width) * self.cell_width
            y = y_offset + (i // self.grid_width) * self.cell_height
            self.draw_song_cell(draw, x, y, song_data)
        
        # 绘制"最近"部分
        y_offset += new_rows * self.cell_height + self.section_padding
        self.draw_section_title(draw, 40, y_offset + 10, "RECENT", recent_rating)
        y_offset += self.title_font_size + 10
        
        for i, song_data in enumerate(recent_scores[:max_recent]):
            x = (i % self.grid_width) * self.cell_width
            y = y_offset + (i // self.grid_width) * self.cell_height
            self.draw_song_cell(draw, x, y, song_data)
        
        # 添加底部文字
        footer_text = "Designed by Kcalb_MengWang | Generated by CornBot Powered by Kohakuwu"
        footer_font = ImageFont.truetype("assets/fonts/Torus-SemiBold.otf", 36)  # 使用较小的字号
        
        # 获取文字大小
        bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
        text_width = bbox[2] - bbox[0]
        
        # 计算居中位置
        x = (width - text_width) // 2
        y = total_height - self.section_padding // 2  # 在底部padding的中间位置
        
        # 绘制文字
        draw.text((x, y - 45), footer_text, font=footer_font, fill=(180, 180, 180))  # 使用浅灰色
        
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
            data = json.load(f)
            # 提取profile和rating数据
            profile_data = data.get('profile', {})
            rating_data = data.get('rating', {})
            
            # 构建player_data结构
            player_data = {
                'data': {
                    'user_name': profile_data.get('data', {}).get('user_name', '未知玩家'),
                    'level': profile_data.get('data', {}).get('level', '??'),
                    'player_rating': profile_data.get('data', {}).get('player_rating', 0),
                    'reincarnation_num': profile_data.get('data', {}).get('reincarnation_num', 0),
                    'avatar_path': None  # 暂时不处理头像
                }
            }
            
            # 使用rating数据
            json_data = rating_data
            
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
        player_data = {
            'data': {
                'user_name': '未知玩家',
                'level': '??',
                'player_rating': 0,
                'avatar_path': None
            }
        }
    
    # 生成图像
    generator = B55GramGenerator()
    image = generator.generate(json_data, player_data)
    
    # 保存图像
    image.save('b55_gram.png')
    print("B55-gram has been generated as 'b55_gram.png'")

if __name__ == "__main__":
    main() 