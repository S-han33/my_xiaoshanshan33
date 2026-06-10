# 🤖 AI 资讯聚合器

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![RSS](https://img.shields.io/badge/数据源-RSS-orange.svg)

一个自动化工具，定时抓取国内主流科技媒体的AI资讯，并自动生成一个干净、可读性强的HTML页面，方便你快速了解当日AI领域动态。

**🌐 在线预览：** [https://s-han33.github.io/my_xiaoshanshan33/新闻项目/](https://s-han33.github.io/my_xiaoshanshan33/新闻项目/)

---

## ✨ 功能特点

- **自动化爬取**：使用 Python 脚本，通过 RSS 源自动抓取新闻，无需手动干预。
- **智能筛选**：代码内置关键词，可以从标题和摘要中筛选出与AI强相关的新闻。
- **精美展示**：自动生成一个科技感、卡片式布局的 `index.html` 页面，无需任何配置即可在浏览器中打开。
- **一键跳转**：点击新闻卡片即可直达原文链接，确保信息可追溯。

---

## 📋 更新日志

> **规范**：每次修改必须记录日期、版本号、修改的具体内容、改动的文件清单。

---

### 2026-06-10 v2.4
> **修改人**：AI助手（Senior Developer）
> **修改目的**：修复 GitHub Actions 不可靠、RSS 源被封导致生成假页面的问题

**修改内容：**
1. `news.py` — `HEADERS` 增加完整请求头（Accept、Accept-Language、Accept-Encoding、Connection），模拟真实浏览器行为
2. `news.py` — `fetch_news_from_rss()` 增加3次重试机制，采用指数退避策略（失败间隔 1s / 2s / 4s）
3. `news.py` — 增加 XML 内容校验，防止拿到 HTML 错误页或反爬拦截页
4. `news.py` — 兼容 Dublin Core (`dc:date`) 日期格式，提升 RSS 源兼容性
5. `news.py` — `job()` 抓取全部失败时直接 `return`，不再覆盖旧 `index.html`，避免生成只有"示例数据"的假页面
6. `.github/workflows/daily-news.yml` — cron 从 `0 0 * * *`（每天1次）改为 `0 */6 * * *`（每6小时1次），大幅降低漏执行概率
7. `.github/workflows/daily-news.yml` — 显式声明 `permissions: contents: write`，避免权限不足导致推送失败
8. `.github/workflows/daily-news.yml` — 依赖安装改为从 `requirements.txt` 读取，便于统一管理
9. `新闻项目/.github/workflows/daily-news.yml` — **删除**（重复文件，GitHub 不会识别子目录中的工作流）
10. `README.md` — 新增网站在线预览链接；新增 v2.4 更新日志；统一更新日志格式规范

**改动的文件：**

| 文件 | 操作 |
|------|------|
| `新闻项目/news.py` | 修改 |
| `.github/workflows/daily-news.yml` | 修改 |
| `新闻项目/README.md` | 修改 |
| `新闻项目/.github/workflows/daily-news.yml` | **删除** |

---

### 2026-06-08 v2.3
> **修改人**：药药
> **修改目的**：配置 GitHub Actions，实现每天自动抓取、生成并推送，无需任何手动操作

**修改内容：**
1. `news.py` — 新增 `--once` 参数支持（单次运行后退出，适配 CI 环境）
2. `news.py` — 输出路径改为相对路径 `./index.html`，兼容云端运行
3. `.github/workflows/daily-news.yml` — **新增**，GitHub Actions 工作流：每天 UTC 00:00（北京时间 08:00）自动运行

**改动的文件：**

| 文件 | 操作 |
|------|------|
| `新闻项目/news.py` | 修改 |
| `.github/workflows/daily-news.yml` | 新增 |

**优化内容：**
- 每天北京时间 08:00 自动抓取 → 生成 → 推送到 GitHub Pages
- 支持手动触发：GitHub 仓库 → Actions → Daily News Refresh → Run workflow
- 无需本地运行 `news.py`，不再依赖本地 Python 服务

---

### 2026-06-07 v2.2
> **修改人**：药药
> **修改目的**：RSS源扩展至8个，新增日期排序、新鲜度过滤、去重逻辑，确保每天刷新到最新内容

**修改内容：**
1. `news.py` — RSS源从5个扩展到8个（36氪、IT之家、爱范儿、开源中国、InfoQ、少数派、小众软件、Solidot）
2. `news.py` — 新增 `parse_date()` 函数，兼容 ISO 8601 / RFC 2822 等多种日期格式
3. `news.py` — 新增 `is_fresh()` 新鲜度过滤函数
4. `news.py` — 新增按标题前30字符去重逻辑
5. `news.py` — 新增按日期降序排序
6. `news.py` — 移除关键词筛选，改为全量展示
7. `test_feeds.py` — **新增**，用于测试所有RSS源可用性（已清理）

**改动的文件：**

| 文件 | 操作 |
|------|------|
| `新闻项目/news.py` | 修改 |
| `新闻项目/test_feeds.py` | 新增（已清理） |

**优化内容：**
- RSS源列表：36氪、IT之家、爱范儿、开源中国、InfoQ、少数派、小众软件、Solidot（移除超时的虎嗅和XML错误的游戏邦）
- 日期解析兼容 `2026-06-07T10:00:00+08:00`、`Sun, 07 Jun 2026 05:00:00 GMT` 等多种格式
- 自动去重：同一话题只保留最新版本
- 最新内容置顶：每天打开页面，最上面的就是当天最新资讯
- 控制台输出新鲜度统计：清晰显示今日/昨日新闻数量

---

### 2026-06-07 v2.1
> **修改人**：药药
> **修改目的**：修复无法每天 08:00 自动刷新新闻的问题

**修改内容：**
1. `news.py` — 新增 `schedule`、`time`、`sys` 导入
2. `news.py` — 封装 `job()` 函数，将抓取逻辑独立出来
3. `news.py` — 新增 `main()` 函数，实现循环调度（每分钟检查一次定时任务）
4. `news.py` — 硬编码路径改为 `OUTPUT_FILE` 常量
5. `requirements.txt` — 新增 `schedule>=1.2.0` 依赖

**改动的文件：**

| 文件 | 操作 |
|------|------|
| `新闻项目/news.py` | 修改 |
| `新闻项目/requirements.txt` | 修改 |

**优化内容：**
- 启动时立即执行一次抓取，无需等到 08:00 才能看到效果
- 每分钟检查一次定时任务，CPU 零空转（`time.sleep(60)`）
- 支持 `Ctrl+C` 安全停止服务
- 控制台输出增加时间戳和状态标记，运行日志一目了然

---

## 🚀 快速开始

### 环境要求

- Python 3.10 或更高版本

### 安装与使用

#### 🚀 方式一：全自动（推荐）
项目已配置 **GitHub Actions**，每6小时自动抓取新闻并更新页面。
> 只需 **push 到 GitHub 仓库一次**，之后完全托管在云端，无需本地运行任何东西。
> 也可以在 GitHub 仓库 → Actions → Daily News Refresh → **Run workflow** 手动触发。

#### 💻 方式二：本地运行
1.  **克隆项目** (或直接下载代码)
    ```bash
    git clone https://github.com/S-han33/my_xiaoshanshan33.git
    cd my_xiaoshanshan33/新闻项目
    ```

2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

3.  **启动服务**
    ```bash
    python news.py
    ```

4.  **查看结果**
    程序会自动生成 `index.html`，用浏览器打开即可查看。
