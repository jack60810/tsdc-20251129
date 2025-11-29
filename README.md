# TSDC 2025 專案說明

本專案為「企業實戰工作坊 - DATA & AI」的相關資料與簡報內容。

## 📁 專案結構

### `/project/` - 資料抓取專案

此資料夾包含 YouTube 留言資料抓取的相關程式與資料。

- **`grab_data.py`**: Python 資料抓取腳本
  - 使用 `scrapetube` 與 `youtube-comment-downloader` 套件
  - 功能：從指定 YouTube 頻道（預設為 @tainanjosh）抓取最新影片的留言
  - 可設定參數：
    - `VIDEO_LIMIT`: 抓取最新影片數量（預設：5 部）
    - `COMMENTS_PER_VIDEO`: 每部影片抓取的留言數（預設：100 則）
  - 輸出欄位包含：影片標題、影片 ID、留言 ID、使用者資訊、留言內容、時間戳記、按讚數等

- **`tainanjosh_comments.csv`**: 抓取後的留言資料集
  - CSV 格式，使用 UTF-8-sig 編碼（Excel 開啟不會亂碼）
  - 包含從 YouTube 頻道抓取的留言原始資料
  - 可用於後續的情感分析（Sentiment Analysis）或其他 NLP 分析任務

### `/slide/` - 簡報資料夾

此資料夾包含工作坊簡報的 HTML 檔案與相關圖片素材。

- **`slide.html`**: 主要簡報檔案
  - 使用 Reveal.js 框架製作的互動式簡報
  - 主題：「企業實戰工作坊 - DATA & AI：數據人的業界生存指南」
  - 內容涵蓋：
    - 產業分析（Social Discovery 領域競品分析）
    - 統計實戰（Elo Rating 系統、A/B Testing）
    - 數據安全（AI 安全與詐騙偵測）
    - 職涯導航與工具革命（Cursor AI）
    - 專案預告：Vox Populi（YouTube 情感分析專案）

- **圖片素材**：
  - `tinder.png`, `grindr.svg`, `cmb.png`, `pure.png`, `down.png`: 競品 Logo 圖片
  - `before.png`, `after.png`: UI 改版前後對比圖
  - 其他圖片檔案用於簡報中的視覺呈現

## 🚀 使用方式

### 執行資料抓取

```bash
cd project
python grab_data.py
```

執行後會產生 `tainanjosh_comments.csv` 檔案。

### 開啟簡報

直接在瀏覽器中開啟 `slide/slide.html`，或使用本地伺服器：

```bash
cd slide
python -m http.server 8000
# 然後在瀏覽器開啟 http://localhost:8000/slide.html
```

## 📝 注意事項

- 資料抓取腳本使用非官方 API，可能受到 YouTube 政策變更影響
- 建議適度設定抓取頻率，避免對 YouTube 伺服器造成過大負擔
- 簡報需要網路連線以載入外部 CDN 資源（Reveal.js、Tailwind CSS 等）

## 📄 授權

本專案僅供學習與教學使用。

