import json
import time
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# 您想爬取的目標帳號
TARGET_USERNAME = "instagram"

def fetch_threads_data_playwright(username, max_posts=10, headless=True):
    """
    使用 Playwright 爬取 Threads 資料（不需要登入）
    Playwright 比 Selenium 更快且更穩定
    """
    url = f"https://www.threads.net/@{username}"
    
    print(f"正在訪問 {url} ...")
    
    posts_data = []
    
    with sync_playwright() as p:
        try:
            # 啟動瀏覽器
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            print("載入頁面...")
            page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            # 等待頁面載入
            time.sleep(3)
            
            # 滾動頁面以載入更多內容
            print("滾動頁面以載入貼文...")
            # 增加滾動次數以載入更多貼文（Threads 可能需要更多滾動）
            scroll_count = max(30, max_posts // 3)  # 根據需要的貼文數量調整滾動次數
            posts_data = []
            seen_texts = set()
            
            for i in range(scroll_count):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(3)  # 增加等待時間讓內容載入
                print(f"已滾動 {i+1}/{scroll_count} 次...")
                
                # 每次滾動後嘗試提取新資料
                page_source = page.content()
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # 方法 1: 從 HTML 元素中提取（最可靠）
                new_posts = extract_posts_from_elements_playwright(page, max_posts)
                for post in new_posts:
                    text = post.get('text', '').strip()
                    if text and text not in seen_texts and len(text) > 10:
                        seen_texts.add(text)
                        posts_data.append(post)
                
                # 如果已經有足夠的資料，可以提前結束
                if len(posts_data) >= max_posts:
                    print(f"已收集到 {len(posts_data)} 則貼文，停止滾動")
                    break
            
            # 如果元素提取沒有足夠資料，嘗試從 JSON 中提取
            if len(posts_data) < max_posts:
                print("嘗試從頁面 JSON 資料中提取...")
                page_source = page.content()
                soup = BeautifulSoup(page_source, 'html.parser')
                
                json_posts = extract_posts_from_page_source(page_source)
                for post in json_posts:
                    text = post.get('text', '').strip()
                    if text and text not in seen_texts and len(text) > 10:
                        seen_texts.add(text)
                        posts_data.append(post)
                        if len(posts_data) >= max_posts:
                            break
                
                # 方法 3: 從 script 標籤中提取
                if len(posts_data) < max_posts:
                    script_posts = extract_posts_from_scripts(soup)
                    for post in script_posts:
                        text = post.get('text', '').strip()
                        if text and text not in seen_texts and len(text) > 10:
                            seen_texts.add(text)
                            posts_data.append(post)
                            if len(posts_data) >= max_posts:
                                break
            
            # 限制貼文數量
            if len(posts_data) > max_posts:
                posts_data = posts_data[:max_posts]
            
            # 儲存結果
            if posts_data:
                output_file = f"{username}_threads.json"
                # 清理資料中的 Unicode 問題
                cleaned_posts = []
                for post in posts_data:
                    try:
                        text = post.get('text', '')
                        # 確保文字可以正確編碼
                        text = text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
                        post['text'] = text
                        cleaned_posts.append(post)
                    except:
                        continue
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(cleaned_posts, f, ensure_ascii=False, indent=4)
                print(f"成功抓取 {len(posts_data)} 則貼文，已存入 {output_file}")
            else:
                print("未能從頁面中提取到貼文資料")
                # 儲存頁面原始碼供調試
                with open(f"{username}_threads_debug.html", 'w', encoding='utf-8') as f:
                    f.write(page_source)
                print(f"已儲存頁面原始碼到 {username}_threads_debug.html 供調試")
            
            browser.close()
            
        except Exception as e:
            print(f"抓取過程中發生錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    return posts_data


def extract_posts_from_page_source(page_source):
    """
    從頁面原始碼中提取 JSON 資料
    """
    posts_data = []
    
    # 尋找各種可能的 JSON 資料格式
    patterns = [
        r'__NEXT_DATA__\s*=\s*({.+?});',
        r'window\.__initialData__\s*=\s*({.+?});',
        r'"thread_items":\s*(\[.+?\])',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, page_source, re.DOTALL)
        for match in matches:
            try:
                json_str = match.group(1)
                data = json.loads(json_str)
                posts = extract_posts_from_json(data)
                if posts:
                    posts_data.extend(posts)
            except:
                continue
    
    # 更積極地尋找所有包含 "text" 的 JSON 物件
    # 尋找所有可能的貼文文字
    text_pattern = r'"text"\s*:\s*"((?:[^"\\]|\\.)+)"'
    text_matches = re.finditer(text_pattern, page_source)
    for match in text_matches:
        try:
            text = match.group(1)
            # 解碼 Unicode 轉義序列，處理錯誤
            try:
                text = text.encode('utf-8').decode('unicode_escape')
            except:
                # 如果解碼失敗，嘗試其他方法
                try:
                    text = text.encode('latin-1').decode('utf-8', errors='ignore')
                except:
                    pass
            
            # 清理代理對（surrogate pairs）問題
            text = text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
            
            # 過濾太短或明顯不是貼文的文字
            if len(text) > 15 and not text.startswith('http') and 'text' not in text.lower()[:10]:
                posts_data.append({
                    'text': text,
                    'id': None,
                    'like_count': None,
                    'reply_count': None,
                    'timestamp': None
                })
        except:
            continue
    
    # 去重（基於文字內容）
    seen = set()
    unique_posts = []
    for post in posts_data:
        text = post.get('text', '').strip()
        # 使用文字的前 100 個字符作為唯一標識
        text_key = text[:100] if len(text) > 100 else text
        if text and text_key not in seen and len(text) > 15:
            seen.add(text_key)
            unique_posts.append(post)
    
    return unique_posts


def extract_posts_from_elements_playwright(page, max_posts=100):
    """
    使用 Playwright 從 HTML 元素中提取貼文
    """
    posts_data = []
    
    try:
        # 嘗試不同的選擇器（Threads 的常見結構）
        selectors = [
            'article',
            '[role="article"]',
            'div[data-testid*="post"]',
            'div[class*="thread"]',
            'div[class*="post"]',
            'div[class*="Thread"]',
            'div[class*="Post"]',
            'div[dir="auto"]',  # Threads 經常使用這個屬性
        ]
        
        all_elements = []
        for selector in selectors:
            try:
                elements = page.query_selector_all(selector)
                if elements:
                    print(f"找到 {len(elements)} 個可能的貼文元素 (使用選擇器: {selector})")
                    all_elements.extend(elements)
            except:
                continue
        
        # 去重元素（基於位置或 ID）
        unique_elements = []
        seen_positions = set()
        for elem in all_elements:
            try:
                elem_id = elem.get_attribute('id') or ''
                # 使用元素的文字前 50 個字符作為唯一標識
                text_preview = elem.inner_text()[:50] if elem.inner_text() else ''
                unique_key = f"{elem_id}_{text_preview}"
                
                if unique_key not in seen_positions:
                    seen_positions.add(unique_key)
                    unique_elements.append(elem)
            except:
                continue
        
        print(f"去重後共有 {len(unique_elements)} 個唯一元素")
        
        # 提取貼文內容
        for elem in unique_elements[:max_posts * 2]:  # 多提取一些以防過濾
            try:
                text = elem.inner_text()
                if text and len(text.strip()) > 15:  # 過濾太短的文字
                    # 清理文字（移除多餘空白）
                    cleaned_text = ' '.join(text.split())
                    post = {
                        'text': cleaned_text,
                        'id': elem.get_attribute('id') or elem.get_attribute('data-id'),
                        'like_count': None,
                        'reply_count': None,
                        'timestamp': None
                    }
                    posts_data.append(post)
            except:
                continue
                
    except Exception as e:
        print(f"從元素提取時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    return posts_data


def extract_posts_from_scripts(soup):
    """
    從 script 標籤中提取資料
    """
    posts_data = []
    
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            # 尋找包含貼文資料的 JSON
            json_matches = re.finditer(r'\{[^{}]*"text"[^{}]*\}', script.string)
            for match in json_matches:
                try:
                    data = json.loads(match.group())
                    if 'text' in data:
                        text = data.get('text', '')
                        if len(text) > 20:
                            posts_data.append({
                                'id': data.get('id'),
                                'text': text,
                                'like_count': data.get('like_count'),
                                'reply_count': data.get('reply_count'),
                                'timestamp': data.get('timestamp')
                            })
                except:
                    continue
    
    return posts_data


def extract_posts_from_json(data, posts_data=None):
    """
    遞迴搜尋 JSON 資料中的貼文資訊
    """
    if posts_data is None:
        posts_data = []
    
    if isinstance(data, dict):
        if 'text' in data or ('caption' in data and isinstance(data.get('caption'), dict) and 'text' in data.get('caption')):
            text = data.get('text') or (data.get('caption', {}).get('text', '') if isinstance(data.get('caption'), dict) else '')
            if text and len(text) > 20:
                post = {
                    'id': data.get('id') or data.get('pk'),
                    'text': text,
                    'like_count': data.get('like_count') or data.get('num_likes'),
                    'reply_count': data.get('reply_count') or data.get('num_replies'),
                    'timestamp': data.get('taken_at') or data.get('created_at')
                }
                posts_data.append(post)
        
        for value in data.values():
            extract_posts_from_json(value, posts_data)
    
    elif isinstance(data, list):
        for item in data:
            extract_posts_from_json(item, posts_data)
    
    return posts_data


if __name__ == "__main__":
    print("使用 Playwright 爬取 Threads 資料（不需要登入）")
    print("=" * 50)
    print("注意：首次運行會自動下載瀏覽器，可能需要一些時間")
    print()
    
    posts = fetch_threads_data_playwright(TARGET_USERNAME, max_posts=100, headless=True)
    
    if posts:
        print(f"\n成功抓取 {len(posts)} 則貼文")
        print("\n前 3 則貼文預覽:")
        for i, post in enumerate(posts[:3], 1):
            try:
                text = post.get('text', '')[:100]
                # 安全地處理 Unicode
                text = text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
                print(f"\n{i}. {text}...")
            except:
                print(f"\n{i}. [無法顯示文字]")
    else:
        print("\n未能抓取到資料")
        print("提示：")
        print("1. 確保已安裝 Playwright: pip install playwright")
        print("2. 安裝瀏覽器: playwright install chromium")
        print("3. 嘗試將 headless=False 來查看瀏覽器行為")

