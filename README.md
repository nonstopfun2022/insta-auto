# insta-auto：Instagram 自動投稿

@futsuu_no_ai のフィード投稿（カルーセル）を、決めた日時に自動で投稿するしくみです。

## しくみ
- `posts/<投稿名>/` に「画像（01.jpg〜）」「キャプション（caption.txt）」「予定（post.json）」を置く
- GitHub Actions が **1時間ごと（毎時5分ごろ）** に動き、条件に合う投稿を **1回に1本だけ** 投稿する
- 投稿したものは `published.csv` に記録され、二度と投稿されない

### 投稿される条件（3つ全部そろったときだけ）
1. `post.json` の `"approved"` が `true`（miwaさんのOK）
2. `"publish_at"` の日時を過ぎている（日本時間なら末尾に `+09:00`）
3. リポジトリの変数 `LIVE_MODE` が `on`（`on` 以外のときは試し運転で、投稿しない）

## できないこと
- **ストーリーズのリンクスタンプ**（APIでは付けられない）→ MiriCanvasのストーリーズはスマホで投稿する
- 投稿の時刻は数分〜十数分おくれることがある（GitHub Actions の都合）

---

## はじめの設定（miwaさんが行う）

> パスワードやトークン（合い言葉）は、Claudeには入力できません。チャットにも書かないでください。

### 1. GitHub
1. https://github.com/signup でアカウントを作る
2. 新しいリポジトリを作る：名前 `insta-auto`、**Public（公開）**、ほかは空のまま
3. このフォルダの中身をアップロードする（Claudeが手順を案内します）

### 2. Meta（インスタのAPI）※2026-11-09 設定ずみ
- 開発者アプリ：futsuu-autopost（開発モード）
- ビジネスポートフォリオ：ふつうの社会人のai活用（@futsuu_no_ai を追加ずみ）
- システムユーザー：autopost-bot（アプリと @futsuu_no_ai〔コンテンツ権限のみ〕を割り当て）
- トークン：autopost-bot の「トークンを生成」で作成（有効期限なし、instagram_basic と instagram_content_publish）
- ※新しいアプリでは「Instagramログイン」のトークンは使えないため、この方法にした

### 3. GitHub に合い言葉と設定を入れる ※設定ずみ
リポジトリの Settings → Secrets and variables → Actions
- **Secrets** に `IG_ACCESS_TOKEN`（システムユーザーのトークン）
- **Variables** に `IG_USER_ID` = `17841462105871043`（@futsuu_no_ai のID）
- **Variables** に `LIVE_MODE` = `off`（最初は試し運転）

### 4. 試し運転
1. Actions → 「Instagram auto publish」→ Run workflow（dry_run = true）
2. ログに「投稿する予定の画像とキャプション」が出ればOK（実際には投稿されない）

### 5. 本番
1. 投稿してよいものの `post.json` を `"approved": true` にする
2. 変数 `LIVE_MODE` を `on` にする

### 6. トークンについて
- システムユーザーのトークンは期限なし。更新はいらない
- 試し運転のログに `connection OK: @futsuu_no_ai` と出ればつながっている
- トークンがもれたかもと思ったら、autopost-bot の「トークンを取り消す」→ 作り直して Secrets を上書きする

---

## 新しい投稿を足すとき
1. 画像を作る（`images/instagram/...` にPNG）
2. `scripts/prepare_insta.ps1` の対応表に足して実行 → JPEG が `posts/<投稿名>/` に入る
3. `caption.txt` と `post.json` を作る
4. GitHub にアップロードする

## 注意
- 公開リポジトリなので、置いた画像とキャプションは投稿前でも見られる。下書きや個人情報は置かない
- 投稿の上限は24時間で50件または100件（公式の説明が食いちがっている）【要確認】。このしくみは1時間に1本まで
- 広告の投稿（PR）は、A8の提携承認と投稿日の料金確認がすんでから `approved` を `true` にする
