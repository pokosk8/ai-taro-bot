# ai-taro-bot

Discord でメンション（`@AI太郎`）されたら、Claude が返事をする最小構成の Bot です。
AI社員に何をさせるかはまだ決めていないので、まずは「動くもの」を置いています。

## 仕組み

- `bot.py` … Bot 本体。メンションされたメッセージを Claude に渡して、返事を返信します
- 各チャンネルの直近 10 往復ぶんだけ、メモリ上で会話を覚えます（再起動すると消えます）
- 既定のモデルは `claude-haiku-5-5`（安くて速いモデル）。環境変数 `CLAUDE_MODEL` で変えられます
- 人格・口調は `bot.py` の `SYSTEM_PROMPT` を書き換えるだけで変わります

## 必要な環境変数

| 名前 | 中身 |
| --- | --- |
| `DISCORD_BOT_TOKEN` | Discord Developer Portal の Bot ページで作ったトークン |
| `ANTHROPIC_API_KEY` | Anthropic の API キー（`sk-ant-` で始まるもの） |
| `CLAUDE_MODEL` | （任意）使うモデル名 |

**キーやトークンはコードに書かず、GitHub にも上げないこと。**
ローカルで試すときは `.env` に書けば、`.gitignore` で除外されます。

## Discord 側の設定

- Developer Portal の Bot ページで **Message Content Intent** を ON にする
- OAuth2 の URL ジェネレーターで、スコープ `bot`、権限は「チャンネルを見る」「メッセージを送信」「メッセージ履歴を読む」だけにして、サーバーに招待する

## Railway で動かす（スマホのブラウザだけでできます）

1. [railway.com](https://railway.com) に GitHub アカウントでログインする
2. **New Project** → **Deploy from GitHub repo** → このリポジトリを選ぶ
   （プライベートのリポジトリなので、Railway に GitHub のアクセスを許可する）
3. 作られたサービスの **Variables** に `DISCORD_BOT_TOKEN` と `ANTHROPIC_API_KEY` を追加する
4. デプロイが終わったら、ログに `ログインしました: AI太郎...` と出れば成功
5. Discord でメンションして話しかける

`railway.json` で起動コマンド（`python bot.py`）を指定しています。
この Bot は Web サーバーではないので、ドメインの公開（Generate Domain）は不要です。

## パソコンで試すとき

```bash
pip install -r requirements.txt
export DISCORD_BOT_TOKEN=...
export ANTHROPIC_API_KEY=...
python bot.py
```

## 止めたいとき

Railway のサービスを停止（または削除）すれば、課金も止まります。
