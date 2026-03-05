"""
上海国际人才网 - 人才引进信息监控脚本
每20分钟自动获取最新人才引进政策信息
使用Playwright获取动态渲染的网页内容
"""

from playwright.sync_api import sync_playwright
from datetime import datetime
import os
import json
import time

LOG_FILE = os.path.join(os.path.dirname(__file__), "log", "talent_info.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "log", "talent_latest.txt")

def ensure_log_dir():
    """确保日志目录存在"""
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

def fetch_talent_info():
    """使用Playwright获取人才引进信息"""
    url = "https://www.sh-italent.com/"
    news_items = []
    keywords = ['留学回国', '居住证', '引进人才', '户口', '落户', '实施细则', '人才工作局', '高校毕业生', '三支一扶', '海聚英才', '人才计划', '规划纲要']
    exclude_words = ['ICP备', 'EN', '首页', '新闻中心', '产业导航', '人才活动', '项目申报', '联系我们', '法律声明', '意见反馈', '区人才频道', 'prev', 'next', 'ALL']
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until='networkidle', timeout=60000)
            
            # 等待页面加载
            time.sleep(4)
            
            # 点击"人才引进"标签
            try:
                # 寻找新闻中心区域的人才引进标签
                talent_tabs = page.locator('text=人才引进').all()
                for tab in talent_tabs:
                    if tab.is_visible():
                        tab.click()
                        time.sleep(2)
                        break
            except Exception as e:
                print(f"点击人才引进标签失败: {e}")
            
            # 获取所有链接
            links = page.locator('a').all()
            
            for link in links:
                try:
                    text = link.inner_text().strip()
                    href = link.get_attribute('href') or ''
                    
                    # 排除包含排除词的内容和过短内容
                    if len(text) < 10 or any(ex in text for ex in exclude_words):
                        continue
                    
                    if any(keyword in text for keyword in keywords):
                        full_url = href if href.startswith('http') else f"https://www.sh-italent.com{href}" if href else ""
                        if not any(n['title'] == text for n in news_items):
                            news_items.append({"title": text, "url": full_url})
                except:
                    continue
            
            # 获取所有div中的文本，可能是新闻标题
            if len(news_items) < 3:
                divs = page.locator('div').all()
                for div in divs:
                    try:
                        text = div.inner_text().strip()
                        # 查找单行文本（不含换行符）且长度合适的
                        if '\n' not in text and 15 < len(text) < 80:
                            if any(keyword in text for keyword in keywords):
                                if not any(ex in text for ex in exclude_words):
                                    if not any(n['title'] == text for n in news_items):
                                        news_items.append({"title": text, "url": ""})
                    except:
                        continue
            
            browser.close()
        
        print(f"获取到 {len(news_items)} 条相关信息")
        return news_items[:20]
        
    except Exception as e:
        print(f"获取数据失败: {e}")
        return []

def load_previous_data():
    """加载之前的数据"""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"items": [], "last_update": ""}
    return {"items": [], "last_update": ""}

def save_data(items):
    """保存数据"""
    ensure_log_dir()
    data = {
        "items": items,
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_output(items, new_items):
    """保存可读输出"""
    ensure_log_dir()
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("上海国际人才网 - 人才引进信息监控\n")
        f.write(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        
        if new_items:
            f.write("【新增内容】\n")
            f.write("-" * 40 + "\n")
            for item in new_items:
                f.write(f"• {item['title']}\n")
            f.write("\n")
        
        f.write("【人才引进相关信息】\n")
        f.write("-" * 40 + "\n")
        for i, item in enumerate(items, 1):
            f.write(f"{i}. {item['title']}\n")
            if item.get('url'):
                f.write(f"   链接: {item['url']}\n")
        f.write("\n")

def main():
    """主函数"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始获取人才引进信息...")
    
    # 获取当前数据
    current_items = fetch_talent_info()
    
    if not current_items:
        print("未获取到数据")
        return
    
    # 加载之前的数据
    previous_data = load_previous_data()
    previous_titles = set(item['title'] for item in previous_data.get('items', []))
    
    # 检查新增内容
    new_items = [item for item in current_items if item['title'] not in previous_titles]
    
    if new_items:
        print(f"发现 {len(new_items)} 条新内容:")
        for item in new_items:
            print(f"  - {item['title']}")
    else:
        print("没有新内容")
    
    # 保存数据
    save_data(current_items)
    save_output(current_items, new_items)
    
    print(f"数据已保存到: {OUTPUT_FILE}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 完成")

if __name__ == "__main__":
    main()
