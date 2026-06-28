import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime
import schedule
import time
import sys

# ========== 10+ 个 RSS 源（覆盖 AI / 科技 / 开源） ==========
RSS_FEEDS = [
    {'name': '36氪', 'url': 'https://36kr.com/feed'},
    {'name': 'IT之家', 'url': 'https://www.ithome.com/rss'},
    {'name': '爱范儿', 'url': 'https://www.ifanr.com/feed'},
    {'name': '开源中国', 'url': 'https://www.oschina.net/news/rss'},
    {'name': 'InfoQ', 'url': 'https://www.infoq.cn/feed'},
    {'name': '少数派', 'url': 'https://sspai.com/feed'},
    {'name': '小众软件', 'url': 'https://feeds.appinn.com/appinns/'},
    {'name': 'Solidot', 'url': 'https://www.solidot.org/index.rss'},
    {'name': '机器之心', 'url': 'https://www.jiqizhixin.com/rss'},
    {'name': '量子位 QbitAI', 'url': 'https://rss.aishort.top/?type=qbitai'},
    {'name': '虎嗅网 AI ', 'url': 'https://rss.aishort.top/?type=huxiu&column=tech'},
]

# 输出文件路径（相对路径，兼容本地和 GitHub Actions）
OUTPUT_FILE = './index.html'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*;q=0.9',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}


# ========== 日期解析（兼容多种 RSS 日期格式） ==========
def parse_date(date_str):
    """将多种格式的 RSS 日期转为 YYYY-MM-DD 字符串"""
    if not date_str:
        return None
    try:
        # 格式1: "2026-06-07T10:00:00+08:00" 或 "2026-06-07"
        match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
        if match:
            return match.group(1)
        # 格式2: "Sun, 07 Jun 2026 05:00:00 GMT" 之类
        for fmt in [
            '%a, %d %b %Y %H:%M:%S %Z',
            '%a, %d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
        ]:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
    except Exception:
        pass
    return None


# ========== AI 关键词过滤 ==========
AI_KEYWORDS = [
    # 中文核心
    'ai', '人工智能', '机器学习', '深度学习', '大模型', '大语言模型',
    'llm', 'gpt', 'chatgpt', 'openai', 'claude', 'gemini', 'copilot',
    '智能体', 'agent', 'aigc', '生成式', '多模态', '神经网络',
    'transformer', '扩散模型', 'sora', 'midjourney', 'stable diffusion',
    'hugging face', 'mistral', 'anthropic',
    # 中英文混合
    '大模型', '推理模型', '语言模型', '视觉模型', '文生', '图生',
    'ai芯片', 'ai处理器', 'ai应用', 'ai助手', 'ai功能',
    '算法', '算力', '神经网络',
    # 关键应用
    '自动驾驶', '无人驾驶', '机器人', '智能语音', '自然语言处理',
    '计算机视觉', '人脸识别', '图像识别',
    # 英文
    'artificial intelligence', 'machine learning', 'deep learning',
    'neural network', 'large language model', 'computer vision',
    'autonomous driving', 'natural language processing',
]


def is_ai_related(item):
    """判断一条新闻是否与 AI 相关（匹配标题和摘要）"""
    text = (item['title'] + ' ' + item['summary']).lower()
    for kw in AI_KEYWORDS:
        if kw.lower() in text:
            return True
    return False


def is_fresh(date_str, max_days=2):
    """判断日期是否在最近 X 天内"""
    if not date_str:
        return False
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        diff = (datetime.now() - dt).days
        return 0 <= diff <= max_days
    except ValueError:
        return False


# ========== 从 RSS 订阅源抓取 ==========
def fetch_news_from_rss(feed, max_items=15, max_retries=3):
    """从 RSS 订阅源抓取新闻（带重试机制）"""
    for attempt in range(max_retries):
        try:
            response = requests.get(feed['url'], timeout=15, headers=HEADERS)
            response.raise_for_status()
            
            # 强制以 UTF-8 解码（requests 自动检测可能出错，导致中文乱码）
            response.encoding = 'utf-8'
            
            # 防御：检查返回的是否为 XML，防止拿到 HTML 错误页
            text_start = response.text.strip()[:200].lower()
            if not (text_start.startswith('<?xml') or '<rss' in text_start or '<feed' in text_start):
                raise ValueError(f"返回内容不是 XML: {text_start[:50]}")
            
            root = ET.fromstring(response.text)

            articles = []
            for item in root.findall('.//item')[:max_items]:
                title = item.find('title').text if item.find('title') is not None else ''
                link = item.find('link').text if item.find('link') is not None else ''
                description = item.find('description').text if item.find('description') is not None else ''
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
                
                # 兼容 Dublin Core 日期格式
                if not pub_date:
                    dc_date = item.find('.//{http://purl.org/dc/elements/1.1/}date')
                    if dc_date is not None:
                        pub_date = dc_date.text

                # 解析日期，失败则用今天
                parsed = parse_date(pub_date)
                if not parsed:
                    parsed = datetime.now().strftime('%Y-%m-%d')

                articles.append({
                    'title': title,
                    'url': link,
                    'summary': description[:200] if description else '',
                    'source': feed['name'],
                    'time': parsed,
                    'raw_date': pub_date,
                })
            return articles
        except Exception as e:
            print(f"  [WARN] 抓取 {feed['name']} 失败 (尝试 {attempt+1}/{max_retries}): {str(e)[:80]}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避：1s, 2s, 4s
            else:
                return []
    return []


def format_display_date(date_str):
    """将 YYYY-MM-DD 转为 '2026 年 06 月 13 日 星期六' 格式"""
    week_days = ['一', '二', '三', '四', '五', '六', '日']
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        w = week_days[dt.weekday()]
        return f'{dt.year} 年 {dt.month:02d} 月 {dt.day:02d} 日  星期{w}'
    except ValueError:
        now = datetime.now()
        w = week_days[now.weekday()]
        return f'{now.year} 年 {now.month:02d} 月 {now.day:02d} 日  星期{w}'


def generate_html(news_list):
    """生成 HTML（暗色科技风 - 图片同款设计）"""
    if not news_list:
        print("警告：没有新闻数据，生成空白页面")
        news_list = [{
            'title': '示例：请检查网络或 RSS 源',
            'url': '#',
            'summary': '目前没有抓取到新闻，请确认网络连接或稍后重试',
            'source': '系统提示',
            'time': datetime.now().strftime('%Y-%m-%d')
        }]

    # 用最新一条新闻的日期作为标题日期
    latest_date = news_list[0]['time'] if news_list else datetime.now().strftime('%Y-%m-%d')
    date_str = format_display_date(latest_date)

    now = datetime.now()

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>今日 AI 资讯</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    background: #060608;
    color: #e8e8ec;
    min-height: 100vh;
    position: relative;
    overflow-x: hidden;
  }}

  /* ========== 全局背景光效层 ========== */
  .bg-lights {{
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
  }}

  .bg-lights .beam-left {{
    position: absolute;
    top: -5%;
    left: -30%;
    width: 80vw;
    height: 80vh;
    background: conic-gradient(from 200deg at 50% 50%, transparent 0deg, rgba(255, 130, 40, 0.20) 50deg, rgba(255, 90, 20, 0.10) 100deg, transparent 160deg);
    filter: blur(80px);
    transform: rotate(-10deg);
  }}

  .bg-lights .beam-right {{
    position: absolute;
    top: -5%;
    right: -30%;
    width: 80vw;
    height: 80vh;
    background: conic-gradient(from -20deg at 50% 50%, transparent 0deg, rgba(255, 130, 40, 0.20) 50deg, rgba(255, 90, 20, 0.10) 100deg, transparent 160deg);
    filter: blur(80px);
    transform: rotate(10deg);
  }}

  .bg-lights .glow-top {{
    position: absolute;
    top: -150px;
    left: 50%;
    transform: translateX(-50%);
    width: 600px;
    height: 350px;
    background: radial-gradient(ellipse, rgba(255, 140, 50, 0.06) 0%, transparent 65%);
  }}

  .container {{
    max-width: 800px;
    margin: 0 auto;
    position: relative;
    z-index: 1;
    padding: 0 20px;
  }}

  /* ========== Hero 头部区域 ========== */
  .hero {{
    text-align: center;
    padding: 70px 0 36px;
    position: relative;
  }}

  /* 顶部标签 pills */
  .hero .top-pills {{
    display: inline-flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 32px;
  }}

  .hero .pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 16px;
    border-radius: 100px;
    font-size: 12px;
    font-weight: 500;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.02);
    color: #888;
    backdrop-filter: blur(12px);
    transition: all 0.3s;
    cursor: default;
  }}

  .hero .pill.pill-active {{
    border-color: rgba(255, 140, 50, 0.30);
    background: rgba(255, 140, 50, 0.08);
    color: #ff8c32;
  }}

  /* 大标题 - 白 + 橙渐变 */
  .hero h1 {{
    font-size: 44px;
    font-weight: 700;
    color: #f5f5f8;
    line-height: 1.15;
    margin-bottom: 14px;
    letter-spacing: -0.5px;
  }}

  .hero h1 .highlight {{
    background: linear-gradient(135deg, #ff8c32 0%, #ffb347 50%, #ff4d00 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }}

  /* 日期副标题 */
  .hero .date {{
    font-size: 15px;
    color: #666;
    letter-spacing: 1px;
    margin-bottom: 36px;
  }}

  /* ========== 统计条（微透明框） ========== */
  .stats-bar {{
    display: flex;
    justify-content: center;
    gap: 16px;
    margin-bottom: 44px;
    flex-wrap: wrap;
  }}

  .stat-item {{
    text-align: center;
    padding: 16px 26px;
    min-width: 100px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    backdrop-filter: blur(16px);
    transition: all 0.3s;
  }}

  .stat-item:hover {{
    border-color: rgba(255, 140, 50, 0.18);
    background: rgba(255, 255, 255, 0.035);
    transform: translateY(-2px);
  }}

  .stat-item .num {{
    font-size: 26px;
    font-weight: 700;
    background: linear-gradient(135deg, #ff8c32 0%, #ffb347 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
    margin-bottom: 6px;
  }}

  .stat-item .label {{
    font-size: 11px;
    color: #555;
    font-weight: 500;
    letter-spacing: 0.5px;
  }}

  /* 卡片 - 玻璃态暗色 */
  .card {{
    background: rgba(255, 255, 255, 0.035);
    border-radius: 18px;
    padding: 24px 28px;
    margin-bottom: 16px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(20px) saturate(180%);
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    border-left: 3px solid transparent;
    position: relative;
    overflow: hidden;
    cursor: pointer;
    display: block;
    text-decoration: none;
    color: inherit;
  }}

  .card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255, 140, 50, 0.25), transparent);
    opacity: 0;
    transition: opacity 0.3s;
  }}

  .card:hover {{
    transform: translateY(-4px) scale(1.005);
    border-left-color: #ff8c32;
    box-shadow: 0 12px 40px rgba(255, 140, 50, 0.08), 0 0 60px rgba(255, 140, 50, 0.04);
    background: rgba(255, 255, 255, 0.055);
  }}

  .card:hover::before {{
    opacity: 1;
  }}

  .card::after {{
    content: "↗";
    position: absolute;
    top: 22px;
    right: 24px;
    font-size: 16px;
    color: #333;
    transition: all 0.3s;
  }}

  .card:hover::after {{
    color: #ff8c32;
    transform: translate(3px, -3px);
  }}

  .card .card-header {{
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 10px;
    padding-right: 30px;
  }}

  .card .index {{
    flex-shrink: 0;
    width: 30px;
    height: 30px;
    background: linear-gradient(135deg, #ff8c32 0%, #ff4d00 100%);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 700;
    color: #fff;
    box-shadow: 0 2px 12px rgba(255, 140, 50, 0.3);
  }}

  .card .title {{
    font-size: 17px;
    font-weight: 600;
    color: #f0f0f4;
    line-height: 1.5;
    flex: 1;
  }}

  .card .summary {{
    font-size: 14px;
    color: #888;
    line-height: 1.7;
    margin-bottom: 14px;
    padding-left: 42px;
    padding-right: 30px;
  }}

  .card .meta {{
    display: flex;
    align-items: center;
    gap: 16px;
    padding-left: 42px;
    font-size: 12px;
    color: #555;
  }}

  .card .meta .source {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(255, 140, 50, 0.10);
    color: #ff8c32;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 500;
    border: 1px solid rgba(255, 140, 50, 0.12);
  }}

  .card .meta .time {{
    color: #444;
  }}

  /* 底部 */
  .footer {{
    text-align: center;
    margin-top: 40px;
    padding: 20px;
    color: #333;
    font-size: 12px;
  }}

  /* 响应式 */
  @media (max-width: 600px) {{
    .hero {{ padding: 48px 0 28px; }}
    .hero h1 {{ font-size: 30px; }}
    .container {{ padding: 0 14px; }}
    .card {{ padding: 18px 16px; }}
    .card .summary, .card .meta {{ padding-left: 0; }}
    .card .index {{ display: none; }}
    .card .card-header {{ padding-right: 24px; }}
    .card::after {{ right: 16px; }}
    .stats-bar {{ gap: 12px; }}
    .stat-item {{ padding: 12px 18px; min-width: 80px; }}
    .stat-item .num {{ font-size: 22px; }}
  }}
</style>
</head>
<body>

<!-- 背景光效 -->
<div class="bg-lights">
  <div class="beam-left"></div>
  <div class="beam-right"></div>
  <div class="glow-top"></div>
</div>

<div class="container">
  <!-- Hero 头部 -->
  <div class="hero">
    <div class="top-pills">
      <span class="pill pill-active">AI Daily</span>
      <span class="pill">Tech News</span>
    </div>
    <h1>探索 <span class="highlight">AI</span> 的无限可能</h1>
    <p class="date">{date_str}</p>
  </div>

  <!-- 统计条 -->
  <div class="stats-bar">
    <div class="stat-item"><div class="num">{len(news_list)}</div><div class="label">今日资讯</div></div>
    <div class="stat-item"><div class="num">{len(RSS_FEEDS)}</div><div class="label">数据来源</div></div>
    <div class="stat-item"><div class="num">{now.hour}:00</div><div class="label">实时更新</div></div>
  </div>

  <!-- 资讯列表 -->
  <div class="news-list">
    {''.join([f"""
    <a class="card" href="{item['url']}" target="_blank" rel="noopener noreferrer" title="点击查看详情">
      <div class="card-header">
        <div class="index">{i + 1}</div>
        <div class="title">{item['title']}</div>
      </div>
      <div class="summary">{item['summary']}</div>
      <div class="meta">
        <span class="source">{item['source']}</span>
        <span class="time">{item['time']}</span>
      </div>
    </a>
    """ for i, item in enumerate(news_list)])}
  </div>

  <!-- 底部 -->
  <div class="footer">
    AI 资讯 · 每日自动更新 · 数据来源：RSS 订阅源
  </div>
</div>

</body>
</html>'''

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML文件已生成 → {OUTPUT_FILE}")


def job():
    """定时执行的抓取任务（每天早上 08:00 触发）"""
    print(f"\n{'='*50}")
    print(f"[START] 定时任务触发... {datetime.now()}")
    print(f"{'='*50}")

    all_news = []
    for feed in RSS_FEEDS:
        print(f"  [FETCH] 正在抓取: {feed['name']}")
        news = fetch_news_from_rss(feed, max_items=15)
        all_news.extend(news)
        if news:
            dates = sorted(set(a['time'] for a in news))
            print(f"    → 抓到 {len(news)} 条，日期: {dates[0]} ~ {dates[-1]}")
        else:
            print(f"    → 0 条")

    print(f"\n[DATA] 共抓取 {len(all_news)} 条原始新闻")

    # 如果所有源都失败，不生成 HTML（保持上次的内容不变）
    if not all_news:
        print("[FAIL] 所有 RSS 源均抓取失败，跳过本次更新（保留旧页面）")
        return

    # 去重（按标题，取最新的那条）
    seen = {}
    for item in all_news:
        key = item['title'].strip()[:30]
        if key not in seen or item['time'] > seen[key]['time']:
            seen[key] = item
    unique_news = list(seen.values())

    # 按日期排序（最新的排最前）
    def sort_key(item):
        return item['time'] if item['time'] else '0000-00-00'
    unique_news.sort(key=sort_key, reverse=True)

    # 统计新鲜度
    today = datetime.now().strftime('%Y-%m-%d')
    fresh_count = sum(1 for n in unique_news if is_fresh(n['time'], max_days=1))
    print(f"  [NEW] 今日+昨日新闻: {fresh_count} 条 / 共 {len(unique_news)} 条去重")

    # AI 关键词过滤：只保留与 AI 相关的新闻
    ai_news = [n for n in unique_news if is_ai_related(n)]
    print(f"  [AI] 其中 AI 相关新闻: {len(ai_news)} 条")

    if not ai_news:
        print("[FAIL] 没有找到 AI 相关新闻，跳过本次更新（保留旧页面）")
        return

    # 新鲜度过滤 + 排序：今天的优先，昨天的限数量
    today_news = [n for n in ai_news if is_fresh(n['time'], max_days=0)]
    yesterday_news = [n for n in ai_news if is_fresh(n['time'], max_days=1) and not is_fresh(n['time'], max_days=0)]
    older_news = [n for n in ai_news if is_fresh(n['time'], max_days=2) and not is_fresh(n['time'], max_days=1)]

    print(f"  [TODAY] 当天新闻: {len(today_news)} 条")
    print(f"  [YEST] 昨日新闻: {len(yesterday_news)} 条")

    # 组合：今天所有 + 昨天最多10条
    limit_yesterday = max(0, 30 - len(today_news))  # 总上限40条，留给昨天的位置
    limit_yesterday = min(limit_yesterday, 10)      # 但昨天最多10条

    if len(today_news) >= 5:
        # 今天有5条以上，只补少量昨天的
        news_list = today_news + yesterday_news[:limit_yesterday]
    elif len(today_news) + len(yesterday_news) >= 5:
        # 今天不够，混合今天+昨天，但昨天最多15条
        news_list = today_news + yesterday_news[:15]
    else:
        # 实在太少，放宽到2天
        news_list = today_news + yesterday_news[:15] + older_news[:10]
        print(f"  [WARN] 当日新闻太少，放宽到2天内: {len(news_list)} 条")

    if not news_list:
        print("[FAIL] 过滤后无有效新闻，跳过本次更新（保留旧页面）")
        return

    if not news_list:
        print("[FAIL] 过滤后无有效新闻，跳过本次更新（保留旧页面）")
        return

    generate_html(news_list)
    print(f"[OK] 本次更新完成 {datetime.now()}\n")


def main():
    # 支持 --once 参数：运行一次后退出（供 GitHub Actions 使用）
    if '--once' in sys.argv:
        print(f"\n{'='*50}")
        print(f"[ONCE] 单次运行模式 (--once)")
        print(f"{'='*50}")
        job()
        return

    print(f"\n{'='*50}")
    print(f"[AI] AI 资讯自动刷新服务启动")
    print(f"[DATE] 启动时间: {datetime.now()}")
    print(f"[TIME] 定时任务: 每天 08:00 自动刷新")
    print(f"[FILE] 输出文件: {OUTPUT_FILE}")
    print(f"{'='*50}\n")

    # 启动时先立即执行一次（首次运行或手动重启时立即生效）
    job()

    # 设置定时任务：每天早上 8:00
    schedule.every().day.at("08:00").do(job)
    print("[WAIT] 定时任务已注册，程序将持续运行...")
    print("   [TIP] 保持此窗口打开，每天 08:00 会自动刷新")
    print("   [TIP] 按 Ctrl+C 可安全停止服务\n")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次，避免 CPU 空转
    except KeyboardInterrupt:
        print(f"\n[STOP] 服务已手动停止 ({datetime.now()})")
        sys.exit(0)


if __name__ == "__main__":
    main()
