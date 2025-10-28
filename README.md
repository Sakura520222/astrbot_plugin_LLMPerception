AstrBot LLMPerception 插件

<div align="center">

![Version](https://img.shields.io/badge/version-1.6.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![GitHub Stars](https://img.shields.io/github/stars/Sakura520222/astrbot_plugin_LLMPerception?style=social)
![GitHub Forks](https://img.shields.io/github/forks/Sakura520222/astrbot_plugin_LLMPerception?style=social)

**让AI更懂你 - 智能环境感知插件**

</div>

## 📖 简介

LLMPerception 是一个为 AstrBot 设计的智能环境感知插件，旨在增强 LLM 对用户所处环境的理解能力。通过精确的时间感知、节假日识别和平台环境分析，让 AI 能够提供更贴心、更符合场景的智能回复。

✨ **核心价值**：让AI不再是冰冷的文字生成器，而是真正理解你当前处境的有温度的助手。

## 🚀 快速开始

### 1️⃣ 安装插件
- 在 AstrBot 插件市场搜索 `LLMPerception` 并安装
- 或手动复制到 `data/plugins/` 目录

### 2️⃣ 基本配置（推荐）
```json
{
    "timezone": "Asia/Shanghai",
    "enable_holiday_perception": true,
    "enable_platform_perception": true,
    "log_level": "INFO"
}
```

### 3️⃣ 立即体验
安装后无需额外配置，插件会自动为每条消息添加环境感知信息，让AI回复更贴心！

## 🚀 功能特性

### 🕒 时间感知
- ⏰ **精确时间戳**：年-月-日 时:分:秒格式
- 🌍 **多时区支持**：可自定义时区设置，全球适用
- 📊 **智能时间段**：自动识别上午/中午/下午/晚上/深夜

### 🎉 节假日感知
- 🏮 **法定节假日识别**：春节、清明、劳动节、端午、中秋、国庆、元旦等
- 🌍 **多国家同时识别**：支持同时识别多个国家的节假日，默认配置为中国、美国、日本
- 🌐 **智能库切换**：中国节假日使用 `chinese-calendar` 库，国际节假日使用 `holidays` 库
- 🔄 **调休智能判断**：自动识别调休工作日（如国庆期间周末上班）
- 📅 **星期识别**：周一到周日、工作日/周末精确判断
- 📚 **数据可靠**：中国节假日基于 `chinese-calendar` 库，国际节假日基于 `holidays` 库

### 🌐 平台环境感知
- 💬 **平台类型识别**：QQ、Telegram、Discord、微信公众号、企业微信等
- 👥 **聊天类型区分**：群聊和私聊智能识别
- 📱 **消息类型分析**：图片、语音、视频等多媒体消息识别

### 📋 日志管理
- 🔍 **多级别日志**：DEBUG/INFO/WARNING/ERROR四级日志控制
- 📝 **详细日志输出**：可配置的详细处理过程记录
- 🎯 **智能过滤**：根据配置级别自动过滤无关日志信息

## 📋 更新日志

### v1.6.0 (当前版本)
**发布日期**: 2025-10-28

#### ✨ 新增功能
- 🌍 **多国家节假日支持**：新增支持美国、英国、日本、德国、法国等15+个国家的节假日识别
- 🔄 **智能库切换**：中国节假日使用chinese-calendar库，国际节假日使用holidays库
- 🛡️ **增强错误处理**：添加不支持国家代码检测和降级方案

#### ⚙️ 配置增强
- 📝 **更新holiday_country配置**：支持更多国家代码选项
- 📋 **配置架构更新**：完善配置提示信息和参考链接

#### 📚 文档优化
- 🔧 **功能文档更新**：添加多国家节假日支持说明和使用示例

### v1.5.0
**发布日期**: 2025-10-27

#### ✨ 新增功能
- 📊 **日志管理功能**：新增多级别日志控制（DEBUG/INFO/WARNING/ERROR）
- 🔍 **详细日志输出**：可配置的详细处理过程记录
- 🎯 **智能日志过滤**：根据配置级别自动过滤无关日志信息

#### ⚙️ 配置增强
- 📝 **新增日志相关配置项**：`log_level` 和 `enable_detailed_logging`
- 📋 **配置说明完善**：更新所有配置项的详细说明和示例

#### 📚 文档优化
- 🔧 **技术文档更新**：修正配置类型说明，添加日志管理功能说明

### v1.0.0
**发布日期**: 2025-10-17

#### 🎉 初始版本
- 🕒 **基础时间感知**：精确时间戳和多时区支持
- 🎊 **节假日识别**：法定节假日和调休智能判断
- 🌐 **平台环境感知**：多种平台类型识别
- 🔧 **自定义感知功能**：灵活的条件触发和模板变量支持

## ⚙️ 配置说明

插件提供丰富的配置选项，可通过 AstrBot 控制台或配置文件进行修改：

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `timezone` | string | `Asia/Shanghai` | 🌍 时区设置，支持 `Asia/Tokyo`, `America/New_York`, `UTC` 等 |
| `enable_holiday_perception` | bool | `true` | 🎉 启用/禁用节假日感知功能 |
| `enable_platform_perception` | bool | `true` | 💬 启用/禁用平台环境感知 |
| `holiday_country` | list | `["CN", "US", "JP"]` | 🏮 节假日国家/地区代码列表（支持同时识别多个国家，如 CN/中国、US/美国、GB/英国、JP/日本、DE/德国、FR/法国等15+个国家） |
| `enable_custom_perception` | bool | `false` | 🔧 启用/禁用自定义感知功能 |
| `custom_perception_rules` | list | `[]` | 📋 自定义感知规则列表 |
| `log_level` | string | `INFO` | 🔍 日志输出级别：DEBUG/INFO/WARNING/ERROR |
| `enable_detailed_logging` | bool | `true` | 📝 启用/禁用详细日志输出 |

## 🔧 自定义感知功能

### ✨ 功能特性

- 🎯 **灵活的条件触发**：基于时间、平台、消息类型等条件触发自定义规则
- 📝 **模板变量支持**：支持在内容中使用变量模板
- 🔒 **安全执行**：采用安全的条件评估机制，避免代码注入风险

### 配置示例

```json
{
    "enable_custom_perception": true,
    "custom_perception_rules": [
        {
            "name": "工作时间提醒",
            "condition": "current_time.hour >= 9 and current_time.hour <= 18",
            "content": "工作时间段",
            "enabled": true
        },
        {
            "name": "深夜模式",
            "condition": "current_time.hour >= 22 or current_time.hour < 6",
            "content": "深夜模式，请早点休息",
            "enabled": true
        },
        {
            "name": "QQ平台特殊处理",
            "condition": "platform_name == 'aiocqhttp'",
            "content": "QQ平台消息",
            "enabled": true
        }
    ]
}
```

### 可用变量

在条件和内容模板中可以使用以下变量：

- `current_time`：当前时间对象
  - `current_time.hour`：小时（0-23）
  - `current_time.minute`：分钟（0-59）
  - `current_time.weekday()`：星期几（0-6，0为周一）
  - `current_time.strftime("%H:%M")`：格式化时间
  - `current_time.strftime("%Y-%m-%d")`：格式化日期
- `platform_name`：平台名称
- `message_type`：消息类型

### 条件语法

支持以下条件表达式：

- 时间比较：`current_time.hour > 18`（晚上6点后）
- 平台判断：`platform_name == 'aiocqhttp'`（QQ平台）
- 组合条件：`current_time.hour >= 9 and current_time.hour <= 18`（工作时间）

### 内容模板

在内容中可以使用变量替换：

- `{current_time.hour}`：当前小时
- `{current_time.strftime("%H:%M")}`：格式化时间
- `{platform_name}`：平台显示名称

## 📊 效果示例

### 💬 普通工作日场景
启用所有功能后，LLM 收到的消息格式如下：

```
[发送时间: 2025-10-17 14:30:00 | 周五, 工作日, 下午 | 平台: QQ, 群聊, 含图片]
用户的实际消息内容
```

### 🏮 春节节假日场景
春节期间AI能够识别节日氛围：
```
[发送时间: 2025-02-01 10:00:00 | 周六, 法定节假日, 春节, 上午 | 平台: Telegram, 私聊]
新年快乐！
```

### 🌍 多国家节假日场景
配置多个国家时，AI能够同时识别不同国家的节假日：
```
[发送时间: 2025-12-25 10:00:00 | 周四, 工作日, 圣诞节(美国), 上午 | 平台: Discord, 群聊]
圣诞快乐！
```

### 🔄 调休工作日场景
调休工作日AI能够理解特殊安排：
```
[发送时间: 2025-02-08 09:00:00 | 周六, 调休工作日, 上午 | 平台: QQ, 群聊]
今天要上班吗？
```

### 📋 日志输出示例
插件运行时的控制台日志输出：
```
[22:51:52] [Plug] [INFO] [astrbot_plugin_llmperception.main:65]: LLMPerception 插件已加载 | 时区: Asia/Shanghai | 节假日感知: True(已启用) | 平台感知: True | 自定义感知: 未启用 | 详细日志: 已启用 | 日志级别: DEBUG 
[22:52:08] [Plug] [INFO] [astrbot_plugin_llmperception.main:324]: 已添加感知信息: 发送时间: 2025-10-27 22:52:08 | 周一, 工作日, 深夜 | 平台: QQ, 私聊 
```

## 📥 安装

### 方法一：插件市场安装（推荐）
1. 打开 AstrBot 插件
2. 进入插件市场
3. 搜索 `LLMPerception` 并点击安装

### 方法二：手动安装
1. 下载插件文件
2. 复制到 AstrBot 的 `data/plugins/` 目录
3. 重启 AstrBot 服务

### 自动依赖安装
插件会自动安装所需依赖：
- `chinese-calendar>=1.9.0`：用于准确的中国节假日和调休识别
- `holidays>=0.40`：用于国际节假日识别

## 📦 依赖

- `chinese-calendar>=1.9.0`：用于准确的中国节假日和调休识别
- `holidays>=0.40`：用于国际节假日识别

## 💡 使用建议

### AI 可以利用这些信息做什么？

#### ⏰ 时间智能
- 🌙 **深夜关怀**："这么晚还没休息呀，要注意身体哦"
- 🌅 **早晨问候**："早上好！新的一天开始啦"
- 📊 **时段适配**：根据时间段调整回复风格和语气

#### 🎉 节日智能
- 🏮 **节日祝福**："春节快乐！祝您新年大吉"
- 😊 **周末轻松**：周末时使用更轻松随意的语气
- 💪 **调休理解**："周末还要上班辛苦了，加油！"

#### 💬 平台智能
- 👥 **群聊活跃**：群聊时更活跃，鼓励互动
- 💕 **私聊贴心**：私聊时更贴心，关注个人需求
- 📱 **平台适配**：根据平台特性调整回复格式

## 🔧 日志配置建议

### 不同场景推荐配置
- 🐛 **调试模式**：`log_level: DEBUG` + `enable_detailed_logging: true`
- 📊 **生产环境**：`log_level: INFO` + `enable_detailed_logging: false`
- ⚠️ **问题排查**：`log_level: WARNING` + `enable_detailed_logging: true`

## 👨‍💻 开发者

- **原作者**：喵喵
- **原仓库**：[GitHub](https://github.com/miaoxutao123/astrbot_plugin_LLMPerception)
- **当前维护者**：Sakura520222
- **仓库**：[GitHub](https://github.com/Sakura520222/astrbot_plugin_LLMPerception)

## ❓ 支持

- 📚 [AstrBot 官方文档](https://astrbot.app)
- 🐛 [问题反馈与建议](https://github.com/Sakura520222/astrbot_plugin_LLMPerception/issues)

## 📄 许可证

本插件遵循 MIT 许可证开源，可自由使用和修改。

