# Threads 資料抓取工具

本目錄包含多種抓取 Threads 資料的方法，從需要登入到完全不需要登入的版本。

## 📁 檔案說明

### 1. `grab_data_threads.py` - 使用 API（需要登入）
- **優點**: 資料結構完整、穩定
- **缺點**: 需要 Instagram/Threads 帳號登入
- **使用場景**: 需要完整資料（按讚數、回覆數等）

### 2. `grab_data_threads_no_login.py` - 簡單網頁爬取（不需要登入）
- **優點**: 不需要登入、簡單快速
- **缺點**: Threads 使用 JavaScript 動態載入，可能無法取得資料
- **使用場景**: 快速測試或 Threads 頁面結構簡單時

### 3. `grab_data_threads_selenium.py` - 使用 Selenium（不需要登入）
- **優點**: 可以處理 JavaScript 動態內容、不需要登入
- **缺點**: 需要安裝 Chrome 和 ChromeDriver、速度較慢
- **使用場景**: 需要處理動態載入的內容

### 4. `grab_data_threads_playwright.py` - 使用 Playwright（不需要登入）⭐ 推薦
- **優點**: 可以處理 JavaScript、比 Selenium 更快更穩定、不需要登入
- **缺點**: 首次使用需要下載瀏覽器
- **使用場景**: 最佳選擇，推薦使用

## 🚀 快速開始

### 方法 1: 使用 Playwright（推薦）

```bash
# 安裝依賴
pip install playwright beautifulsoup4

# 安裝瀏覽器（首次使用）
playwright install chromium

# 運行腳本
python grab_data_threads_playwright.py
```

### 方法 2: 使用 Selenium

```bash
# 安裝依賴
pip install selenium beautifulsoup4

# 安裝 ChromeDriver (macOS)
brew install chromedriver

# 運行腳本
python grab_data_threads_selenium.py
```

### 方法 3: 簡單網頁爬取

```bash
# 安裝依賴
pip install requests beautifulsoup4

# 運行腳本
python grab_data_threads_no_login.py
```

### 方法 4: 使用 API（需要登入）

```bash
# 已在虛擬環境中安裝依賴
source venv/bin/activate

# 修改腳本中的 MY_USERNAME 和 MY_PASSWORD
# 然後運行
python grab_data_threads.py
```

## ⚙️ 設定參數

在每個腳本中，您可以修改以下參數：

```python
TARGET_USERNAME = "instagram"  # 要抓取的帳號名稱
max_posts = 10                 # 最多抓取幾則貼文（僅適用於 Selenium/Playwright）
headless = True                # 是否使用無頭模式（隱藏瀏覽器視窗）
```

## 📝 輸出格式

所有腳本都會產生 JSON 檔案，格式如下：

```json
[
  {
    "id": "貼文 ID",
    "text": "貼文內容",
    "like_count": 按讚數,
    "reply_count": 回覆數,
    "timestamp": 時間戳記
  }
]
```

## ⚠️ 注意事項

1. **遵守使用條款**: 請確保您的爬取行為符合 Threads 的使用條款
2. **請求頻率**: 避免過於頻繁的請求，以免被封鎖
3. **資料準確性**: 網頁爬取可能因為頁面結構變更而失效
4. **動態內容**: Threads 使用 JavaScript 動態載入，簡單的 requests 可能無法取得資料

## 🔧 疑難排解

### Playwright 無法啟動瀏覽器
```bash
playwright install chromium
```

### Selenium 找不到 ChromeDriver
```bash
# macOS
brew install chromedriver

# 或手動下載並設定 PATH
```

### 無法取得資料
1. 檢查目標帳號是否存在
2. 嘗試將 `headless=False` 來查看瀏覽器行為
3. Threads 可能更新了頁面結構，需要調整選擇器
4. 檢查是否有反爬蟲機制（驗證碼等）

## 📚 相關資源

- [Playwright 文檔](https://playwright.dev/python/)
- [Selenium 文檔](https://www.selenium.dev/documentation/)
- [BeautifulSoup 文檔](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

