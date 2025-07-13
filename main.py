import asyncio
from collections import defaultdict
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger


class RequestDeduplicator(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 記錄使用者最後一次發送的訊息
        # 格式: {user_id: (timestamp, message_content)}
        self.last_message = defaultdict(lambda: (0, ""))
        # 為每個使用者建立一個異步鎖，防止競爭條件
        self.user_locks = defaultdict(asyncio.Lock)
        # 從設定檔讀取去重時間間隔 (秒)
        self.deduplication_interval = self.context.conf.get("deduplication_interval", 5)

    @filter.regex(r".*", priority=-1)
    async def deduplicate_requests(self, event: AstrMessageEvent, *args, **kwargs):
        """在每條訊息到達時進行去重檢查"""
        user_id = event.get_sender_id()

        async with self.user_locks[user_id]:
            message_content = event.message_str

            current_time = asyncio.get_running_loop().time()
            last_time, last_content = self.last_message[user_id]

            if (
                current_time - last_time < self.deduplication_interval
                and message_content == last_content
            ):
                logger.info(f"攔截到使用者 {user_id} 的重複請求: {message_content}")
                event.stop_event()  # 終止事件傳播
                return

            # 更新最後一條訊息記錄
            self.last_message[user_id] = (current_time, message_content)

    async def terminate(self):
        """插件停用時清理資源"""
        self.last_message.clear()
        logger.info("Request Deduplicator 插件已停用")
