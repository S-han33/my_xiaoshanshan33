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
]

# 输出文件路径（相对路径，兼容本地和 GitHub Actions）
OUTPUT_FILE = './index.html'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*;q=0.9',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
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
            
            # 防御：检查返回的是否为 XML，防止拿到 HTML 错误页
            text_start = response.text.strip()[:200].lower()
            if not (text_start.startswith('<?xml') or '<rss' in text_start or '<feed' in text_start):
                raise ValueError(f"返回内容不是 XML: {text_start[:50]}")
            
            response.encoding = 'utf-8'
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
            print(f"  ⚠ 抓取 {feed['name']} 失败 (尝试 {attempt+1}/{max_retries}): {str(e)[:80]}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避：1s, 2s, 4s
            else:
                return []
    return []


def generate_html(news_list):
    """生成 HTML"""
    if not news_list:
        print("警告：没有新闻数据，生成空白页面")
        # 如果没抓到新闻，放几条示例数据占位
        news_list = [{
            'title': '示例：请检查网络或 RSS 源',
            'url': '#',
            'summary': '目前没有抓取到新闻，请确认网络连接或稍后重试',
            'source': '系统提示',
            'time': datetime.now().strftime('%Y-%m-%d')
        }]

    now = datetime.now()
    week_days = ['一', '二', '三', '四', '五', '六', '日']
    w = week_days[now.weekday()]
    date_str = f'{now.year} 年 {now.month:02d} 月 {now.day:02d} 日  星期{w}'

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
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e9f2 100%);
    color: #1a1a2e;
    min-height: 100vh;
    padding: 40px 20px;
  }}

  .container {{
    max-width: 800px;
    margin: 0 auto;
  }}

  /* 头部 */
  .header {{
    text-align: center;
    margin-bottom: 40px;
  }}

  .header .logo {{
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
  }}

  .header .logo-icon {{
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    color: #fff;
    font-weight: bold;
  }}

  .header h1 {{
    font-size: 28px;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }}

  .header .date {{
    font-size: 14px;
    color: #888;
    letter-spacing: 1px;
  }}

  /* 统计条 */
  .stats-bar {{
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-bottom: 30px;
    flex-wrap: wrap;
  }}

  .stat-item {{
    text-align: center;
  }}

  .stat-item .num {{
    font-size: 26px;
    font-weight: 700;
    color: #667eea;
  }}

  .stat-item .label {{
    font-size: 12px;
    color: #999;
    margin-top: 2px;
  }}

  /* 卡片 */
  .card {{
    background: #fff;
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    transition: transform 0.2s, box-shadow 0.2s, border-left-color 0.2s;
    border-left: 4px solid transparent;
    position: relative;
    overflow: hidden;
    cursor: pointer;
    display: block;
    text-decoration: none;
    color: inherit;
  }}

  .card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(102,126,234,0.2);
    border-left-color: #667eea;
  }}

  .card::after {{
    content: "↗";
    position: absolute;
    top: 20px;
    right: 24px;
    font-size: 16px;
    color: #ccc;
    transition: color 0.2s, transform 0.2s;
  }}

  .card:hover::after {{
    color: #667eea;
    transform: translate(3px, -3px);
  }}

  .card .card-header {{
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 8px;
    padding-right: 30px;
  }}

  .card .index {{
    flex-shrink: 0;
    width: 28px;
    height: 28px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 700;
    color: #fff;
  }}

  .card .title {{
    font-size: 17px;
    font-weight: 600;
    color: #1a1a2e;
    line-height: 1.5;
    flex: 1;
  }}

  .card .summary {{
    font-size: 14px;
    color: #666;
    line-height: 1.7;
    margin-bottom: 12px;
    padding-left: 40px;
    padding-right: 30px;
  }}

  .card .meta {{
    display: flex;
    align-items: center;
    gap: 16px;
    padding-left: 40px;
    font-size: 12px;
    color: #aaa;
  }}

  .card .meta .source {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #f0f3ff;
    color: #667eea;
    padding: 3px 10px;
    border-radius: 20px;
    font-weight: 500;
  }}

  .card .meta .time {{
    color: #bbb;
  }}

  /* 底部 */
  .footer {{
    text-align: center;
    margin-top: 40px;
    padding: 20px;
    color: #bbb;
    font-size: 12px;
  }}

  /* 响应式 */
  @media (max-width: 600px) {{
    .container {{ padding: 0 8px; }}
    .card {{ padding: 18px 16px; }}
    .card .summary, .card .meta {{ padding-left: 0; }}
    .card .index {{ display: none; }}
    .card .card-header {{ padding-right: 24px; }}
    .card::after {{ right: 16px; }}
    .header h1 {{ font-size: 22px; }}
  }}
</style>
</head>
<body>

<div class="container">
  <!-- 头部 -->
  <div class="header">
    <div class="logo">
      <div class="logo-icon">AI</div>
    </div>
    <h1>今日 AI 资讯</h1>
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
    print(f"🌟 定时任务触发... {datetime.now()}")
    print(f"{'='*50}")

    all_news = []
    for feed in RSS_FEEDS:
        print(f"  📡 正在抓取: {feed['name']}")
        news = fetch_news_from_rss(feed, max_items=15)
        all_news.extend(news)
        if news:
            dates = sorted(set(a['time'] for a in news))
            print(f"    → 抓到 {len(news)} 条，日期: {dates[0]} ~ {dates[-1]}")
        else:
            print(f"    → 0 条")

    print(f"\n📊 共抓取 {len(all_news)} 条原始新闻")

    # 如果所有源都失败，不生成 HTML（保持上次的内容不变）
    if not all_news:
        print("❌ 所有 RSS 源均抓取失败，跳过本次更新（保留旧页面）")
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
    print(f"  🆕 今日+昨日新闻: {fresh_count} 条 / 共 {len(unique_news)} 条去重")

    # 最终取前 20 条（但尽量让新鲜内容排前面）
    news_list = unique_news[:20]

    generate_html(news_list)
    print(f"✅ 本次更新完成 {datetime.now()}\n")


def main():
    # 支持 --once 参数：运行一次后退出（供 GitHub Actions 使用）
    if '--once' in sys.argv:
        print(f"\n{'='*50}")
        print(f"🔁 单次运行模式 (--once)")
        print(f"{'='*50}")
        job()
        return

    print(f"\n{'='*50}")
    print(f"🤖 AI 资讯自动刷新服务启动")
    print(f"📅 启动时间: {datetime.now()}")
    print(f"⏰ 定时任务: 每天 08:00 自动刷新")
    print(f"📁 输出文件: {OUTPUT_FILE}")
    print(f"{'='*50}\n")

    # 启动时先立即执行一次（首次运行或手动重启时立即生效）
    job()

    # 设置定时任务：每天早上 8:00
    schedule.every().day.at("08:00").do(job)
    print("⏳ 定时任务已注册，程序将持续运行...")
    print("   💡 保持此窗口打开，每天 08:00 会自动刷新")
    print("   💡 按 Ctrl+C 可安全停止服务\n")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次，避免 CPU 空转
    except KeyboardInterrupt:
        print(f"\n🛑 服务已手动停止 ({datetime.now()})")
        sys.exit(0)


if __name__ == "__main__":
    main()
