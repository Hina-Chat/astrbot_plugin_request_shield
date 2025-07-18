# Request Shield

若網路波動，使用者可能對 LLM 發起多次相同請求。

該插件可過濾 **指定時間内** 由使用者發起的重複請求，不論其是否因網路波動。

## 安装

1. 下載 Code 為 ZIP；
2. 插件管理 - 安裝插件，選擇下載的 ZIP。

## 配置

- **請求去重時間窗口 (`deduplication_interval`)**
  - **描述**: 在 X 秒内的連續請求將視為重複請求。
  - **預設**: 5

## 說明

本插件通過以下方式實現請求過濾：

1.  **全局消息監聽**

使用一個低優先級的全局事件監聽器 (`@filter.regex(r".*", priority=-1)`) 來捕獲所有傳入的消息。

2.  **用戶消息記錄**

在內存中維護一個字典，記錄每位用戶最後一次發送消息的內容和時間戳。

3.  **異步鎖**:

為每位用戶分配一個獨立的異步鎖 (`asyncio.Lock`)，確保在處理來自同一用戶的並發請求時數據一致，避免競爭條件。

4.  **去重邏輯**

    - 當接收到新消息時，首先獲取對應用戶的鎖。
    - 比較新消息內容與記錄的上一條消息內容。
    - 若內容相同，且時間間隔小於配置的 `請求去重時間窗口`，則判定為重複請求。
    - 對於重複請求，插件會調用 `event.stop_event()` 來終止該事件的後續傳播，從而阻止機器人響應。
    - 若非重複請求，則更新該用戶的消息記錄。