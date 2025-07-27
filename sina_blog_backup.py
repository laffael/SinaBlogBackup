#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sina Blog Backup
备份新浪博客为 Markdown + 图片
Author: Raphael Wang (https://github.com/laffael)
License: GNU GPL v3
"""

import os
import re
import time
import requests
import browser_cookie3
from bs4 import BeautifulSoup
import html2text
from urllib.parse import urljoin, urlparse
from datetime import datetime
from html import unescape
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3
import glob

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === 用户配置 ===
BLOG_UID = "123456"  # ✅ 手动设置博客 UID
OUTPUT_DIR = input("请输入输出目录（默认 output_md）: ").strip() or "output_md"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_DIR)

REQUEST_DELAY = 1.0   # ✅ 请求间隔（秒）
ENABLE_LOG_FILE = True  # ✅ 是否写日志文件

LIST_URL = "https://blog.sina.com.cn/s/articlelist_{uid}_0_{page}.html"
FAILED_FILE = os.path.join(OUTPUT_DIR, "failed_articles.txt")
FAILED_IMG_FILE = os.path.join(OUTPUT_DIR, "failed_images.txt")

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

session = requests.Session()
retry = Retry(connect=5, read=5, backoff_factor=1)
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)

# === 日志工具 ===
LOG_FILE = os.path.join(OUTPUT_DIR, "backup.log")
def log(msg):
    print(msg)
    if ENABLE_LOG_FILE:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

# === 工具函数 ===
def safe_filename(name):
    return re.sub(r'[\\/:*?"<>|]', '_', name)

def ascii_headers(headers):
    clean = {}
    for k, v in headers.items():
        try:
            v.encode('ascii')
            clean[k] = v
        except UnicodeEncodeError:
            pass
    return clean

def get_cookies():
    cj = browser_cookie3.chrome(domain_name="sina.com.cn")
    cookies_dict = {}
    for c in cj:
        try:
            c.value.encode('ascii')
            cookies_dict[c.name] = c.value
        except UnicodeEncodeError:
            log(f"[WARN] 跳过非ASCII Cookie: {c.name}")
    log("[INFO] 已从 Chrome 读取 Cookies")
    return cookies_dict

COOKIES = get_cookies()

# === 检查文章是否已存在 ===
def article_exists(meta):
    filename = f"{meta['date']}-[{safe_filename(meta['title'])}].md"
    path = os.path.join(OUTPUT_DIR, filename)
    return os.path.exists(path)

def record_failed(meta):
    with open(FAILED_FILE, "a", encoding="utf-8") as f:
        f.write(f"{meta['date']}|{meta['title']}|{meta['url']}\n")

def record_failed_image(url):
    with open(FAILED_IMG_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

# === 获取总页数 ===
def get_total_pages(uid):
    url = LIST_URL.format(uid=uid, page=1)
    r = session.get(url, headers=ascii_headers(HEADERS), cookies=COOKIES,
                    verify=False, allow_redirects=True, timeout=10)
    r.encoding = 'utf-8' if 'utf-8' in r.text.lower() else 'gbk'
    soup = BeautifulSoup(r.text, "html.parser")
    page_info = soup.find(string=re.compile("共\\d+页"))
    if page_info:
        m = re.search(r'共(\d+)页', page_info)
        if m:
            return int(m.group(1))
    return 1

# === 抓取文章链接 ===
def fetch_article_links(uid, total_pages):
    links = []
    for p in range(1, total_pages+1):
        url = LIST_URL.format(uid=uid, page=p)
        log(f"[INFO] 抓取列表页: {url}")
        try:
            r = session.get(url, headers=ascii_headers(HEADERS), cookies=COOKIES,
                            verify=False, allow_redirects=True, timeout=10)
        except requests.exceptions.Timeout:
            log(f"[ERROR] 列表页超时: {url}")
            continue

        r.encoding = 'utf-8' if 'utf-8' in r.text.lower() else 'gbk'
        soup = BeautifulSoup(r.text, "html.parser")
        for cell in soup.select("span.atc_title a"):
            href = cell.get("href")
            if href.startswith("//"):
                href = "https:" + href
            title = unescape(cell.get_text(strip=True))
            p_tag = cell.find_parent("span").find_parent("p")
            date_tag = p_tag.find_next_sibling("p").select_one("span.atc_tm") if p_tag else None
            date_text = date_tag.get_text(strip=True) if date_tag else "1970-01-01 00:00"
            try:
                dt = datetime.strptime(date_text, "%Y-%m-%d %H:%M")
                date_fmt = dt.strftime("%Y%m%d")
            except:
                date_fmt = "19700101"
            links.append({"url": href, "title": title, "date": date_fmt})
        time.sleep(REQUEST_DELAY)
    return links

# === 下载图片 ===
def download_images(html, base_url, article_id):
    soup = BeautifulSoup(html, "html.parser")
    img_dir = os.path.join(OUTPUT_DIR, "images", article_id)
    os.makedirs(img_dir, exist_ok=True)

    for a_tag in soup.find_all("a", href=True):
        img_tag = a_tag.find("img")
        if img_tag:
            img_url = a_tag["href"]
            if not img_url.startswith("http"):
                img_url = urljoin(base_url, img_url)

            if re.match(r"https?://s\d+\.sinaimg\.cn/orignal/[0-9a-zA-Z]+", img_url):
                file_id = os.path.basename(urlparse(img_url).path)
                filename = f"{file_id}.jpg"
                img_path = os.path.join(img_dir, filename)

                if os.path.exists(img_path) and os.path.getsize(img_path) > 0:
                    img_tag["src"] = f"./images/{article_id}/{filename}"
                    continue

                headers = {
                    "User-Agent": "Mozilla/5.0",
                    "Referer": "https://blog.sina.com.cn/",
                }

                try:
                    r = session.get(img_url, headers=ascii_headers(headers), cookies=COOKIES,
                                    verify=False, allow_redirects=True, timeout=30)
                    if "image" not in r.headers.get("Content-Type", ""):
                        log(f"[WARN] 非图片响应: {img_url}")
                        continue
                    with open(img_path, "wb") as f:
                        f.write(r.content)
                    img_tag["src"] = f"./images/{article_id}/{filename}"
                    log(f"[IMG] 下载原图: {filename}")
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                    log(f"[ERROR] 图片下载失败: {img_url}")
                    record_failed_image(img_url)

    return str(soup)

# === 抓取文章 ===
def fetch_article(url):
    log(f"[INFO] 抓取文章: {url}")
    try:
        r = session.get(url, headers=ascii_headers(HEADERS), cookies=COOKIES,
                        verify=False, allow_redirects=True, timeout=10)
    except requests.exceptions.Timeout:
        log(f"[ERROR] 文章超时: {url}")
        return None

    r.encoding = 'utf-8' if 'utf-8' in r.text.lower() else 'gbk'
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.select_one("h2.titName").get_text(strip=True)
    content_div = soup.select_one("div.articalContent")
    html = str(content_div)
    article_id = re.search(r'blog_([0-9a-zA-Z]+)\.html', url).group(1)
    return {"title": title, "html": html, "id": article_id}

# === 保存 Markdown ===
def save_md(article, meta):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"{meta['date']}-[{safe_filename(meta['title'])}].md"
    path = os.path.join(OUTPUT_DIR, filename)

    html = download_images(article["html"], meta["url"], article["id"])
    md_content = html2text.html2text(html)

    with open(path, "w", encoding="utf-8") as f:
        f.write(md_content)
    log(f"[SAVE] 已保存: {path}")

# === 模式 2：重新下载所有图片 ===
def redownload_all_images():
    log("[INFO] 开始扫描 Markdown 文件重新下载图片...")
    md_files = glob.glob(os.path.join(OUTPUT_DIR, "*.md"))
    if not md_files:
        log("[INFO] 没有找到 Markdown 文件")
        return

    for md_file in md_files:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        urls = re.findall(r"https?://s\d+\.sinaimg\.cn/orignal/[0-9a-zA-Z]+", content)
        if not urls:
            continue

        article_id = os.path.splitext(os.path.basename(md_file))[0]
        img_dir = os.path.join(OUTPUT_DIR, "images", article_id)
        os.makedirs(img_dir, exist_ok=True)

        for img_url in urls:
            file_id = os.path.basename(urlparse(img_url).path)
            filename = f"{file_id}.jpg"
            img_path = os.path.join(img_dir, filename)

            if os.path.exists(img_path) and os.path.getsize(img_path) > 0:
                continue

            try:
                r = session.get(img_url, headers=ascii_headers(HEADERS), cookies=COOKIES,
                                verify=False, allow_redirects=True, timeout=30)
                if "image" not in r.headers.get("Content-Type", ""):
                    continue
                with open(img_path, "wb") as f:
                    f.write(r.content)
                log(f"[IMG] 重新下载图片: {filename}")
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                log(f"[ERROR] 图片下载超时: {img_url}")
                record_failed_image(img_url)

# === 模式 3：重新下载失败文章 ===
def retry_failed():
    if not os.path.exists(FAILED_FILE):
        log("[INFO] 无失败记录")
        return
    with open(FAILED_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    if not lines:
        log("[INFO] 无失败文章")
        return

    log(f"[INFO] 重试 {len(lines)} 篇失败文章...")
    open(FAILED_FILE, "w").close()
    for line in lines:
        date, title, url = line.split("|", 2)
        meta = {"url": url, "title": title, "date": date}
        if article_exists(meta):
            log(f"[SKIP] 已存在文章，跳过: {title}")
            continue
        article = fetch_article(url)
        if article:
            save_md(article, meta)
        else:
            record_failed(meta)
        time.sleep(REQUEST_DELAY)

# === 模式 4：重新下载失败图片 ===
def retry_failed_images():
    if not os.path.exists(FAILED_IMG_FILE):
        log("[INFO] 无失败图片记录")
        return
    with open(FAILED_IMG_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
    if not urls:
        log("[INFO] 无失败图片")
        return

    log(f"[INFO] 重试 {len(urls)} 张失败图片...")
    remaining = []
    for img_url in urls:
        file_id = os.path.basename(urlparse(img_url).path)
        filename = f"{file_id}.jpg"
        img_dir = os.path.join(OUTPUT_DIR, "images", "retry")
        os.makedirs(img_dir, exist_ok=True)
        img_path = os.path.join(img_dir, filename)

        if os.path.exists(img_path) and os.path.getsize(img_path) > 0:
            continue

        try:
            r = session.get(img_url, headers=ascii_headers(HEADERS), cookies=COOKIES,
                            verify=False, allow_redirects=True, timeout=30)
            if "image" not in r.headers.get("Content-Type", ""):
                remaining.append(img_url)
                continue
            with open(img_path, "wb") as f:
                f.write(r.content)
            log(f"[OK] 重试成功: {filename}")
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            log(f"[ERROR] 仍然失败: {img_url}")
            remaining.append(img_url)

    with open(FAILED_IMG_FILE, "w", encoding="utf-8") as f:
        for url in remaining:
            f.write(url + "\n")
    log(f"[INFO] 剩余失败图片: {len(remaining)}")

# === 主流程 ===
def backup_blog(uid):
    total_pages = get_total_pages(uid)
    log(f"[INFO] 检测到总页数: {total_pages}")
    metas = fetch_article_links(uid, total_pages)
    if not metas:
        log("[ERROR] 未获取到文章")
        return

    log("\n[INFO] 检测到以下文章：")
    for meta in metas:
        log(f"{meta['date']}-[{meta['title']}]")

    confirm = input("\n是否抓取这些文章？ (y/n): ").strip().lower()
    if confirm != 'y':
        log("[INFO] 用户取消抓取")
        return

    for meta in metas:
        if article_exists(meta):
            log(f"[SKIP] 已存在文章，跳过: {meta['title']}")
            continue
        article = fetch_article(meta["url"])
        if article:
            save_md(article, meta)
        else:
            record_failed(meta)
        time.sleep(REQUEST_DELAY)

if __name__ == "__main__":
    mode = input("选择模式: 1=正常抓取  2=重新下载所有图片  3=重新下载失败文章  4=重新下载失败图片: ").strip()
    if mode == '2':
        redownload_all_images()
    elif mode == '3':
        retry_failed()
    elif mode == '4':
        retry_failed_images()
    else:
        backup_blog(BLOG_UID)
