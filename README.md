# ONGEKI Best 55数据导出工具

这是一个用于获取 ONGEKI 游戏数据并转换为 Excel 格式的工具。

## 功能特点
- 自动登录 bemanicn.com 账号
- 自动处理 OAuth 授权流程
- 自动处理 Cloudflare 防护
- 获取 Best 评分数据
- 计算歌曲定数
- 生成美观的 Excel 报表
- 支持代理配置
- 详细的日志记录

## 安装说明

1. 克隆仓库：
```bash
git clone https://github.com/NightmareDreemurr/otogame-b50-to-xlsx.git
cd otogame-b50-to-xlsx
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

基本用法：
```bash
python get_rating.py --email 您的邮箱 --password 您的密码 --excel
```

命令行参数：
- `--email`: bemanicn.com 账号邮箱
- `--password`: bemanicn.com 账号密码
- `--output`: 输出文件名（默认：b50.json）
- `--excel`: 同时生成 Excel 文件
- `--debug`: 开启详细调试信息
- `--no-proxy`: 禁用代理

示例：
1. 仅获取 JSON 数据：
```bash
python get_rating.py --email your@email.com --password yourpassword
```

2. 获取数据并生成 Excel：
```bash
python get_rating.py --email your@email.com --password yourpassword --excel
```

## 工作原理

### OAuth 授权流程

本工具实现了完整的 OAuth 自动授权流程：

1. **初始化授权**：
   - 访问 u.otogame.net 获取 OAuth 重定向 URL
   - 自动重定向到 bemanicn.com 的授权页面

2. **登录处理**：
   - 如果未登录，自动跳转到登录页面
   - 提交登录凭据
   - 处理登录后的重定向

3. **授权确认**：
   - 自动检测是否需要授权确认
   - 如果需要确认，自动提取表单数据
   - 模拟点击"同意"按钮完成授权

4. **授权码处理**：
   - 获取授权回调中的授权码
   - 使用授权码获取访问令牌
   - 使用访问令牌获取 ID 令牌

### Cloudflare 绕过机制

本工具使用 `cloudscraper` 库来自动处理 Cloudflare 的防护机制。主要特点：

1. 自动模拟浏览器行为：
   - 使用真实的浏览器指纹
   - 处理 JavaScript 挑战
   - 自动管理 cookies

2. 配置说明：
```python
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)
```

### 数据获取流程

1. **登录流程**：
   - 访问 u.otogame.net 获取 OAuth 重定向 URL
   - 重定向到 bemanicn.com 的登录页面
   - 提交登录凭据（邮箱和密码）
   - 处理登录后的 OAuth 重定向

2. **令牌获取**：
   - 从 OAuth 回调 URL 获取授权码
   - 使用授权码获取访问令牌（Access Token）
   - 使用访问令牌获取 ID 令牌（ID Token）

3. **评分数据获取**：
   - 使用 ID 令牌访问音乐页面
   - 调用评分 API 获取 B50 数据
   - 数据包含：最佳成绩、新曲成绩、最近成绩

4. **数据处理**：
   - 解析 JSON 响应
   - 计算歌曲定数
   - 生成评分统计

### Excel 文件格式

生成的 Excel 文件包含以下内容：

1. **最佳成绩区域**：
   - 显示评分最高的歌曲
   - 包含歌曲名、难度、定数、分数、单曲 Rating

2. **新曲区域**：
   - 显示最近更新的歌曲成绩
   - 与最佳成绩区域格式相同

3. **最近成绩区域**：
   - 显示最近游玩的歌曲成绩
   - 与最佳成绩区域格式相同

4. **统计信息**：
   - 各区域歌曲数量
   - 各区域 Rating 小计
   - 总 Rating 计算

## 注意事项

1. 需要有效的 bemanicn.com 账号
2. 首次使用时会自动进行 OAuth 授权
3. 授权信息会被保存，后续使用无需重复授权
4. 确保网络环境稳定
5. 首次运行可能需要较长时间（Cloudflare 验证）
6. 建议开启 `--debug` 选项查看详细日志

## 常见问题

1. **登录失败**：
   - 检查账号密码是否正确
   - 确认网络连接是否稳定
   - 查看是否触发了 Cloudflare 验证

2. **授权失败**：
   - 检查是否已正确登录
   - 确认账号是否有访问权限
   - 查看详细日志了解授权流程状态

3. **数据获取失败**：
   - 检查令牌是否过期
   - 可能需要重新授权
   - 查看详细日志定位问题

4. **Excel 生成问题**：
   - 确保 Excel 文件未被其他程序占用
   - 检查是否有写入权限
   - 查看 Python 依赖是否正确安装

## 贡献指南

欢迎提交 Issues 和 Pull Requests！

## 开源协议

MIT License 
