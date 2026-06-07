import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import schedule
import time
import sys

# 国内 AI 资讯 RSS 源（都是官方提供的，稳定可靠）
RSS_FEEDS = [
    {'name': '36氪', 'url': 'https://36kr.com/feed'},
    {'name': '少数派', 'url': 'https://sspai.com/feed'},
    {'name': 'IT之家', 'url': 'https://www.ithome.com/rss'},
    {'name': '爱范儿', 'url': 'https://www.ifanr.com/feed'},
    {'name': '小众软件', 'url': 'https://feeds.appinn.com/appinns/'},
]

# 输出文件路径
OUTPUT_FILE = r'E:\python的项目\新闻项目\index.html'


def fetch_news_from_rss(feed):
    """从 RSS 订阅源抓取新闻"""
    try:
        response = requests.get(feed['url'], timeout=10)
        response.encoding = 'utf-8'
        root = ET.fromstring(response.text)

        articles = []
        # RSS 的标准结构是 .//item
        for item in root.findall('.//item')[:10]:
            title = item.find('title').text if item.find('title') is not None else ''
            link = item.find('link').text if item.find('link') is not None else ''
            description = item.find('description').text if item.find('description') is not None else ''
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''

            articles.append({
                'title': title,
                'url': link,
                'summary': description[:200] if description else '',
                'source': feed['name'],
                'time': pub_date[:10] if pub_date else datetime.now().strftime('%Y-%m-%d')
            })
        return articles
    except Exception as e:
        print(f"抓取 {feed['name']} RSS 失败: {e}")
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
    <div class="stat-item"><div class="num">RSS</div><div class="label">数据来源</div></div>
    <div class="stat-item"><div class="num">{now.hour}:00</div><div class="label">实时更新</div></div>
  </div>

  <!-- 资讯列表 -->
  <div class="news-list">
    {''.join([f'''
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
    ''' for i, item in enumerate(news_list)])}
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
        print(f"  正在抓取: {feed['name']}")
        news = fetch_news_from_rss(feed)
        all_news.extend(news)
        print(f"    → 抓到 {len(news)} 条")

    print(f"\n📊 共抓取 {len(all_news)} 条新闻")

    if all_news:
        # 去重（按标题）
        seen = set()
        unique_news = []
        for item in all_news:
            if item['title'] not in seen:
                seen.add(item['title'])
                unique_news.append(item)
        news_list = unique_news[:20]
    else:
        news_list = []

    generate_html(news_list)
    print(f"✅ 本次更新完成 {datetime.now()}\n")


def main():
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