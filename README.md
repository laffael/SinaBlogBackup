# 📌 Sina Blog Backup

一个用于 **批量备份新浪博客文章到 Markdown** 的 Python 脚本，支持自动下载文章内的图片，断点续传，失败重试，并可自定义输出目录。

作者：[Raphael Wang](https://github.com/laffael)  
许可证：[GNU GPL v3](LICENSE)

---

## ✨ 功能特性

- ✅ 批量抓取新浪博客文章，保存为 Markdown 格式
- ✅ 自动下载文章内的新浪原图并使用相对路径
- ✅ 自动从 Chrome 读取 Cookies（支持登录后私密文章）
- ✅ 已下载文章与图片自动跳过（断点续传）
- ✅ 失败的文章与图片自动记录，可单独重试
- ✅ 自定义输出目录与抓取速度
- ✅ 完整日志输出（可选写入文件）

---

## 📂 目录结构

```
SinaBlogBackup/
├── sina_blog_backup.py       # 主脚本
├── output_md/                # 文章与图片输出目录
│   ├── 文章1.md
│   ├── 文章2.md
│   └── images/
│       ├── blogid1/
│       │   ├── abc123.jpg
│       │   └── def456.jpg
│       └── retry/
├── failed_articles.txt        # 下载失败的文章记录
├── failed_images.txt          # 下载失败的图片记录
└── backup.log                 # 日志文件（可选）
```

---

## 🔧 可配置参数

在 `sina_blog_backup.py` 顶部配置：

| 参数名 | 类型 | 默认值 | 说明 |
|-------|------|-------|------|
| `BLOG_UID` | `str` | `"1234567890"` | 博客 UID，需手动填写，例如 `articlelist_1234567890` 中的数字部分 |
| `OUTPUT_DIR` | `str` | `"output_md"` | 输出目录，运行时可输入，支持相对/绝对路径 |
| `REQUEST_DELAY` | `float` | `1.0` | 请求间隔秒数，防止过快请求导致封锁 |
| `ENABLE_LOG_FILE` | `bool` | `True` | 是否将日志写入 `backup.log` 文件 |

### 示例配置

```python
BLOG_UID = "1234567890"          # 我的博客 UID
OUTPUT_DIR = "my_backup"         # 自定义输出目录
REQUEST_DELAY = 2.5              # 每 2.5 秒抓取一次
ENABLE_LOG_FILE = False          # 只输出到终端，不写日志文件
```

---

## 🚀 使用方法

### 1️⃣ 安装依赖

```bash
pip install requests beautifulsoup4 html2text browser-cookie3
```

### 2️⃣ 设置 UID

编辑 `sina_blog_backup.py` 修改：

```python
BLOG_UID = "你的UID"
```

UID 获取：访问博客首页，URL 类似：

```
https://blog.sina.com.cn/s/articlelist_1234567890_0_1.html
```

其中 `1234567890` 即 UID。

### 3️⃣ 运行脚本

```bash
python sina_blog_backup.py
```

运行后会提示模式选择：

```
选择模式: 1=正常抓取  2=重新下载所有图片  3=重新下载失败文章  4=重新下载失败图片
```

---

## 📜 模式说明

- **模式 1：正常抓取**
  - 抓取所有文章并保存为 Markdown
  - 已下载文章自动跳过（断点续传）

- **模式 2：重新下载所有图片**
  - 扫描 Markdown 文件
  - 重新下载所有新浪原图

- **模式 3：重新下载失败文章**
  - 读取 `failed_articles.txt`
  - 重新抓取失败的文章

- **模式 4：重新下载失败图片**
  - 读取 `failed_images.txt`
  - 重新下载所有失败的图片

---

## 📢 注意事项

- 本地需安装 Chrome 并已登录新浪博客账号
- 网络不稳定时可能出现超时，失败的文章/图片会自动记录
- 调整 `REQUEST_DELAY` 以避免触发请求限制

---

## 📄 License

本项目基于 **GNU General Public License v3.0 (GPLv3)** 授权发布。

- 允许自由使用、修改和分发
- 分发或修改必须保持相同开源协议
- 禁止闭源或商业化发布

👉 详细条款见 [LICENSE](LICENSE)

---

## 👤 作者

- **Raphael Wang**  
- GitHub: [https://github.com/laffael](https://github.com/laffael)
