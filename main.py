import json
import time
import datetime
from collections import Counter
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import traceback

TMPL = '''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        /* ... 基础 CSS 保持不变 ... */
        :root {
            --primary: #6c9e6d;
            --bg: #fdfdfd;
            --card-bg: #f4f8f4;
            --text-main: #333;
            --text-sub: #888;
        }
        body { font-family: "MiSans Global", sans-serif; background: #eee; padding: 20px; width: 500px; box-sizing: border-box; margin: 0;}
        .container {
            width: 100%; background: var(--bg); padding: 20px;
            border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            border: 1px dashed #ccc;
            box-sizing: border-box;
        }

        /* ... 头部、统计图样式省略 (保持不变) ... */
        .header { text-align: center; margin-bottom: 20px; }
        .header h1 { color: var(--primary); margin: 0; font-size: 24px; }
        .header p { color: var(--text-sub); font-size: 12px; margin-top: 5px; }
        .section-title {
            border-left: 4px solid var(--primary);
            padding-left: 10px; font-weight: bold; color: var(--text-main);
            margin: 25px 0 15px 0; font-size: 16px;
        }
        .stats-box { display: flex; gap: 10px; }
        .card { background: var(--card-bg); border-radius: 8px; padding: 10px; flex: 1; }
        .user-row { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 6px; }
        .chart { display: flex; align-items: flex-end; height: 100px; gap: 4px; padding-top:10px;}
        .bar { background: #c8e6c9; flex: 1; border-radius: 3px 3px 0 0; transition: height 0.3s; }
        .bar:nth-child(even) { background: #a5d6a7; }

        .topic-item { margin-bottom: 15px; position: relative; padding-left: 15px; }
        .topic-item::before {
            content: "•"; color: var(--primary); position: absolute; left: 0; font-size: 20px; line-height: 14px;
        }
        .topic-time { color: var(--primary); font-size: 12px; font-weight: bold; }

        /* --- Markdown 内容样式 --- */
        .markdown-render {
            font-size: 13px; color: #444; margin-top: 4px; line-height: 1.6;
        }
        /* 针对 Markdown 生成标签的样式修正 */
        .markdown-render p { margin: 0 0 5px 0; }
        .markdown-render strong { color: #2e7d32; font-weight: 700; }
        .markdown-render code {
            background: #f0f0f0; padding: 2px 4px; border-radius: 4px;
            font-family: Consolas, monospace; font-size: 0.9em; color: #c62828;
        }
        .markdown-render ul { margin: 5px 0; padding-left: 20px; }

        .footer-note {
            background: #fff8e1; border: 1px solid #ffe0b2;
            border-radius: 10px; padding: 15px; font-size: 13px; color: #795548;
            margin-top: 30px; position: relative;
        }
        .copyright {
            margin-top: 30px;
            text-align: center;
            border-top: 1px dashed #e0e0e0;
            padding-top: 15px;
        }
        .copyright p {
            margin: 3px 0;
            font-size: 10px;
            color: #aaa;
            font-family: Consolas, "Microsoft YaHei", sans-serif;
        }
        /* 给 "Powered By" 加一点特殊的颜色点缀 */
        .copyright .brand {
            font-weight: bold;
            color: #999;
        }
        .footer-note::before { content: "🌱"; position: absolute; top: -10px; left: 15px; background: #fff8e1; padding: 0 5px;}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{group_name}} 近期热点回顾</h1>
            <p>观察日记 ({{ date }})</p>
        </div>

        <div class="stats-box">
            <div class="card">
                <div style="color:var(--primary); font-weight:bold; margin-bottom:8px;">🌿 活跃之星 Top 5</div>
                {% for user in top_users %}
                <div class="user-row">
                    <span style="font-weight:bold; color:#555">{{ user.name }}</span>
                    <span style="color:var(--primary)">{{ user.count }}条</span>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="section-title">近期话题索引</div>
        {% for topic in topics %}
        <div class="topic-item">
            <div class="topic-time">{{ topic.time_range }}</div>
            <div class="markdown-render">{{ topic.summary }}</div>
        </div>
        {% endfor %}

        <div class="footer-note">
            <strong>{{bot_name}}的悄悄话：</strong><br>
            <div class="markdown-render" style="margin-top:5px;">{{ summary_text }}</div>
        </div>
        <div class="copyright">
            <p>Generated by QQ群总结工具</p>
            <p class="brand">Powered By AstrBot & Google Gemini 3.0 Flash</p>
            <p>Inspired by 小维</p>
        </div>
    </div>

    <script>
        document.addEventListener("DOMContentLoaded", function() {
            // 获取所有需要渲染的容器
            const elements = document.querySelectorAll('.markdown-render');

            elements.forEach(el => {
                // 1. 获取原始文本 (Jinja2 填入的 Markdown)
                // 使用 textContent 可能会丢失换行符，innerText 更好，
                // 或者直接解析 innerHTML (前提是 Jinja 没有转义过度)
                // 这里我们假设 Jinja 输出的是标准文本
                const rawMarkdown = el.innerHTML;

                // 2. 调用 marked.js 进行渲染
                // { breaks: true } 允许回车即换行，不需要打两个空格
                const htmlContent = marked.parse(rawMarkdown, { breaks: true });

                // 3. 替换内容
                el.innerHTML = htmlContent;
            });
        });
    </script>
</body>
</html>
'''

@register("group_summary", "YourName", "群聊总结生成器", "1.2.0")
class GroupSummaryPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config or {}
        self.html_gen = HtmlGenerator()
        self.max_msg_count = self.config["max_msg_count"]
        self.max_query_rounds = self.config["max_query_rounds"]
        self.bot_name = self.config["bot_name"]

    # --- 辅助方法：调用 NapCat API 获取历史消息 ---
    async def fetch_group_history(self, bot, group_id: str):
        """
        分页获取群聊历史消息
        逻辑：获取一批 -> 拿到最旧的一条 seq -> 以该 seq 为终点再获取一批 -> 循环
        """
        all_messages = []
        message_seq = 0 # 用于标记下一次获取的“截止点”

        cutoff_time = time.time() - (24 * 3600)

        logger.info(f"开始获取群 {group_id} 消息，目标上限: {self.max_msg_count}条 / {self.max_query_rounds}轮")

        for round_idx in range(self.max_query_rounds):
            # 1. 检查总数是否超标
            if len(all_messages) >= self.max_msg_count:
                break

            try:
                # 2. 构造 API 参数
                params = {
                    "group_id": group_id,
                    "count": 200,
                    "message_seq":message_seq,
                    "reverseOrder": True,
                }
                # 3. 调用 API
                resp: dict = await bot.api.call_action("get_group_msg_history", **params)

                round_messages = resp["messages"]
                if not round_messages:
                    break
                message_seq = round_messages[0]["message_id"]

                batch_msgs = round_messages
                logger.info(f"Round {round_idx+1}: 获取到 {len(batch_msgs)} 条消息")
                if not batch_msgs:
                    break # 没有更多消息了

                # NapCat 返回通常是 [旧 -> 新] 的顺序
                # 我们需要把这批消息加到总列表里
                # 注意：如果是翻页获取，新获取的批次应该放在总列表的最前面，或者最后统一按时间排序
                all_messages.extend(batch_msgs)

                # 如果这一批里最新的消息都已经超过了24小时，那说明后面的更不用看了，直接停止
                oldest_msg_time = batch_msgs[0].get("time", 0)

                # 如果这一轮抓取的最旧消息都还在 cutoff 之前，说明已经抓够了时间范围
                if oldest_msg_time < cutoff_time:
                    # 虽然这一批里可能有一部分有效，但下一轮肯定都是无效的了，标记结束
                    # (这里不break，让后面统一 process 过滤掉多余的即可)
                    pass

                # 简单的进度日志
                logger.info(f"Round {round_idx+1}: 获取到 {len(batch_msgs)} 条消息")

            except Exception as e:
                logger.error(f"Error: {traceback.format_exc()}")
                logger.info(f"Fetch loop error: {e}")
                break

        # 去重并按时间排序 (防止API返回重叠数据)
        # 使用 message_id 作为唯一键
        # unique_msgs = {msg['message_id']: msg for msg in all_messages if 'message_id' in msg}
        # sorted_msgs = sorted(unique_msgs.values(), key=lambda x: x.get('time', 0))

        return all_messages

    # --- 辅助方法：纯 Python 统计数据 (替代 SQL) ---
    def process_messages(self, messages: list, hours_limit: int = 24):
        """
        处理原始消息列表：
        1. 过滤时间范围
        2. 统计 Top 5 用户
        3. 统计每小时趋势
        4. 生成 LLM 用的纯文本日志
        """
        cutoff_time = time.time() - (hours_limit * 3600)

        valid_msgs = []
        user_counter = Counter()
        trend_counter = Counter()

        # 遍历消息进行过滤和统计
        for msg in messages:
            # NapCat 返回的 timestamp 通常是 int (秒)
            ts = msg.get("time", 0)
            if ts < cutoff_time:
                continue

            sender = msg.get("sender", {})
            nickname = sender.get("card") or sender.get("nickname") or "未知用户"
            content = msg.get("raw_message") or ""  # 获取纯文本或 CQ 码文本

            # 1. 收集有效消息
            valid_msgs.append({
                "time": ts,
                "name": nickname,
                "content": content
            })

            # 2. 统计用户发言数
            user_counter[nickname] += 1

            # 3. 统计小时趋势
            hour_str = datetime.datetime.fromtimestamp(ts).strftime("%H")
            # 简单去掉前导0 (可选，为了匹配 CSS ID 或 字典 Key)
            # hour_int = int(hour_str)
            trend_counter[str(int(hour_str))] += 1

        # 整理 Top 5
        top_users = [{"name": name, "count": count} for name, count in user_counter.most_common(5)]

        # 整理 LLM 日志文本
        chat_log = "\n".join([
            f"[{datetime.datetime.fromtimestamp(m['time']).strftime('%H:%M')}] {m['name']}: {m['content']}"
            for m in valid_msgs
        ])

        return valid_msgs, top_users, dict(trend_counter), chat_log

    @filter.command("总结群聊")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def summarize_group(self, event: AstrMessageEvent):
        group_id = event.get_group_id()
        if not group_id:
            yield event.plain_result("⚠️ 请在群聊内使用本命令。")
            return
        group_info = await event.bot.api.call_action("get_group_info", **{"group_id":group_id})
        logger.info(f"群信息:{group_info}")
        yield event.plain_result("🌱 正在连接云端，下载近期群聊...")

        # 1. 调用 API 获取消息
        # 建议 count 设置大一点，然后在 Python 里通过时间过滤
        raw_messages = await self.fetch_group_history(event.bot, group_id)

        if not raw_messages:
            yield event.plain_result("⚠️ 无法获取群聊历史，可能是 Bot 刚刚启动或 API 不支持。")
            return

        # 2. 本地数据处理
        valid_msgs, top_users, trend, chat_log = self.process_messages(raw_messages, hours_limit=24)

        if not valid_msgs:
            yield event.plain_result("最近 24 小时内似乎没有新的消息记录。")
            return

        # 限制日志长度，防止 LLM Token 溢出
        if len(chat_log) > 12000:
            chat_log = chat_log[-12000:]

        # 3. 构建 Prompt
        prompt = f"""
        你是一个群聊记录员“纱织”。请根据以下的群聊记录（最近24小时），生成一份总结数据。

        【要求】：
        1. 分析 3-8 个主要话题，每个话题包含：时间段（如 2026-01-01 10:00-2026-01-01 11:00）和简短内容。
        2. 写一段“纱织姐姐的悄悄话”作为总结，风格温暖、感性。
        3. 严格返回 JSON 格式：{{"topics": [{{"time_range": "...", "summary": "..."}}],"closing_remark": "..."}}

        【聊天记录】：
        {chat_log}
        """

        yield event.plain_result(f"☁️ 已获取 {len(valid_msgs)} 条有效消息，正在生成分析报告...")

        # 4. 调用 LLM
        try:
            """调用llm回复"""
            provider = (
                    self.context.get_provider_by_id(self.config["provider_id"])
                    or self.context.get_using_provider()
            )
            if not provider:
                yield event.plain_result("❌ 未配置用于文本生成任务的 LLM 提供商。")
                return

            response = await provider.text_chat(prompt, session_id=None)
            clean_json = response.completion_text.replace("```json", "").replace("```", "").strip()
            analysis_data = json.loads(clean_json)
            logger.info(f"LLM 回复: {response}")
        except Exception as e:
            logger.error(f"Traceback Error: {traceback.format_exc()}")
            logger.error(f"LLM Error: {e}")
            analysis_data = {"topics": [], "closing_remark": "纱织姐姐有点累了，没能写出总结..."}

        try:
            # 5. 组装数据并渲染
            render_data = {
                "date": datetime.datetime.now().strftime("%Y.%m.%d"),
                "top_users": top_users,
                "trend": trend,  # Counter 对象可以直接在 Jinja2 中当字典用
                "topics": analysis_data.get("topics", []),
                "summary_text": analysis_data.get("closing_remark", ""),
                "group_name":group_info.get("group_name"),
                "bot_name":self.bot_name
            }
        except Exception as e:
            logger.error(f"Traceback Error: {traceback.format_exc()}")
            yield event.plain_result(f"❌ 沙雕LLM可能返回了不符合要求的数据")
            return
        logger.info(f"渲染数据: {render_data}")
        options = {"quality": 95, "device_scale_factor_level": "ultra","viewport_width":500}
        # 调用 AstrBot 渲染服务
        try:
            img_result = await self.html_render(TMPL,render_data,options=options)
            yield event.image_result(img_result)
        except Exception as e:
            yield event.plain_result(f"❌ 渲染失败: {e}")