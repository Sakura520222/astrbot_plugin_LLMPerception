from __future__ import annotations

from datetime import datetime, date
import zoneinfo
import re

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
    logger.warning("chinese-calendar 库未安装，中国节假日识别功能将受限")

try:
    import holidays
    HOLIDAYS_AVAILABLE = True
except ImportError:
    HOLIDAYS_AVAILABLE = False
    logger.warning("holidays 库未安装，国外节假日识别功能将受限")


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

# 情感分析相关常量
EMOTION_KEYWORDS = {
    "开心": ["开心", "高兴", "快乐", "喜悦", "愉快", "兴奋", "幸福", "满意", "棒", "好", "赞", "不错", "太棒了", "太好了", "喜欢"],
    "生气": ["生气", "愤怒", "恼火", "不爽", "讨厌", "烦", "气死", "可恶", "混蛋", "垃圾", "差劲", "糟糕"],
    "悲伤": ["悲伤", "难过", "伤心", "痛苦", "失望", "沮丧", "郁闷", "想哭", "泪", "可怜", "不幸"],
    "惊讶": ["惊讶", "惊奇", "震惊", "意外", "没想到", "居然", "竟然", "天哪", "哇", "哦"],
    "恐惧": ["害怕", "恐惧", "担心", "担忧", "紧张", "吓", "恐怖", "可怕", "危险"],
    "中性": ["正常", "一般", "还行", "可以", "了解", "知道", "明白", "收到", "好的"]
}

TONE_KEYWORDS = {
    "疑问": ["吗", "呢", "什么", "为什么", "怎么", "如何", "是否", "会不会", "能不能", "可不可以"],
    "感叹": ["！", "！", "啊", "呀", "哇", "哦", "天哪", "太", "真", "非常", "特别"],
    "陈述": ["。", "，", "的", "了", "在", "是", "有", "可以", "能够", "应该"]
}

EMOTION_EMOJIS = {
    "开心": "😊",
    "生气": "😠", 
    "悲伤": "😢",
    "惊讶": "😲",
    "恐惧": "😨",
    "中性": "😐"
}


@register("add_time", "miaomiao", "让每次请求都携带这次请求的时间", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)

        # 从配置文件读取设置
        timezone_name = config.get("timezone", "Asia/Shanghai")
        self.enable_holiday = config.get("enable_holiday_perception", True)
        self.enable_platform = config.get("enable_platform_perception", True)
        
        # 处理holiday_country配置，支持字符串和列表格式
        holiday_country_config = config.get("holiday_country", ["CN", "US", "JP"])
        if isinstance(holiday_country_config, str):
            # 如果是字符串，转换为单元素列表（向后兼容）
            self.holiday_country = [holiday_country_config]
        elif isinstance(holiday_country_config, list):
            # 如果是列表，直接使用
            self.holiday_country = holiday_country_config
        else:
            # 其他类型，使用默认值
            self.holiday_country = ["CN", "US", "JP"]
            
        self.enable_custom = config.get("enable_custom_perception", False)
        self.custom_rules = config.get("custom_perception_rules", [])
        self.log_level = config.get("log_level", "INFO")
        self.enable_detailed_logging = config.get("enable_detailed_logging", True)
        
        # 情感感知相关配置
        self.enable_emotion = config.get("enable_emotion_perception", True)
        self.emotion_method = config.get("emotion_analysis_method", "rule_based")
        self.enable_tone = config.get("enable_tone_detection", True)
        self.emotion_threshold = config.get("emotion_threshold", 0.3)

        # 初始化时区
        try:
            self.timezone = zoneinfo.ZoneInfo(timezone_name)
            self._log_message("DEBUG", f"时区设置成功: {timezone_name}")
        except (zoneinfo.ZoneInfoNotFoundError, KeyError) as e:
            error_msg = f"无效的时区设置 '{timezone_name}': {e}，使用默认时区 Asia/Shanghai"
            self._log_message("ERROR", error_msg)
            logger.error(error_msg)
            self.timezone = zoneinfo.ZoneInfo("Asia/Shanghai")
            timezone_name = "Asia/Shanghai"

        # 记录插件加载信息
        calendar_status = "已启用" if CHINESE_CALENDAR_AVAILABLE else "受限(未安装chinese-calendar)"
        holidays_status = "已启用" if HOLIDAYS_AVAILABLE else "受限(未安装holidays)"
        custom_status = f"已启用({len(self.custom_rules)}条规则)" if self.enable_custom else "未启用"
        detailed_logging_status = "已启用" if self.enable_detailed_logging else "未启用"
        emotion_status = f"已启用({self.emotion_method})" if self.enable_emotion else "未启用"
        tone_status = "已启用" if self.enable_tone else "未启用"
        
        # 格式化国家列表显示
        country_display = ", ".join(self.holiday_country)
        if len(self.holiday_country) > 3:
            country_display = f"{', '.join(self.holiday_country[:3])}...等{len(self.holiday_country)}个国家"
        
        logger.info(
            f"LLMPerception 插件已加载 | 时区: {timezone_name} | "
            f"节假日感知: {self.enable_holiday}(国家列表: [{country_display}], 中国库: {calendar_status}, 国际库: {holidays_status}) | "
            f"平台感知: {self.enable_platform} | "
            f"情感感知: {emotion_status} | "
            f"语气识别: {tone_status} | "
            f"自定义感知: {custom_status} | "
            f"详细日志: {detailed_logging_status} | "
            f"日志级别: {self.log_level}"
        )

    def _get_holiday_info(self, current_time: datetime) -> str:
        """获取节假日信息（支持多国家同时识别）"""
        if not self.enable_holiday:
            return ""

        info_parts = []

        # 判断是否为周末
        weekday = current_time.weekday()
        info_parts.append(WEEKDAY_NAMES[weekday])

        # 获取当前日期
        current_date = date(current_time.year, current_time.month, current_time.day)
        
        # 存储检测到的节假日信息
        holiday_detections = []
        workday_status = None
        
        # 遍历所有配置的国家，检测节假日
        for country_code in self.holiday_country:
            try:
                # 中国节假日（使用chinese-calendar库）
                if country_code == "CN":
                    if CHINESE_CALENDAR_AVAILABLE:
                        try:
                            # 判断是否为法定节假日
                            is_holiday = calendar_cn.is_holiday(current_date)
                            # 判断是否为工作日（考虑调休）
                            is_workday = calendar_cn.is_workday(current_date)

                            if is_holiday:
                                # 获取节日名称
                                holiday_name = calendar_cn.get_holiday_detail(current_date)
                                if holiday_name and len(holiday_name) > 1 and holiday_name[1]:
                                    holiday_detections.append(f"中国:{holiday_name[1]}")
                                    self._log_message("DEBUG", f"检测到中国节假日: {holiday_name[1]}")
                                else:
                                    holiday_detections.append("中国:法定节假日")
                            
                            # 设置工作日状态（中国节假日库有更精确的判断）
                            if workday_status is None:
                                if is_workday:
                                    if weekday >= 5:
                                        workday_status = "调休工作日"
                                    else:
                                        workday_status = "工作日"
                                else:
                                    workday_status = "周末"
                                    
                        except Exception as e:
                            error_msg = f"中国节假日判断失败: {e}"
                            self._log_message("WARNING", error_msg)
                            logger.warning(error_msg)
                    
                # 国外节假日（使用holidays库）
                elif HOLIDAYS_AVAILABLE:
                    try:
                        # 根据国家代码创建holidays对象
                        country_holidays = holidays.country_holidays(country_code)
                        
                        # 检查是否为节假日
                        holiday_name = country_holidays.get(current_date)
                        
                        if holiday_name:
                            # 获取节日名称（可能有多语言，取第一个）
                            if isinstance(holiday_name, (list, tuple)):
                                holiday_name = holiday_name[0]
                            
                            # 获取国家名称映射
                            country_names = {
                                "US": "美国", "GB": "英国", "JP": "日本", "DE": "德国", 
                                "FR": "法国", "CA": "加拿大", "AU": "澳大利亚", "IT": "意大利",
                                "ES": "西班牙", "KR": "韩国", "RU": "俄罗斯", "BR": "巴西",
                                "IN": "印度", "MX": "墨西哥", "ZA": "南非"
                            }
                            country_name = country_names.get(country_code, country_code)
                            holiday_detections.append(f"{country_name}:{holiday_name}")
                            self._log_message("DEBUG", f"检测到{country_code}节假日: {holiday_name}")
                        
                        # 特殊处理万圣节（10月31日），因为某些版本的holidays库可能不包含它
                        elif current_date.month == 10 and current_date.day == 31:
                            # 万圣节在多个国家庆祝
                            halloween_countries = ["US", "CA", "GB", "AU", "IE", "NZ"]
                            if country_code in halloween_countries:
                                country_names = {
                                    "US": "美国", "GB": "英国", "CA": "加拿大", 
                                    "AU": "澳大利亚", "IE": "爱尔兰", "NZ": "新西兰"
                                }
                                country_name = country_names.get(country_code, country_code)
                                holiday_detections.append(f"{country_name}:万圣节")
                                self._log_message("DEBUG", f"检测到{country_code}万圣节")
                        
                        # 特殊处理情人节（2月14日）
                        elif current_date.month == 2 and current_date.day == 14:
                            # 情人节在多个国家庆祝
                            valentine_countries = ["US", "GB", "CA", "AU", "DE", "FR", "IT", "ES", "JP", "KR", "BR", "MX"]
                            if country_code in valentine_countries:
                                country_names = {
                                    "US": "美国", "GB": "英国", "CA": "加拿大", "AU": "澳大利亚",
                                    "DE": "德国", "FR": "法国", "IT": "意大利", "ES": "西班牙",
                                    "JP": "日本", "KR": "韩国", "BR": "巴西", "MX": "墨西哥"
                                }
                                country_name = country_names.get(country_code, country_code)
                                holiday_detections.append(f"{country_name}:情人节")
                                self._log_message("DEBUG", f"检测到{country_code}情人节")
                        
                        # 特殊处理复活节（计算方法复杂，这里使用简单近似：3月22日-4月25日之间的周日）
                        elif current_date.month in [3, 4]:
                            # 复活节通常在3月22日到4月25日之间的周日
                            easter_start = date(current_date.year, 3, 22)
                            easter_end = date(current_date.year, 4, 25)
                            if easter_start <= current_date <= easter_end and current_date.weekday() == 6:  # 周日
                                easter_countries = ["US", "GB", "CA", "AU", "DE", "FR", "IT", "ES", "BR", "MX"]
                                if country_code in easter_countries:
                                    country_names = {
                                        "US": "美国", "GB": "英国", "CA": "加拿大", "AU": "澳大利亚",
                                        "DE": "德国", "FR": "法国", "IT": "意大利", "ES": "西班牙",
                                        "BR": "巴西", "MX": "墨西哥"
                                    }
                                    country_name = country_names.get(country_code, country_code)
                                    holiday_detections.append(f"{country_name}:复活节")
                                    self._log_message("DEBUG", f"检测到{country_code}复活节")
                        
                        # 特殊处理感恩节（美国：11月第四个周四；加拿大：10月第二个周一）
                        elif current_date.month == 11 and current_date.weekday() == 3:  # 周四
                            # 检查是否为11月第四个周四（美国感恩节）
                            if 22 <= current_date.day <= 28:  # 第四个周四在22-28日之间
                                if country_code in ["US"]:
                                    country_names = {"US": "美国"}
                                    country_name = country_names.get(country_code, country_code)
                                    holiday_detections.append(f"{country_name}:感恩节")
                                    self._log_message("DEBUG", f"检测到{country_code}感恩节")
                        elif current_date.month == 10 and current_date.weekday() == 0:  # 周一
                            # 检查是否为10月第二个周一（加拿大感恩节）
                            if 8 <= current_date.day <= 14:  # 第二个周一在8-14日之间
                                if country_code in ["CA"]:
                                    country_names = {"CA": "加拿大"}
                                    country_name = country_names.get(country_code, country_code)
                                    holiday_detections.append(f"{country_name}:感恩节")
                                    self._log_message("DEBUG", f"检测到{country_code}感恩节")
                        
                        # 特殊处理元旦（1月1日）
                        elif current_date.month == 1 and current_date.day == 1:
                            # 元旦在几乎所有国家都庆祝
                            new_year_countries = ["US", "GB", "CA", "AU", "DE", "FR", "IT", "ES", "JP", "KR", "BR", "MX", "RU", "IN"]
                            if country_code in new_year_countries:
                                country_names = {
                                    "US": "美国", "GB": "英国", "CA": "加拿大", "AU": "澳大利亚",
                                    "DE": "德国", "FR": "法国", "IT": "意大利", "ES": "西班牙",
                                    "JP": "日本", "KR": "韩国", "BR": "巴西", "MX": "墨西哥",
                                    "RU": "俄罗斯", "IN": "印度"
                                }
                                country_name = country_names.get(country_code, country_code)
                                holiday_detections.append(f"{country_name}:元旦")
                                self._log_message("DEBUG", f"检测到{country_code}元旦")
                        
                        # 特殊处理劳动节（5月1日）
                        elif current_date.month == 5 and current_date.day == 1:
                            # 劳动节在多个国家庆祝
                            labor_day_countries = ["DE", "FR", "IT", "ES", "RU", "BR", "MX", "IN", "CN"]
                            if country_code in labor_day_countries:
                                country_names = {
                                    "DE": "德国", "FR": "法国", "IT": "意大利", "ES": "西班牙",
                                    "RU": "俄罗斯", "BR": "巴西", "MX": "墨西哥", "IN": "印度",
                                    "CN": "中国"
                                }
                                country_name = country_names.get(country_code, country_code)
                                holiday_detections.append(f"{country_name}:劳动节")
                                self._log_message("DEBUG", f"检测到{country_code}劳动节")
                        
                        # 特殊处理独立日/国庆日
                        # 美国独立日（7月4日）
                        elif current_date.month == 7 and current_date.day == 4:
                            if country_code in ["US"]:
                                country_names = {"US": "美国"}
                                country_name = country_names.get(country_code, country_code)
                                holiday_detections.append(f"{country_name}:独立日")
                                self._log_message("DEBUG", f"检测到{country_code}独立日")
                        
                        # 法国国庆日（7月14日）
                        elif current_date.month == 7 and current_date.day == 14:
                            if country_code in ["FR"]:
                                country_names = {"FR": "法国"}
                                country_name = country_names.get(country_code, country_code)
                                holiday_detections.append(f"{country_name}:国庆日")
                                self._log_message("DEBUG", f"检测到{country_code}国庆日")
                        
                        # 加拿大国庆日（7月1日）
                        elif current_date.month == 7 and current_date.day == 1:
                            if country_code in ["CA"]:
                                country_names = {"CA": "加拿大"}
                                country_name = country_names.get(country_code, country_code)
                                holiday_detections.append(f"{country_name}:国庆日")
                                self._log_message("DEBUG", f"检测到{country_code}国庆日")
                        
                        # 特殊处理母亲节（5月第二个周日）
                        elif current_date.month == 5 and current_date.weekday() == 6:  # 周日
                            # 检查是否为5月第二个周日
                            if 8 <= current_date.day <= 14:  # 第二个周日在8-14日之间
                                mother_day_countries = ["US", "GB", "CA", "AU", "DE", "FR", "IT", "ES", "JP", "BR", "MX"]
                                if country_code in mother_day_countries:
                                    country_names = {
                                        "US": "美国", "GB": "英国", "CA": "加拿大", "AU": "澳大利亚",
                                        "DE": "德国", "FR": "法国", "IT": "意大利", "ES": "西班牙",
                                        "JP": "日本", "BR": "巴西", "MX": "墨西哥"
                                    }
                                    country_name = country_names.get(country_code, country_code)
                                    holiday_detections.append(f"{country_name}:母亲节")
                                    self._log_message("DEBUG", f"检测到{country_code}母亲节")
                        
                        # 特殊处理父亲节（6月第三个周日）
                        elif current_date.month == 6 and current_date.weekday() == 6:  # 周日
                            # 检查是否为6月第三个周日
                            if 15 <= current_date.day <= 21:  # 第三个周日在15-21日之间
                                father_day_countries = ["US", "GB", "CA", "AU", "DE", "FR", "IT", "ES", "JP", "BR", "MX"]
                                if country_code in father_day_countries:
                                    country_names = {
                                        "US": "美国", "GB": "英国", "CA": "加拿大", "AU": "澳大利亚",
                                        "DE": "德国", "FR": "法国", "IT": "意大利", "ES": "西班牙",
                                        "JP": "日本", "BR": "巴西", "MX": "墨西哥"
                                    }
                                    country_name = country_names.get(country_code, country_code)
                                    holiday_detections.append(f"{country_name}:父亲节")
                                    self._log_message("DEBUG", f"检测到{country_code}父亲节")
                            
                    except holidays.exceptions.UnknownCountryError:
                        error_msg = f"不支持的国家代码: {country_code}，请检查配置"
                        self._log_message("ERROR", error_msg)
                        logger.error(error_msg)
                    except Exception as e:
                        error_msg = f"{country_code}节假日判断失败: {e}"
                        self._log_message("WARNING", error_msg)
                        logger.warning(error_msg)
                        
            except Exception as e:
                error_msg = f"节假日判断异常（国家:{country_code}）: {e}"
                self._log_message("WARNING", error_msg)
                logger.warning(error_msg)
        
        # 处理节假日检测结果
        if holiday_detections:
            # 如果有检测到节假日，添加节假日信息
            info_parts.append("节假日")
            # 添加所有检测到的节假日名称
            info_parts.extend(holiday_detections)
        else:
            # 如果没有检测到节假日，设置工作日状态
            if workday_status is None:
                # 如果没有中国节假日库的精确判断，使用简单周末判断
                if weekday >= 5:
                    workday_status = "周末"
                else:
                    workday_status = "工作日"
            
            info_parts.append(workday_status)

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

    def _get_custom_perception_info(self, current_time: datetime, event: AstrMessageEvent) -> str:
        """获取自定义感知信息"""
        if not self.enable_custom or not self.custom_rules:
            return ""

        custom_parts = []
        platform_name = event.get_platform_name()
        message_type = event.message_obj.type if event.message_obj else None

        # 创建可用的变量字典
        variables = {
            'current_time': current_time,
            'event': event,
            'platform_name': platform_name,
            'message_type': message_type
        }

        # 处理每条自定义规则
        for rule in self.custom_rules:
            if not rule.get('enabled', True):
                self._log_message("DEBUG", f"跳过禁用规则: {rule.get('name', 'unknown')}")
                continue

            try:
                # 安全地评估条件
                condition = rule['condition']
                # 使用简单的字符串匹配来避免eval的安全风险
                # 这里我们只支持简单的变量替换和基本比较
                condition_result = self._safe_evaluate_condition(condition, variables)
                
                if condition_result:
                    # 处理内容模板
                    content = rule['content']
                    custom_content = self._process_content_template(content, variables)
                    if custom_content:
                        custom_parts.append(custom_content)
                        self._log_message("DEBUG", f"自定义规则触发: {rule.get('name', 'unknown')} -> {custom_content}")
                else:
                    self._log_message("DEBUG", f"自定义规则未触发: {rule.get('name', 'unknown')}")
                        
            except Exception as e:
                error_msg = f"自定义规则 '{rule.get('name', 'unknown')}' 执行失败: {e}"
                self._log_message("WARNING", error_msg)
                logger.warning(error_msg)

        return " | ".join(custom_parts)

    def _get_emotion_info(self, event: AstrMessageEvent) -> str:
        """获取情感状态信息"""
        if not self.enable_emotion:
            return ""

        # 提取消息文本
        message_text = self._extract_message_text(event)
        if not message_text:
            return ""

        emotion_parts = []

        # 情感分析
        emotion_result = self._analyze_emotion(message_text)
        if emotion_result and emotion_result != "中性":  # 只有当情感不是中性时才添加
            emotion_emoji = EMOTION_EMOJIS.get(emotion_result, "")
            emotion_parts.append(f"情感:{emotion_result}{emotion_emoji}")
            self._log_message("DEBUG", f"情感分析结果: {emotion_result}")

        # 语气识别
        if self.enable_tone:
            tone_result = self._analyze_tone(message_text)
            if tone_result:
                emotion_parts.append(f"语气:{tone_result}")
                self._log_message("DEBUG", f"语气识别结果: {tone_result}")

        return " | ".join(emotion_parts)

    def _extract_message_text(self, event: AstrMessageEvent) -> str:
        """从消息事件中提取文本内容"""
        if not event.message_obj or not hasattr(event.message_obj, 'message'):
            return ""
        
        text_parts = []
        for seg in event.message_obj.message:
            if hasattr(seg, 'text') and seg.text:
                text_parts.append(seg.text.strip())
        
        return " ".join(text_parts)

    def _analyze_emotion(self, text: str) -> str:
        """分析文本情感（基于规则的方法）"""
        if self.emotion_method == "rule_based":
            return self._rule_based_emotion_analysis(text)
        else:
            # 预留机器学习方法
            return self._rule_based_emotion_analysis(text)

    def _rule_based_emotion_analysis(self, text: str) -> str:
        """基于规则的情感分析"""
        if not text or len(text.strip()) == 0:
            return "中性"
        
        emotion_scores = {emotion: 0.0 for emotion in EMOTION_KEYWORDS.keys()}
        
        # 预处理文本
        cleaned_text = self._preprocess_text(text)
        
        # 从表情符号检测情绪
        emoji_emotion, emoji_score = self._detect_emotion_from_emoji(text)
        if emoji_emotion:
            emotion_scores[emoji_emotion] += emoji_score
        
        # 关键词匹配
        for emotion, keywords in EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if self._contains_word(cleaned_text, keyword):
                    emotion_scores[emotion] += 1.0
        
        # 找到最高分的情绪
        max_emotion = "中性"
        max_score = emotion_scores["中性"]
        
        for emotion, score in emotion_scores.items():
            if score > max_score or (score == max_score and emotion != "中性"):
                max_score = score
                max_emotion = emotion
        
        # 设置阈值（降低到0.5以提高敏感度）
        threshold = 0.5
        if max_score < threshold:
            return "中性"
        
        return max_emotion

    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 转换为小写进行匹配
        return text.lower()
    
    def _contains_word(self, text: str, word: str) -> bool:
        """检查文本是否包含特定词语（优化的中文匹配）"""
        # 对于中文，使用更智能的匹配方式
        # 主要目标是避免单字关键词的部分匹配问题
        
        # 如果关键词是单字，需要更严格的边界检查
        if len(word) == 1:
            # 单字关键词：使用正则表达式检查是否作为独立词语
            # 更宽松的边界检查：允许在非中文字符边界出现
            pattern = r'(^|[^\u4e00-\u9fff])' + re.escape(word) + r'([^\u4e00-\u9fff]|$)'
            return bool(re.search(pattern, text))
        else:
            # 多字关键词：直接使用in检查，因为多字词不容易出现部分匹配问题
            # 例如"开心"在"我很开心"中是完整匹配，在"开心果"中也是完整匹配
            return word in text
    
    def _detect_emotion_from_emoji(self, text: str) -> tuple:
        """从表情符号检测情感"""
        emoji_emotion = None
        emoji_score = 0
        
        # 常见表情符号与情感的映射
        emoji_mapping = {
            "😊": "开心", "😂": "开心", "😄": "开心", "😍": "开心", "🥰": "开心",
            "😠": "生气", "😡": "生气", "🤬": "生气", "💢": "生气",
            "😢": "悲伤", "😭": "悲伤", "😔": "悲伤", "🥺": "悲伤",
            "😲": "惊讶", "😮": "惊讶", "🤯": "惊讶", "😱": "惊讶",
            "😨": "恐惧", "😰": "恐惧", "😥": "恐惧", "😓": "恐惧"
        }
        
        for emoji, emotion in emoji_mapping.items():
            if emoji in text:
                emoji_emotion = emotion
                emoji_score = 2  # 表情符号权重较高
                break  # 只取第一个匹配的表情符号
        
        return emoji_emotion, emoji_score

    def _analyze_tone(self, text: str) -> str:
        """分析文本语气"""
        if not text or len(text.strip()) == 0:
            return "陈述"
        
        tone_scores = {"疑问": 0, "感叹": 0, "陈述": 0}
        
        # 预处理文本
        cleaned_text = self._preprocess_text(text)
        
        # 标点符号分析
        question_marks = cleaned_text.count("?") + cleaned_text.count("？")
        exclamation_marks = cleaned_text.count("!") + cleaned_text.count("！")
        
        tone_scores["疑问"] += question_marks * 2
        tone_scores["感叹"] += exclamation_marks * 2
        
        # 疑问词分析
        question_words = ["吗", "呢", "什么", "为什么", "怎么", "如何", "是否", "会不会", "能不能", "可不可以", "为何", "哪里", "何时", "谁", "哪个"]
        for word in question_words:
            if self._contains_word(cleaned_text, word):
                tone_scores["疑问"] += 1
        
        # 感叹词分析
        exclamation_words = ["啊", "呀", "哇", "哦", "天哪", "太", "真", "非常", "特别", "超级", "极其", "无比", "简直", "实在"]
        for word in exclamation_words:
            if self._contains_word(cleaned_text, word):
                tone_scores["感叹"] += 1
        
        # 句子长度和结构分析
        sentences = self._split_sentences(text)
        if sentences:
            # 如果句子以疑问词开头或结尾
            first_sentence = sentences[0].lower()
            last_sentence = sentences[-1].lower()
            
            if any(first_sentence.startswith(word) for word in question_words):
                tone_scores["疑问"] += 2
            if any(last_sentence.endswith(word) for word in question_words):
                tone_scores["疑问"] += 1
                
            if any(first_sentence.startswith(word) for word in exclamation_words):
                tone_scores["感叹"] += 2
            if any(last_sentence.endswith(word) for word in exclamation_words):
                tone_scores["感叹"] += 1
        
        # 找到最高分的语气
        max_tone = "陈述"
        max_score = tone_scores.get("陈述", 0)
        
        for tone, score in tone_scores.items():
            if score > max_score:
                max_score = score
                max_tone = tone
        
        # 改进混合语气识别
        question_score = tone_scores["疑问"]
        exclamation_score = tone_scores["感叹"]
        
        # 如果疑问和感叹分数都很高，可能是混合语气
        if question_score >= 2 and exclamation_score >= 2:
            # 根据分数比例判断主要语气
            if question_score > exclamation_score:
                return "疑问感叹"
            else:
                return "感叹疑问"
        elif question_score >= 3 and exclamation_score >= 1:
            return "疑问感叹"
        elif exclamation_score >= 3 and question_score >= 1:
            return "感叹疑问"
        
        return max_tone
    
    def _split_sentences(self, text: str) -> list:
        """简单分割句子"""
        # 使用标点符号分割句子
        import re
        sentences = re.split(r'[。！？!?]', text)
        return [s.strip() for s in sentences if s.strip()]

    def _safe_evaluate_condition(self, condition: str, variables: dict) -> bool:
        """安全地评估条件表达式"""
        try:
            # 简单的变量替换和基本条件判断
            # 支持简单的比较操作和变量检查
            condition_lower = condition.lower().strip()
            
            # 检查是否为简单的时间条件
            if 'hour' in condition_lower and 'current_time' in condition_lower:
                # 提取小时比较条件
                import re
                hour_match = re.search(r'current_time\.hour\s*([<>=!]+)\s*(\d+)', condition)
                if hour_match:
                    operator = hour_match.group(1)
                    target_hour = int(hour_match.group(2))
                    current_hour = variables['current_time'].hour
                    
                    if operator == '>':
                        return current_hour > target_hour
                    elif operator == '>=':
                        return current_hour >= target_hour
                    elif operator == '<':
                        return current_hour < target_hour
                    elif operator == '<=':
                        return current_hour <= target_hour
                    elif operator == '==' or operator == '=':
                        return current_hour == target_hour
                    elif operator == '!=':
                        return current_hour != target_hour
            
            # 检查是否为平台条件
            if 'platform_name' in condition_lower:
                platform_name = variables['platform_name']
                if '==' in condition or '=' in condition:
                    # 提取平台名称比较
                    import re
                    platform_match = re.search(r"platform_name\s*[=!]+\s*['\"]([^'\"]+)['\"]", condition)
                    if platform_match:
                        target_platform = platform_match.group(1)
                        return platform_name == target_platform
            
            # 检查是否为消息类型条件
            if 'message_type' in condition_lower:
                message_type = variables['message_type']
                if message_type and '==' in condition or '=' in condition:
                    import re
                    type_match = re.search(r"message_type\s*[=!]+\s*['\"]([^'\"]+)['\"]", condition)
                    if type_match:
                        target_type = type_match.group(1)
                        return str(message_type) == target_type
            
            # 默认返回False，避免不安全的条件执行
            return False
            
        except Exception as e:
            logger.warning(f"条件评估失败: {condition}, 错误: {e}")
            return False

    def _process_content_template(self, content: str, variables: dict) -> str:
        """处理内容模板中的变量替换"""
        try:
            result = content
            
            # 替换时间变量
            current_time = variables['current_time']
            result = result.replace('{current_time.hour}', str(current_time.hour))
            result = result.replace('{current_time.minute}', str(current_time.minute))
            result = result.replace('{current_time.weekday()}', str(current_time.weekday()))
            result = result.replace('{current_time.strftime("%H:%M")}', current_time.strftime("%H:%M"))
            result = result.replace('{current_time.strftime("%Y-%m-%d")}', current_time.strftime("%Y-%m-%d"))
            
            # 替换平台变量
            platform_name = variables['platform_name']
            platform_display = PLATFORM_DISPLAY_NAMES.get(platform_name, platform_name)
            result = result.replace('{platform_name}', platform_display)
            
            # 替换消息类型变量
            message_type = variables['message_type']
            if message_type:
                result = result.replace('{message_type}', str(message_type))
            
            return result
            
        except Exception as e:
            logger.warning(f"内容模板处理失败: {content}, 错误: {e}")
            return result

    def _log_message(self, level: str, message: str):
        """根据配置的日志级别输出日志"""
        level_priority = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
        config_priority = level_priority.get(self.log_level, 1)
        message_priority = level_priority.get(level, 1)
        
        if message_priority >= config_priority:
            if level == "DEBUG":
                logger.debug(message)
            elif level == "INFO":
                logger.info(message)
            elif level == "WARNING":
                logger.warning(message)
            elif level == "ERROR":
                logger.error(message)

    def _log_detailed_info(self, current_time: datetime, event: AstrMessageEvent, perception_text: str):
        """输出详细的请求处理信息"""
        if not self.enable_detailed_logging:
            return
        
        platform_name = event.get_platform_name()
        platform_display = PLATFORM_DISPLAY_NAMES.get(platform_name, platform_name)
        message_type = event.message_obj.type if event.message_obj else "未知"
        
        # 构建详细日志信息
        detailed_info = [
            f"时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"平台: {platform_display}",
            f"消息类型: {message_type}",
            f"感知信息: {perception_text}"
        ]
        
        # 添加消息内容摘要（如果存在）
        if event.message_obj and hasattr(event.message_obj, 'message'):
            message_content = ""
            for seg in event.message_obj.message:
                if hasattr(seg, 'text') and seg.text:
                    message_content += seg.text[:50]  # 限制长度避免日志过长
                    if len(seg.text) > 50:
                        message_content += "..."
                    break
            if message_content:
                detailed_info.append(f"消息摘要: {message_content}")
        
        self._log_message("DEBUG", " | ".join(detailed_info))

    @filter.on_llm_request()
    async def my_custom_hook_1(self, event: AstrMessageEvent, req: ProviderRequest):
        # 记录请求开始
        self._log_message("DEBUG", "开始处理LLM请求")
        
        # 获取当前时间（使用配置的时区）
        current_time = datetime.now(self.timezone)
        
        # 记录时间信息
        self._log_message("DEBUG", f"当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 基础时间信息
        timestr = current_time.strftime("%Y-%m-%d %H:%M:%S")

        # 构建感知信息
        perception_parts = [f"发送时间: {timestr}"]

        # 添加节假日信息
        holiday_info = self._get_holiday_info(current_time)
        if holiday_info:
            perception_parts.append(holiday_info)
            self._log_message("DEBUG", f"节假日信息: {holiday_info}")

        # 添加平台信息
        platform_info = self._get_platform_info(event)
        if platform_info:
            perception_parts.append(platform_info)
            self._log_message("DEBUG", f"平台信息: {platform_info}")

        # 添加自定义感知信息
        custom_info = self._get_custom_perception_info(current_time, event)
        if custom_info:
            perception_parts.append(custom_info)
            self._log_message("DEBUG", f"自定义信息: {custom_info}")

        # 添加情感感知信息
        emotion_info = self._get_emotion_info(event)
        if emotion_info:
            perception_parts.append(emotion_info)
            self._log_message("DEBUG", f"情感信息: {emotion_info}")

        # 组合所有感知信息
        perception_text = " | ".join(perception_parts)

        # 记录原始消息长度
        original_length = len(req.prompt) if req.prompt else 0
        
        # 在用户消息前添加感知信息
        req.prompt = f"[{perception_text}]\n{req.prompt}"
        
        # 记录处理后的消息长度
        new_length = len(req.prompt) if req.prompt else 0
        
        # 输出详细处理信息
        self._log_detailed_info(current_time, event, perception_text)
        
        # 记录处理结果
        self._log_message("INFO", f"已添加感知信息: {perception_text}")
        self._log_message("DEBUG", f"消息长度变化: {original_length} -> {new_length} (+{new_length - original_length})")
        
        # 记录请求完成
        self._log_message("DEBUG", "LLM请求处理完成")

    async def terminate(self):
        """Plugin shutdown hook (currently no-op)."""
        return
