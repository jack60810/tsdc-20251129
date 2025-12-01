import json
import time
import asyncio
from threads_api.src.threads_api import ThreadsAPI

# 設定您的免洗帳號資訊 (建議使用環境變數，不要直接寫死在程式碼中以免外洩)
# 如果該套件支援不登入瀏覽，可嘗試註解掉登入部分，但目前 Meta 幾乎強制要求登入
MY_USERNAME = "您的免洗帳號帳號"
MY_PASSWORD = "您的免洗帳號密碼"

# 您想爬取的目標帳號 (例如: instagram 官方帳號)
TARGET_USERNAME = "instagram"

async def fetch_threads_data():
    api = ThreadsAPI()

    print(f"正在登入帳號: {MY_USERNAME} ...")
    try:
        # 登入 (注意：這一步最容易觸發驗證挑戰，如 2FA)
        await api.login(MY_USERNAME, MY_PASSWORD)
        print("登入成功！")
    except Exception as e:
        print(f"登入失敗，請檢查帳號狀態或網路。錯誤: {e}")
        return

    try:
        # 1. 取得目標帳號的 User ID (Threads 內部使用的是數字 ID)
        print(f"正在取得 {TARGET_USERNAME} 的 User ID...")
        user_id = await api.get_user_id_from_username(TARGET_USERNAME)
        
        if not user_id:
            print("找不到該使用者 ID")
            return
            
        print(f"目標 User ID: {user_id}")

        # 2. 抓取該用戶的貼文 (Threads)
        print("正在抓取貼文...")
        # Get user threads 通常會回傳一個列表
        threads = await api.get_user_threads(user_id)
        
        # 3. 解析並儲存資料
        posts_data = []
        
        # 注意：回傳的資料結構很複雜，這裡簡化處理
        # threads 可能是一個 Threads 物件，需要檢查實際結構
        if hasattr(threads, 'threads'):
            thread_list = threads.threads
        elif isinstance(threads, list):
            thread_list = threads
        else:
            thread_list = [threads]
        
        for item in thread_list:
            # 這是概略結構，實際欄位名稱需視 API 版本而定
            # 通常資料藏在 thread_items 裡面
            if hasattr(item, 'thread_items'):
                thread_items = item.thread_items
            elif isinstance(item, dict):
                thread_items = item.get('thread_items', [])
            else:
                thread_items = [item]
            
            for post in thread_items:
                if hasattr(post, 'post'):
                    post_content = post.post
                elif isinstance(post, dict):
                    post_content = post.get('post', post)
                else:
                    post_content = post
                
                if hasattr(post_content, 'caption'):
                    caption = post_content.caption
                    if hasattr(caption, 'text'):
                        text = caption.text
                    else:
                        text = str(caption) if caption else ''
                elif isinstance(post_content, dict):
                    caption = post_content.get('caption', {})
                    text = caption.get('text', '') if isinstance(caption, dict) else str(caption) if caption else ''
                else:
                    text = str(post_content) if post_content else ''
                
                if text:
                    data = {
                        'id': getattr(post_content, 'id', None) if hasattr(post_content, 'id') else (post_content.get('id') if isinstance(post_content, dict) else None),
                        'text': text,
                        'like_count': getattr(post_content, 'like_count', None) if hasattr(post_content, 'like_count') else (post_content.get('like_count') if isinstance(post_content, dict) else None),
                        'reply_count': getattr(post_content, 'reply_count', None) if hasattr(post_content, 'reply_count') else (post_content.get('reply_count') if isinstance(post_content, dict) else None),
                        'timestamp': getattr(post_content, 'taken_at', None) if hasattr(post_content, 'taken_at') else (post_content.get('taken_at') if isinstance(post_content, dict) else None)
                    }
                    posts_data.append(data)

        # 4. 存成 JSON 檔
        output_file = f"{TARGET_USERNAME}_threads.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(posts_data, f, ensure_ascii=False, indent=4)
            
        print(f"成功抓取 {len(posts_data)} 則貼文，已存入 {output_file}")

    except Exception as e:
        print(f"抓取過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fetch_threads_data())