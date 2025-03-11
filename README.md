# ONGEKI B50数据导出工具

这是一个用于获取ONGEKI音游B50数据并转换为Excel格式的Python工具。支持从u.otogame.net获取玩家的Rating数据，并生成详细的Excel报表。

## 功能特点

- 自动登录bemanicn.com并完成OAuth认证
- 获取玩家的B50数据（最佳、新曲、最近）
- 计算歌曲定数
- 生成美观的Excel报表
- 支持代理设置
- 详细的日志记录

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/your-username/otogame-b50-to-xlsx.git
cd otogame-b50-to-xlsx
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
python get_rating.py --email 您的邮箱 --password 您的密码 --excel
```

### 命令行参数

- `--email`: bemanicn.com的账号邮箱
- `--password`: bemanicn.com的账号密码
- `--output`: 输出文件名（默认：b50.json）
- `--excel`: 同时生成Excel文件（可选）
- `--debug`: 开启详细调试信息（可选）
- `--no-proxy`: 禁用代理（可选）

### 示例

1. 仅获取JSON数据：
```bash
python get_rating.py --email user@example.com --password yourpassword
```

2. 获取数据并生成Excel：
```bash
python get_rating.py --email user@example.com --password yourpassword --excel
```

3. 开启调试模式：
```bash
python get_rating.py --email user@example.com --password yourpassword --excel --debug
```

## 工作原理

1. **登录流程**
   - 获取OAuth重定向URL
   - 访问OAuth授权页面
   - 使用账号密码登录bemanicn.com
   - 获取授权码（code）

2. **获取令牌**
   - 使用授权码访问回调URL
   - 获取访问令牌（access token）
   - 获取ID令牌（id token）

3. **获取数据**
   - 使用ID令牌访问音乐页面
   - 获取Rating数据
   - 保存为JSON格式

4. **Excel转换**
   - 读取JSON数据
   - 计算歌曲定数
   - 生成三个部分（最佳、新曲、最近）
   - 格式化Excel表格
   - 添加统计信息

## Excel文件格式

生成的Excel文件包含以下内容：

1. **最佳成绩**
   - 歌曲列表（按Rating排序）
   - 每首歌的分数、定数和单曲Rating
   - 最佳成绩的总Rating

2. **新曲成绩**
   - 新曲列表
   - 相关统计数据

3. **最近成绩**
   - 最近游玩记录
   - 相关统计数据

## 注意事项

- 需要有效的bemanicn.com账号
- 确保网络连接稳定
- 如果遇到连接问题，可以尝试使用`--no-proxy`选项
- 调试信息会保存在`otogame_debug.log`文件中

## 常见问题

1. **登录失败**
   - 检查账号密码是否正确
   - 确认网络连接是否正常
   - 查看调试日志获取详细错误信息

2. **数据获取失败**
   - 可能是令牌过期，重新运行程序
   - 检查网络连接
   - 确认账号权限是否正常

3. **Excel生成失败**
   - 确保JSON数据文件存在且格式正确
   - 检查是否有足够的磁盘空间
   - 确保Excel文件未被其他程序占用

## 贡献

欢迎提交Issue和Pull Request来改进这个工具。

## 许可证

MIT License 