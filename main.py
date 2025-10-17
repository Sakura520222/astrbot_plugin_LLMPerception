from __future__ import annotations

from datetime import datetime, date
import zoneinfo

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.provider import ProviderRequest
from astrbot.api.star import Context, Star, register
from astrbot.api.all import AstrBotConfig
from astrbot.core.platform.message_type import MessageType
try:
    import chinese_calendar as calendar_cn
    CHINESE_CALENDAR_AVAILABLE = True
except ImportError:
    CHINESE_CALENDAR_AVAILABLE = False
    logger.warning("chinese-calendar 库未安装，节假日识别功能将受限")


# 常量定义
WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

PLATFORM_DISPLAY_NAMES = {
    "aiocqhttp": "QQ",
    "telegram": "Telegram",
    "discord": "Discord",
    "weixin_official_account": "微信公众号",
    "wecom": "企业微信",
    "wecom_ai_bot": "企业微信AI机器人",
    "satori": "Satori",
    "misskey": "Misskey",
}


@register("add_time", "miaomiao", "让每次请求都携带这次请求的时间", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)

        # 从配置文件读取设置
        timezone_name = config.get("timezone", "Asia/Shanghai")
        self.enable_holiday = config.get("enable_holiday_perception", True)
        self.enable_platform = config.get("enable_platform_perception", True)
        self.holiday_country = config.get("holiday_country", "CN")

        # 初始化时区
        try:
            self.timezone = zoneinfo.ZoneInfo(timezone_name)
        except (zoneinfo.ZoneInfoNotFoundError, KeyError) as e:
            logger.error(f"无效的时区设置 '{timezone_name}': {e}，使用默认时区 Asia/Shanghai")
            self.timezone = zoneinfo.ZoneInfo("Asia/Shanghai")
            timezone_name = "Asia/Shanghai"

        # 记录插件加载信息
        calendar_status = "已启用" if CHINESE_CALENDAR_AVAILABLE else "受限(未安装chinese-calendar)"
        logger.info(
            f"LLMPerception 插件已加载 | 时区: {timezone_name} | "
            f"节假日感知: {self.enable_holiday}({calendar_status}) | "
            f"平台感知: {self.enable_platform}"
        )

    def _get_holiday_info(self, current_time: datetime) -> str:
        """获取节假日信息"""
        if not self.enable_holiday:
            return ""

        info_parts = []

        # 判断是否为周末
        weekday = current_time.weekday()
        info_parts.append(WEEKDAY_NAMES[weekday])

        # 使用 chinese-calendar 库进行节假日判断（仅支持中国）
        if self.holiday_country == "CN" and CHINESE_CALENDAR_AVAILABLE:
            current_date = date(current_time.year, current_time.month, current_time.day)

            # 判断是否为法定节假日
            is_holiday = calendar_cn.is_holiday(current_date)
            # 判断是否为工作日（考虑调休）
            is_workday = calendar_cn.is_workday(current_date)

            if is_holiday:
                info_parts.append("法定节假日")
                # 获取节日名称
                holiday_name = calendar_cn.get_holiday_detail(current_date)
                if holiday_name and len(holiday_name) > 1 and holiday_name[1]:
                    info_parts.append(holiday_name[1])  # holiday_name 是 (False/True, '节日名称')
            elif is_workday:
                if weekday >= 5:
                    info_parts.append("调休工作日")
                else:
                    info_parts.append("工作日")
            else:
                info_parts.append("周末")
        else:
            # 降级方案：简单判断周末
            if weekday >= 5:
                info_parts.append("周末")
            else:
                info_parts.append("工作日")

        # 判断时间段
        hour = current_time.hour
        if 5 <= hour < 12:
            time_period = "上午"
        elif 12 <= hour < 14:
            time_period = "中午"
        elif 14 <= hour < 18:
            time_period = "下午"
        elif 18 <= hour < 22:
            time_period = "晚上"
        else:
            time_period = "深夜"
        info_parts.append(time_period)

        return ", ".join(info_parts)

    def _get_platform_info(self, event: AstrMessageEvent) -> str:
        """获取平台环境信息"""
        if not self.enable_platform:
            return ""

        info_parts = []

        # 平台类型
        platform_name = event.get_platform_name()
        platform_display = PLATFORM_DISPLAY_NAMES.get(platform_name, platform_name)
        info_parts.append(f"平台: {platform_display}")

        # 判断是群聊还是私聊（通过 MessageType 判断）

        if event.message_obj and event.message_obj.type == MessageType.GROUP_MESSAGE:
            info_parts.append("群聊")
        elif event.message_obj and event.message_obj.type == MessageType.FRIEND_MESSAGE:
            info_parts.append("私聊")

        # 消息类型
        message_chain = event.message_obj
        if message_chain and hasattr(message_chain, 'message'):
            has_image = any(seg.type == "image" for seg in message_chain.message)
            has_audio = any(seg.type in ["voice", "audio"] for seg in message_chain.message)
            has_video = any(seg.type == "video" for seg in message_chain.message)

            if has_image:
                info_parts.append("含图片")
            if has_audio:
                info_parts.append("含语音")
            if has_video:
                info_parts.append("含视频")

        return ", ".join(info_parts)

    @filter.on_llm_request()
    async def my_custom_hook_1(self, event: AstrMessageEvent, req: ProviderRequest):
        # 获取当前时间（使用配置的时区）
        current_time = datetime.now(self.timezone)

        # 基础时间信息
        timestr = current_time.strftime("%Y-%m-%d %H:%M:%S")

        # 构建感知信息
        perception_parts = [f"发送时间: {timestr}"]

        # 添加节假日信息
        holiday_info = self._get_holiday_info(current_time)
        if holiday_info:
            perception_parts.append(holiday_info)

        # 添加平台信息
        platform_info = self._get_platform_info(event)
        if platform_info:
            perception_parts.append(platform_info)

        # 组合所有感知信息
        perception_text = " | ".join(perception_parts)

        # 在用户消息前添加感知信息
        req.prompt = f"[{perception_text}]\n{req.prompt}"

        logger.info(f"已添加感知信息: {perception_text}")

    async def terminate(self):
        """Plugin shutdown hook (currently no-op)."""
        return
