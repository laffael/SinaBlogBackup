# Sina Blog Backup

一个用于 **批量备份新浪博客文章到 Markdown** 的 Python 脚本，支持自动下载文章内的图片，断点续传，失败重试，并可自定义输出目录。

Sina Blog Backup 由 [Raphael Wang](https://github.com/laffael) 编写，遵守 [GNU GPL v3](LICENSE) 协议发布，可自由使用和修改，但 **严禁将本软件及其衍生品用于任何商业用途**。项目基于微博现有接口和 Python 构建，提供便捷的备份方式，目前适用于 Windows 与 macOS。接受功能建议，但一般不接受定制开发需求。

该脚本可以将新浪博客文章及其中的图片下载并保存为 Markdown 文件，支持断点续传与失败重试。

## 特性

- 抓取指定 UID 下的全部文章
- 自动下载正文内的图片并使用相对路径
- 支持从 Chrome 读取登录 Cookies
- 已下载内容自动跳过，支持断点续传
- 失败的任务会记录到文本，方便再次尝试
- 可自定义输出目录、请求间隔和日志

## 快速开始

1. 安装依赖
   ```bash
   pip install requests beautifulsoup4 html2text browser-cookie3
   ```
2. 编辑 `sina_blog_backup.py` 设置 `BLOG_UID` 与其他参数
3. 运行脚本
   ```bash
   python sina_blog_backup.py
   ```
4. 根据提示选择模式即可开始备份

## 目录结构

```text
SinaBlogBackup/
├── sina_blog_backup.py       # 主脚本
├── output_md/                # 默认文章与图片目录
│   ├── xxx.md
│   └── images/
├── failed_articles.txt       # 下载失败的文章
├── failed_images.txt         # 下载失败的图片
└── backup.log                # 日志（可选）
```

## 模式说明

1. **正常抓取**：抓取所有文章并保存为 Markdown
2. **重新下载所有图片**：扫描现有文章并重新下载所有图片
3. **重新下载失败文章**：读取 `failed_articles.txt` 重新抓取
4. **重新下载失败图片**：读取 `failed_images.txt` 重新下载

## 配置示例

在脚本顶部可修改以下变量：

```python
BLOG_UID = "1234567890"      # 博客 UID
OUTPUT_DIR = "output_md"     # 输出目录
REQUEST_DELAY = 1.0          # 请求间隔秒数
ENABLE_LOG_FILE = True       # 是否写入日志文件
```

## 注意事项

- 需在本机 Chrome 浏览器登录新浪博客账号
- 网络波动可能导致请求超时，失败的任务会自动记录
- 如需提高速度或避免封锁，可调整 `REQUEST_DELAY`

## License

本项目基于 [GNU GPL v3](LICENSE) 协议发布，可自由使用和修改，但必须以相同协议开源，**禁止任何商业用途**。

## Author

[Raphael Wang](https://github.com/laffael)
