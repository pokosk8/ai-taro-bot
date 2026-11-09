"""AI太郎 — メンションされたら Claude で返事する Discord Bot（最小構成）。

必要な環境変数:
  DISCORD_BOT_TOKEN  Discord Developer Portal で作った Bot のトークン
  ANTHROPIC_API_KEY  Anthropic の API キー (sk-ant-...)
任意:
  CLAUDE_MODEL       使うモデル名（省略時は claude-haiku-5-5）
"""

import logging
import os
import sys
from collections import defaultdict, deque

import anthropic
import discord

MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-5-5")
MAX_TOKENS = 1024
# 1チャンネルごとに覚えておくやりとりの数（1往復 = 2件）。メモリ上だけなので再起動すると消える。
HISTORY_TURNS = 10
DISCORD_LIMIT = 2000

# AI社員の人格・口調はここを書き換えるだけで変えられる。
SYSTEM_PROMPT = (
    "あなたは「AI太郎」という名前の、Discordサーバーにいるアシスタントです。"
    "日本語で、親しみやすく簡潔に答えてください。"
    "分からないことは正直に分からないと伝えてください。"
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ai-taro")


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        log.error("環境変数 %s が設定されていません", name)
        sys.exit(1)
    return value


DISCORD_TOKEN = require_env("DISCORD_BOT_TOKEN")
claude = anthropic.AsyncAnthropic(api_key=require_env("ANTHROPIC_API_KEY"))

intents = discord.Intents.default()
intents.message_content = True  # Developer Portal 側でも Message Content Intent を ON にしておくこと
client = discord.Client(intents=intents)

# channel_id -> 直近のやりとり [{"role": ..., "content": ...}, ...]
history: dict[int, deque] = defaultdict(lambda: deque(maxlen=HISTORY_TURNS * 2))


def split_message(text: str, limit: int = DISCORD_LIMIT) -> list[str]:
    """Discord の文字数上限に収まるよう、できるだけ改行位置で分割する。"""
    chunks = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut <= 0:
            cut = limit
        chunks.append(text[:cut])
        text = text[cut:].lstrip("\n")
    if text:
        chunks.append(text)
    return chunks


def strip_mention(message: discord.Message) -> str:
    text = message.content
    for mention in (f"<@{client.user.id}>", f"<@!{client.user.id}>"):
        text = text.replace(mention, "")
    return text.strip()


@client.event
async def on_ready():
    log.info("ログインしました: %s (model=%s)", client.user, MODEL)


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if client.user not in message.mentions:
        return

    text = strip_mention(message)
    if not text:
        await message.reply("呼んだ？なんでも聞いてな。")
        return

    channel_history = history[message.channel.id]
    messages = list(channel_history) + [{"role": "user", "content": text}]

    async with message.channel.typing():
        try:
            response = await claude.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=messages,
            )
        except anthropic.APIError as e:
            log.exception("Claude API エラー")
            await message.reply(f"ごめん、Claudeを呼ぶのに失敗した…（{type(e).__name__}）")
            return

    reply = "".join(b.text for b in response.content if b.type == "text").strip()
    if not reply:
        reply = "（返事が空っぽやった。もう一回聞いてみて）"

    # 成功したときだけ履歴に積む（user → assistant の順番を崩さないため）
    channel_history.append({"role": "user", "content": text})
    channel_history.append({"role": "assistant", "content": reply})

    first = True
    for chunk in split_message(reply):
        if first:
            await message.reply(chunk)
            first = False
        else:
            await message.channel.send(chunk)


if __name__ == "__main__":
    client.run(DISCORD_TOKEN, log_handler=None)
