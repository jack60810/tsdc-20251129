import json
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 您想爬取的目標帳號 (例如: instagram 官方帳號)
TARGET_USERNAME = "instagram"

def fetch_threads_data_no_login(username):
    """
    不使用登入，直接爬取 Threads 公開頁面
    """
    base_url = f"https://www.threads.net/@{username}"
    
    print(f"正在訪問 {base_url} ...")
    
    # 設定 headers 模擬瀏覽器
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        print(f"成功取得頁面 (狀態碼: {response.status_code})")
        
        # 解析 HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Threads 的資料通常嵌入在 JSON-LD 或 script 標籤中
        # 尋找包含 JSON 資料的 script 標籤
        posts_data = []
        
        # 方法 1: 尋找 JSON-LD 或內嵌的 JSON 資料
        scripts = soup.find_all('script', type='application/json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                # 這裡需要根據實際的 JSON 結構來解析
                # Threads 的資料結構可能在不同版本中有所不同
                if isinstance(data, dict):
                    # 嘗試找到貼文資料
                    posts = extract_posts_from_json(data)
                    if posts:
                        posts_data.extend(posts)
            except:
                continue
        
        # 方法 2: 尋找包含 __NEXT_DATA__ 或其他內嵌資料的 script
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and ('__NEXT_DATA__' in script.string or 'threads' in script.string.lower()):
                try:
                    # 嘗試提取 JSON 資料
                    json_match = re.search(r'\{.*\}', script.string, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group())
                        posts = extract_posts_from_json(data)
                        if posts:
                            posts_data.extend(posts)
                except:
                    continue
        
        # 方法 3: 如果上述方法都失敗，嘗試使用 Meta 的公開 API
        # Threads 有時會在頁面中嵌入用戶 ID，可以用來調用公開 API
        user_id = extract_user_id(soup, response.text)
        
        if user_id and not posts_data:
            print(f"找到 User ID: {user_id}，嘗試使用公開 API...")
            posts_data = fetch_from_public_api(user_id, username)
        
        if not posts_data:
            # 如果還是沒有資料，嘗試解析 HTML 結構
            posts_data = extract_posts_from_html(soup)
        
        # 儲存結果
        if posts_data:
            output_file = f"{username}_threads.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(posts_data, f, ensure_ascii=False, indent=4)
            print(f"成功抓取 {len(posts_data)} 則貼文，已存入 {output_file}")
        else:
            print("未能從頁面中提取到貼文資料")
            print("提示：Threads 可能使用動態載入，建議使用 Selenium 或 Playwright")
            # 儲存原始 HTML 供調試
            with open(f"{username}_threads_raw.html", 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"已儲存原始 HTML 到 {username}_threads_raw.html 供調試")
        
        return posts_data
        
    except requests.exceptions.RequestException as e:
        print(f"請求失敗: {e}")
        return []
    except Exception as e:
        print(f"處理過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return []


def extract_posts_from_json(data, posts_data=None):
    """
    遞迴搜尋 JSON 資料中的貼文資訊
    """
    if posts_data is None:
        posts_data = []
    
    if isinstance(data, dict):
        # 檢查是否包含貼文相關的鍵
        if 'text' in data or 'caption' in data or 'thread_items' in data:
            post = {
                'id': data.get('id') or data.get('pk'),
                'text': data.get('text') or data.get('caption', {}).get('text', '') if isinstance(data.get('caption'), dict) else str(data.get('caption', '')),
                'like_count': data.get('like_count') or data.get('num_likes'),
                'reply_count': data.get('reply_count') or data.get('num_replies'),
                'timestamp': data.get('taken_at') or data.get('created_at')
            }
            if post['text'] or post['id']:
                posts_data.append(post)
        
        # 遞迴搜尋所有值
        for value in data.values():
            extract_posts_from_json(value, posts_data)
    
    elif isinstance(data, list):
        for item in data:
            extract_posts_from_json(item, posts_data)
    
    return posts_data


def extract_user_id(soup, html_text):
    """
    從 HTML 中提取用戶 ID
    """
    # 方法 1: 從 script 標籤中尋找
    user_id_pattern = r'"user_id":\s*"?(\d+)"?'
    match = re.search(user_id_pattern, html_text)
    if match:
        return match.group(1)
    
    # 方法 2: 從 data 屬性中尋找
    user_id_pattern = r'data-user-id="(\d+)"'
    match = re.search(user_id_pattern, html_text)
    if match:
        return match.group(1)
    
    return None


def fetch_from_public_api(user_id, username):
    """
    嘗試使用 Threads 的公開 API (如果有的話)
    """
    # Threads 的公開 API 端點 (這可能需要根據實際情況調整)
    api_url = f"https://www.threads.net/api/graphql"
    
    # 這是一個範例，實際的 API 端點和參數可能需要研究
    # 有些網站會使用 GraphQL 端點，但需要特定的查詢和認證
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    # 注意：這只是範例，實際的 API 可能需要不同的參數
    # 如果 Threads 有公開的 RSS feed 或其他公開端點，可以在這裡使用
    
    return []


def extract_posts_from_html(soup):
    """
    從 HTML 結構中直接提取貼文 (備用方法)
    """
    posts_data = []
    
    # 尋找可能的貼文容器
    # Threads 的 HTML 結構可能會變化，這裡提供一個基本範例
    post_containers = soup.find_all(['article', 'div'], class_=re.compile(r'post|thread|item', re.I))
    
    for container in post_containers:
        try:
            # 嘗試提取文字內容
            text_elem = container.find(['p', 'span', 'div'], class_=re.compile(r'text|content|caption', re.I))
            text = text_elem.get_text(strip=True) if text_elem else ''
            
            if text:
                post = {
                    'text': text,
                    'id': container.get('id') or container.get('data-id'),
                    'like_count': None,
                    'reply_count': None,
                    'timestamp': None
                }
                posts_data.append(post)
        except:
            continue
    
    return posts_data


if __name__ == "__main__":
    posts = fetch_threads_data_no_login(TARGET_USERNAME)
    if posts:
        print(f"\n成功抓取 {len(posts)} 則貼文")
        print("\n前 3 則貼文預覽:")
        for i, post in enumerate(posts[:3], 1):
            print(f"\n{i}. {post.get('text', '')[:100]}...")
    else:
        print("\n未能抓取到資料。可能的原因：")
        print("1. Threads 使用 JavaScript 動態載入內容")
        print("2. 需要更複雜的解析邏輯")
        print("3. 建議使用 Selenium 或 Playwright 來處理動態內容")

