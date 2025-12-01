import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

# 您想爬取的目標帳號
TARGET_USERNAME = "instagram"

def setup_driver(headless=True):
    """
    設定 Selenium WebDriver
    """
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"無法啟動 Chrome: {e}")
        print("請確保已安裝 Chrome 和 ChromeDriver")
        print("安裝方法: brew install chromedriver (macOS)")
        return None


def fetch_threads_data_selenium(username, max_posts=10, headless=True):
    """
    使用 Selenium 爬取 Threads 資料（不需要登入）
    """
    url = f"https://www.threads.net/@{username}"
    
    print(f"正在訪問 {url} ...")
    
    driver = setup_driver(headless=headless)
    if not driver:
        return []
    
    posts_data = []
    
    try:
        driver.get(url)
        print("等待頁面載入...")
        
        # 等待頁面載入
        time.sleep(5)
        
        # 嘗試滾動頁面以載入更多內容
        print("滾動頁面以載入更多貼文...")
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        # 取得頁面原始碼
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 方法 1: 從頁面中提取 JSON 資料
        posts_data = extract_posts_from_page_source(page_source)
        
        # 方法 2: 如果方法 1 失敗，嘗試從 HTML 元素中提取
        if not posts_data:
            posts_data = extract_posts_from_elements(driver)
        
        # 方法 3: 如果還是沒有，嘗試從 script 標籤中提取
        if not posts_data:
            posts_data = extract_posts_from_scripts(soup)
        
        # 限制貼文數量
        if len(posts_data) > max_posts:
            posts_data = posts_data[:max_posts]
        
        # 儲存結果
        if posts_data:
            output_file = f"{username}_threads.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(posts_data, f, ensure_ascii=False, indent=4)
            print(f"成功抓取 {len(posts_data)} 則貼文，已存入 {output_file}")
        else:
            print("未能從頁面中提取到貼文資料")
            # 儲存頁面原始碼供調試
            with open(f"{username}_threads_debug.html", 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"已儲存頁面原始碼到 {username}_threads_debug.html 供調試")
        
    except Exception as e:
        print(f"抓取過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
    
    return posts_data


def extract_posts_from_page_source(page_source):
    """
    從頁面原始碼中提取 JSON 資料
    """
    posts_data = []
    
    # 尋找 __NEXT_DATA__ 或其他內嵌的 JSON
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
    
    # 尋找所有可能的 JSON 資料
    json_pattern = r'\{[^{}]*"text"[^{}]*\}'
    matches = re.finditer(json_pattern, page_source)
    for match in matches:
        try:
            data = json.loads(match.group())
            if 'text' in data or 'caption' in data:
                post = {
                    'id': data.get('id') or data.get('pk'),
                    'text': data.get('text') or data.get('caption', {}).get('text', '') if isinstance(data.get('caption'), dict) else str(data.get('caption', '')),
                    'like_count': data.get('like_count') or data.get('num_likes'),
                    'reply_count': data.get('reply_count') or data.get('num_replies'),
                    'timestamp': data.get('taken_at') or data.get('created_at')
                }
                if post['text']:
                    posts_data.append(post)
        except:
            continue
    
    return posts_data


def extract_posts_from_elements(driver):
    """
    從 HTML 元素中直接提取貼文
    """
    posts_data = []
    
    try:
        # 等待貼文元素載入
        wait = WebDriverWait(driver, 10)
        
        # 嘗試不同的選擇器（Threads 的結構可能會變化）
        selectors = [
            'article',
            '[role="article"]',
            'div[data-testid]',
            '.thread-item',
            '.post'
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"找到 {len(elements)} 個可能的貼文元素 (使用選擇器: {selector})")
                    
                    for elem in elements[:10]:  # 限制前 10 個
                        try:
                            text = elem.text
                            if text and len(text) > 20:  # 過濾太短的文字
                                post = {
                                    'text': text,
                                    'id': elem.get_attribute('id') or elem.get_attribute('data-id'),
                                    'like_count': None,
                                    'reply_count': None,
                                    'timestamp': None
                                }
                                posts_data.append(post)
                        except:
                            continue
                    
                    if posts_data:
                        break
            except:
                continue
                
    except Exception as e:
        print(f"從元素提取時發生錯誤: {e}")
    
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
                        posts_data.append({
                            'id': data.get('id'),
                            'text': data.get('text'),
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
            if text:
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
    print("使用 Selenium 爬取 Threads 資料（不需要登入）")
    print("=" * 50)
    
    posts = fetch_threads_data_selenium(TARGET_USERNAME, max_posts=10, headless=True)
    
    if posts:
        print(f"\n成功抓取 {len(posts)} 則貼文")
        print("\n前 3 則貼文預覽:")
        for i, post in enumerate(posts[:3], 1):
            text = post.get('text', '')[:100]
            print(f"\n{i}. {text}...")
    else:
        print("\n未能抓取到資料")
        print("提示：")
        print("1. 確保已安裝 Chrome 和 ChromeDriver")
        print("2. 嘗試將 headless=False 來查看瀏覽器行為")
        print("3. Threads 可能更新了頁面結構，需要調整選擇器")

