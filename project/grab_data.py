import scrapetube
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_RECENT
import pandas as pd
import time

def get_channel_comments(channel_url, video_limit=5, comments_per_video=50):
    """
    抓取指定頻道最新影片的留言
    """
    print(f"正在搜尋頻道: {channel_url} 的最新影片...")
    
    # 1. 獲取頻道影片列表 (使用 scrapetube)
    videos = scrapetube.get_channel(channel_url=channel_url, limit=video_limit)
    
    downloader = YoutubeCommentDownloader()
    all_data = []

    video_count = 0
    for video in videos:
        video_count += 1
        video_id = video['videoId']
        # 嘗試獲取標題，不同來源結構可能不同，這裡做簡單處理
        title = video.get('title', {}).get('runs', [{}])[0].get('text', 'No Title')
        
        print(f"[{video_count}/{video_limit}] 正在抓取影片: {title} (ID: {video_id})")
        
        try:
            # 2. 抓取該影片的留言 (使用 youtube-comment-downloader)
            # 使用 SORT_BY_RECENT 抓取最新留言，或移除參數抓取熱門留言
            comments = downloader.get_comments_from_url(
                f'https://www.youtube.com/watch?v={video_id}', 
                sort_by=SORT_BY_RECENT
            )
            
            count = 0
            for comment in comments:
                if count >= comments_per_video:
                    break
                
                # 3. 整理需要的欄位
                # 注意：非官方 API 方式，"回覆數"有時可能抓不到或為 0，視 YouTube 頁面結構而定
                comment_data = {
                    'Video_Title': title,
                    'Video_ID': video_id,
                    'Comment_ID': comment.get('cid'),
                    'User_ID': comment.get('channel'), # 這是使用者的 Channel ID
                    'User_Name': comment.get('author'),
                    'Content': comment.get('text'), # 留言內容
                    'Timestamp': comment.get('time'), # 發布時間 (例如: "2 hours ago")
                    'Likes': comment.get('votes'), # 按讚數
                    # 非官方 API 的 Reply 數通常需要進一步解析，這裡先抓是否有 reply 標記
                    'Is_Reply': comment.get('reply', False) 
                }
                all_data.append(comment_data)
                count += 1
                
        except Exception as e:
            print(f"抓取影片 {video_id} 時發生錯誤: {e}")
            continue

    # 4. 轉換為 DataFrame 並儲存
    df = pd.DataFrame(all_data)
    return df

# --- 設定參數 ---
CHANNEL_URL = "https://www.youtube.com/@tainanjosh"
VIDEO_LIMIT = 5          # 抓取最新的 5 部影片
COMMENTS_PER_VIDEO = 100 # 每部影片抓取多少則留言 (設多一點以免資料不夠)

# --- 執行主程式 ---
if __name__ == "__main__":
    df_comments = get_channel_comments(CHANNEL_URL, VIDEO_LIMIT, COMMENTS_PER_VIDEO)
    
    # 預覽資料
    print(f"抓取完成！共取得 {len(df_comments)} 則留言。")
    print(df_comments.head())
    
    # 存成 CSV 檔，Excel 打開不會亂碼 (utf-8-sig)
    filename = "tainanjosh_comments.csv"
    df_comments.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"檔案已儲存為: {filename}")