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

### 2. Meta（インスタのAPI）
1. https://developers.facebook.com/ に登録してアプリを作る
2. 「Instagram API（Instagramログイン）」を追加し、@futsuu_no_ai をつなぐ
3. アクセストークンを作る（約60日有効）
   ※画面の名前は変わることがあるので、Claudeが画面を見ながら案内します【要確認】

### 3. GitHub に合い言葉と設定を入れる
リポジトリの Settings → Secrets and variables → Actions
- **Secrets** に `IG_ACCESS_TOKEN`（2-3で作ったトークン）
- **Variables** に `LIVE_MODE` = `off`（最初は試し運転）

### 4. 試し運転
1. Actions → 「Instagram auto publish」→ Run workflow（dry_run = true）
2. ログに「投稿する予定の画像とキャプション」が出ればOK（実際には投稿されない）

### 5. 本番
1. 投稿してよいものの `post.json` を `"approved": true` にする
2. 変数 `LIVE_MODE` を `on` にする

### 6. トークンの自動更新（あとでOK）
- トークンは約60日で切れる。`refresh-token.yml` が月2回更新する
- そのために、Secrets に `GH_PAT`（このリポジトリの Secrets を書きかえられるGitHubトークン）を入れる

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
