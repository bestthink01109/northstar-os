# North Star OS v3 Webアプリ版
# iPhone対応ダッシュボード + AIコーチ対話

---

## 0. 背景と目的

現在のNorth Star OS v3はMarkdownファイル（Dashboard_YYYYMMDD.md）をCursor上で管理しており、iPhoneからアクセスできない。BUN_CEOは移動中や外出先でもダッシュボード確認・タスク管理・AIコーチとの対話をiPhoneで完結させたいと希望している。

本計画は、Phase 3-3「Webアプリ版ダッシュボード開発」を前倒しし、AIコーチ対話機能まで含めた本格的なPWA（Progressive Web App）を構築する。

---

## 1. ゴール

| 項目 | 内容 |
|:---|:---|
| iPhoneのホーム画面からアプリとして起動 | PWA対応。Safariの「ホーム画面に追加」でネイティブアプリ風に動作 |
| ダッシュボード全7セクションの閲覧・編集 | Core Vision / Schedule / Tasks / Research / AI Workspace / PM Report / Reflection |
| AIコーチとのチャット対話 | Claude APIを使ったリアルタイムチャット。朝の儀式・決断の書・リフレクションをスマホ上で完結 |
| Googleカレンダー連携 | 予定・タスクの自動取得と表示 |
| タスク管理 | チェック/追加/期限変更をスマホからワンタップ |
| 認証 | BUN_CEO専用。外部からのアクセスを防ぐ |
| 通知 | LINE Notify連携（Phase 2と統合） |

---

## 2. 技術スタック

| レイヤー | 技術 | 選定理由 |
|:---|:---|:---|
| フロントエンド | Next.js 15 (App Router) | React Server Components + PWA対応。Vercelとの最高の相性 |
| UI | モバイルファースト CSS + Framer Motion | ネイティブアプリ級の操作感。滑らかなアニメーション |
| バックエンド / DB | Supabase（東京リージョン） | PostgreSQL + Auth + Realtime + Edge Functions。既にNorth Star OS v3で採用決定済み |
| AIコーチ | Claude Sonnet API (Anthropic) | PM戦略・コーチング対話。既に設計方針で確定済み |
| カレンダー連携 | Google Calendar API (OAuth 2.0) | 予定・タスクの双方向同期 |
| デプロイ | Vercel | 自動デプロイ + Edge Runtime。既に計画済み |
| 認証 | Supabase Auth（メール/パスワード or Magic Link） | BUN_CEO専用のシンプル認証 |
| PWA | next-pwa | Service Worker + オフラインキャッシュ + ホーム画面追加 |

---

## 3. 画面設計

### 3-1. 画面一覧

| # | 画面 | 機能 | 優先度 |
|:---|:---|:---|:---|
| 1 | ログイン | Magic Link認証（メール入力→リンクタップでログイン） | 必須 |
| 2 | ダッシュボード（ホーム） | 今日の予定・緊急タスク・Core Visionを一画面に凝縮 | 必須 |
| 3 | タスク一覧 | 全タスクの閲覧・チェック完了・追加・期限変更 | 必須 |
| 4 | 週間カレンダー | 1-Week All の予定・タスク表示 | 必須 |
| 5 | AIコーチ | チャットUI。朝の儀式・決断の書・リフレクションのテンプレート付き | 必須 |
| 6 | リサーチ | Research Factsの閲覧（カード型UI） | 必須 |
| 7 | AI Workspace | AIプロジェクト一覧・ステータス管理 | 必須 |
| 8 | 設定 | プロフィール・通知設定・テーマ切替 | 後回し可 |

### 3-2. UIコンセプト

- モバイルファースト（iPhone SE〜iPhone 16 Pro Maxまで対応）
- ボトムナビゲーション（ホーム / タスク / AIコーチ / メニュー）
- ダークモード対応（深い紺色ベースのプレミアムUI）
- カード型レイアウト（セクションごとにスワイプ可能）
- ワンタップ操作（タスク完了、AIコーチ起動など）

---

## 4. データベース設計（Supabase PostgreSQL）

### テーブル一覧

```sql
-- ユーザー（BUN_CEO専用だが将来のマルチテナント対応を見据えた設計）
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  display_name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Core Vision（目標管理）
CREATE TABLE core_vision (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  item_key TEXT NOT NULL, -- 'ultimate_ideal', '10year', '5year', etc.
  content TEXT NOT NULL,
  sort_order INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- タスク
CREATE TABLE tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  title TEXT NOT NULL,
  description TEXT,
  client_name TEXT, -- '共生', '信和ミート', '彩', '福岡プラント' etc.
  due_date DATE,
  priority TEXT CHECK (priority IN ('critical', 'high', 'medium', 'low')),
  status TEXT CHECK (status IN ('todo', 'in_progress', 'done', 'cancelled')) DEFAULT 'todo',
  google_calendar_event_id TEXT, -- Googleカレンダーとの紐付け
  sort_order INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 予定（Googleカレンダーからの同期キャッシュ）
CREATE TABLE schedules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  google_event_id TEXT UNIQUE,
  title TEXT NOT NULL,
  description TEXT,
  location TEXT,
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ,
  all_day BOOLEAN DEFAULT FALSE,
  synced_at TIMESTAMPTZ DEFAULT NOW()
);

-- AIコーチ対話履歴
CREATE TABLE coach_conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  session_type TEXT CHECK (session_type IN ('morning_ritual', 'pm_strategy', 'reflection', 'freeform')),
  title TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE coach_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID REFERENCES coach_conversations(id),
  role TEXT CHECK (role IN ('user', 'assistant', 'system')) NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- PM Strategy Report（決断の書）
CREATE TABLE pm_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  report_date DATE NOT NULL,
  confirmed_at TIMESTAMPTZ,
  orders JSONB, -- [{priority: 1, instruction: '...', note: '...'}]
  supplements TEXT,
  conversation_id UUID REFERENCES coach_conversations(id), -- 対話ログへの紐付け
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Reflection（振り返り）
CREATE TABLE reflections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  reflection_date DATE NOT NULL,
  results TEXT,
  feedback TEXT,
  conversation_id UUID REFERENCES coach_conversations(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- AIプロジェクト管理
CREATE TABLE ai_projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  project_code TEXT NOT NULL, -- 'A', 'B', 'C', 'D'
  tag TEXT NOT NULL, -- '[DEV]', '[RSC]', '[FIN]', '[BizDev]', '[MKT]'
  title TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'Phase 1',
  sort_order INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- リサーチファクト
CREATE TABLE research_facts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  category TEXT NOT NULL, -- '熊本県庁', '福岡県庁', 'AIトレンド' etc.
  title TEXT NOT NULL,
  content JSONB, -- 構造化されたリサーチデータ
  source_url TEXT,
  fetched_at TIMESTAMPTZ,
  recommendations TEXT, -- 提言
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 5. AIコーチ機能の設計

### 5-1. システムプロンプト構成

AIコーチには以下のコンテキストを常に注入する：

| コンテキスト | 内容 |
|:---|:---|
| 運営マニュアル（抜粋） | 経営理念、ビジョン、掟、品質ルール |
| Core Vision | 究極の理想状態〜今月のゴール |
| 今日の予定・タスク | Supabaseから動的取得 |
| 直近の決断の書 | 過去3日分 |
| 直近のリフレクション | 過去3日分 |
| 対話履歴 | 当日のセッション全履歴 |

### 5-2. セッションテンプレート

| セッション | トリガー | AIの役割 |
|:---|:---|:---|
| 朝の儀式 | 毎朝ホーム画面表示時 or ワンタップ | 今日の予定・タスクを概観し、優先順位を議論。決断の書を確定 |
| PM Strategy | 随時 | 複数PJへの指示を議論・確定 |
| リフレクション | 夕方19:30通知 or ワンタップ | 今日の全結果を振り返り、翌日フィードバックを策定 |
| フリートーク | 随時 | アイデア壁打ち、事業相談、悩み相談 |

### 5-3. API呼び出し

```
POST /api/coach/chat
{
  session_type: "morning_ritual",
  message: "おはようございます",
  conversation_id: "xxx" // 既存セッション継続時
}
→ Claude Sonnet APIにストリーミングで接続
→ レスポンスをSupabaseに保存しつつフロントにストリーム返却
```

---

## 6. Googleカレンダー連携

| 項目 | 内容 |
|:---|:---|
| 認証方式 | OAuth 2.0（Google Cloud Console でプロジェクト作成 → Calendar API有効化） |
| 同期タイミング | アプリ起動時 + 手動プルリフレッシュ + 30分間隔バックグラウンド |
| 同期範囲 | 今日 + 向こう7日間 |
| 双方向性 | Phase 1は読み取りのみ。Phase 2でタスク→カレンダー書き込み対応 |

---

## 7. ファイル構成

```
northstar-dashboard/
├── .env.local                    # 環境変数（APIキー等）
├── next.config.js
├── package.json
├── public/
│   ├── manifest.json             # PWA設定
│   ├── icons/                    # アプリアイコン各サイズ
│   └── sw.js                     # Service Worker
├── src/
│   ├── app/
│   │   ├── layout.tsx            # ルートレイアウト（ボトムナビ）
│   │   ├── page.tsx              # ホーム（ダッシュボード）
│   │   ├── login/
│   │   │   └── page.tsx          # ログイン画面
│   │   ├── tasks/
│   │   │   └── page.tsx          # タスク一覧
│   │   ├── calendar/
│   │   │   └── page.tsx          # 週間カレンダー
│   │   ├── coach/
│   │   │   └── page.tsx          # AIコーチ対話
│   │   ├── research/
│   │   │   └── page.tsx          # リサーチファクト
│   │   ├── workspace/
│   │   │   └── page.tsx          # AI Workspace
│   │   └── api/
│   │       ├── coach/
│   │       │   └── chat/
│   │       │       └── route.ts  # AIコーチAPIエンドポイント
│   │       ├── calendar/
│   │       │   └── sync/
│   │       │       └── route.ts  # カレンダー同期API
│   │       └── auth/
│   │           └── callback/
│   │               └── route.ts  # 認証コールバック
│   ├── components/
│   │   ├── ui/                   # 共通UIコンポーネント
│   │   │   ├── Card.tsx
│   │   │   ├── BottomNav.tsx
│   │   │   ├── TaskItem.tsx
│   │   │   ├── ChatBubble.tsx
│   │   │   └── PullToRefresh.tsx
│   │   ├── dashboard/            # ダッシュボード固有
│   │   │   ├── CoreVision.tsx
│   │   │   ├── TodaySchedule.tsx
│   │   │   ├── UrgentTasks.tsx
│   │   │   └── QuickActions.tsx
│   │   └── coach/                # AIコーチ固有
│   │       ├── ChatInput.tsx
│   │       ├── SessionSelector.tsx
│   │       └── StreamingMessage.tsx
│   ├── lib/
│   │   ├── supabase/
│   │   │   ├── client.ts         # ブラウザ用Supabaseクライアント
│   │   │   ├── server.ts         # サーバー用Supabaseクライアント
│   │   │   └── types.ts          # DB型定義
│   │   ├── claude/
│   │   │   ├── client.ts         # Claude APIクライアント
│   │   │   └── prompts.ts        # システムプロンプト定義
│   │   └── google/
│   │       └── calendar.ts       # Google Calendar APIクライアント
│   └── styles/
│       └── globals.css           # グローバルCSS（デザインシステム）
└── supabase/
    └── migrations/
        └── 001_initial.sql       # 初期マイグレーション
```

---

## 8. 段階的リリース計画

> [!IMPORTANT]
> 一気に全機能を作るのではなく、使える単位で段階的にリリースし、実運用しながら改善する。

### Step 1：基盤 + ダッシュボード閲覧（1〜2日）

| # | 内容 |
|:---|:---|
| 1-1 | Next.jsプロジェクト作成 + PWA設定 |
| 1-2 | Supabase東京リージョン作成 + テーブルマイグレーション |
| 1-3 | 認証（Magic Link） |
| 1-4 | ホーム画面（Core Vision + 今日の予定 + 緊急タスク表示） |
| 1-5 | 現在のMarkdownダッシュボードの全データをSupabaseに初期投入 |
| 1-6 | Vercelデプロイ + iPhoneホーム画面追加テスト |

この段階のゴール：iPhoneでダッシュボードが見られる状態

### Step 2：タスク管理 + カレンダー連携（1〜2日）

| # | 内容 |
|:---|:---|
| 2-1 | タスク一覧画面（チェック完了・追加・編集・削除） |
| 2-2 | Google Calendar API連携（OAuth 2.0認証） |
| 2-3 | 週間カレンダー画面 |
| 2-4 | プルリフレッシュ対応 |

この段階のゴール：タスクをiPhoneで管理、予定をリアルタイム表示

### Step 3：AIコーチ対話（2〜3日）

| # | 内容 |
|:---|:---|
| 3-1 | Claude API接続（ストリーミングレスポンス） |
| 3-2 | チャットUI（メッセージ送受信・履歴表示） |
| 3-3 | セッションテンプレート（朝の儀式・PM Strategy・リフレクション・フリートーク） |
| 3-4 | コンテキスト注入（Core Vision + 今日の予定 + タスク + 過去の決断の書） |
| 3-5 | 決断の書の自動生成と保存 |

この段階のゴール：朝の儀式〜リフレクションまでiPhoneで完結

### Step 4：リサーチ + AI Workspace + 仕上げ（1〜2日）

| # | 内容 |
|:---|:---|
| 4-1 | リサーチファクト画面（カード型UI） |
| 4-2 | AI Workspace画面（プロジェクト管理） |
| 4-3 | LINE Notify連携（タスク期限アラート） |
| 4-4 | オフラインキャッシュ + パフォーマンス最適化 |
| 4-5 | 全画面動作テスト + UX調整 |

この段階のゴール：North Star OS v3の全機能がiPhoneで動作

---

## 9. 開発コスト見積もり

### 初期コスト

| 項目 | コスト |
|:---|:---|
| Supabase | 無料枠（Free Tier: 500MB DB, 50K MAU） |
| Vercel | 無料枠（Hobby Plan） |
| Claude API | 従量課金（推定 月$10〜30 = 1,500〜4,500円） |
| Google Calendar API | 無料 |
| ドメイン（任意） | 年額1,500円程度（.app等） |

### 月額ランニングコスト

| 項目 | 月額 |
|:---|:---|
| Supabase Free | ¥0 |
| Vercel Hobby | ¥0 |
| Claude API（AIコーチ対話） | ¥1,500〜¥4,500 |
| 合計 | 約¥1,500〜¥4,500/月 |

> [!NOTE]
> North Star OS v3 Phase 2のn8nコスト（月¥7,500〜18,000）とは別枠。
> 将来的にn8nからこのWebアプリのAPIを呼び出す形で統合可能。

---

## 10. ユーザーレビュー必要事項

> [!IMPORTANT]
> 以下の点についてBUN_CEOの判断をお願いします。

1. Supabaseのアカウントは既にお持ちですか？ まだであれば新規作成が必要です（無料）

2. Claude APIキーの準備：Anthropicのアカウントは既にお持ちですか？ APIキーの発行が必要です

3. Google Cloud Consoleのプロジェクト：Calendar APIを有効化するためのGoogleプロジェクトはありますか？

4. Step 1（閲覧専用ダッシュボード）をまず作って、使いながら改善していくアプローチで良いですか？

5. ドメインは取得しますか？（例：northstar.app, bun-ceo.appなど） なくてもVercelの無料ドメイン（xxx.vercel.app）で動作します

6. 開発の着手タイミング：今日の代行業務の後に着手しますか？ それとも別日に集中して取り組みますか？

---

## 11. 検証計画

### 自動テスト
- 各API Route の動作確認（curl / httpie）
- Supabase接続テスト
- Claude APIストリーミングテスト

### ブラウザテスト
- iPhone Safari での PWA動作確認
- ホーム画面追加 → スプラッシュスクリーン → 起動
- 各画面の表示・操作テスト

### 手動検証
- BUN_CEOのiPhoneでの実地テスト
- 朝の儀式フロー（AIコーチ対話 → 決断の書確定）のエンドツーエンド動作
- タスクの完了操作（ワンタップ）の体感速度
