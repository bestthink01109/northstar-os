#!/usr/bin/env node
/**
 * NorthStar OS - セッション書き出しスクリプト
 * 使い方: node session_export.js [出力ファイル]
 *
 * Antigravity など任意のAIツールにセッション内容を渡すためのスクリプト。
 * 今日のダッシュボードと前回のCOOコンテキストを1つのテキストに束ねて出力する。
 *
 * 出力ファイルを省略すると stdout に出力。
 * 例: node session_export.js /tmp/session.txt
 */
const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');

const KEY_FILE     = path.join(process.env.HOME, 'Downloads/fifth-sprite-492523-i8-8a32ca4d8877.json');
const OAUTH_FILE   = path.join(process.env.HOME, 'Downloads/client_secret_750072023351-kej7sa596e299guqi9h60jgtf1p6m0vo.apps.googleusercontent.com.json');
const TOKEN_FILE   = path.join(__dirname, 'oauth_tokens.json');
const DAILY_REPORT = '1SGCPerV8CCHT6CcDI8-E6G2JbbmNmsp8';
const MAIN_CAL     = 'bestthink01109@gmail.com';
const TASK_CAL     = 'a0c7e0a0c3b9038b4a54b546d6119480d08d047ac3676811ea6fd1b00da46dc2@group.calendar.google.com';

async function getAuth() {
  return new google.auth.GoogleAuth({ keyFile: KEY_FILE, scopes: ['https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/calendar'] });
}
async function getOAuth() {
  const c = JSON.parse(fs.readFileSync(OAUTH_FILE)).installed;
  const auth = new google.auth.OAuth2(c.client_id, c.client_secret, c.redirect_uris[0]);
  auth.setCredentials(JSON.parse(fs.readFileSync(TOKEN_FILE)));
  return auth;
}
function getTodayJST() {
  const j = new Date(Date.now() + 9*60*60*1000);
  const y = j.getUTCFullYear(), m = String(j.getUTCMonth()+1).padStart(2,'0'), d = String(j.getUTCDate()).padStart(2,'0');
  const w = ['日','月','火','水','木','金','土'][j.getUTCDay()];
  return { date:`${y}-${m}-${d}`, label:`${y}年${m}月${d}日（${w}）`, compact:`${y}${m}${d}` };
}

async function main() {
  const today = getTodayJST();
  const outFile = process.argv[2] || null;
  const lines = [];

  lines.push('='.repeat(60));
  lines.push('NorthStar OS ダッシュボードセッション');
  lines.push(`日付: ${today.label}`);
  lines.push('='.repeat(60));
  lines.push('');
  lines.push('【あなたの役割】');
  lines.push('あなたはBUN社長（赤瀬文成）のCOO AIです。以下のセッションを進行してください。');
  lines.push('');
  lines.push('【COO基本ルール】');
  lines.push('- お金・契約・大きな方向性の判断は必ず社長に上げる');
  lines.push('- タスクは削除禁止。完了時は「[完了]」と書き換える');
  lines.push('- 省略・手抜き禁止');
  lines.push('- カレンダー: 予定はメインカレンダー、タスクはBUN_CEOカレンダーに分離');
  lines.push('');
  lines.push('【セッション進行順】');
  lines.push('#1 Core Vision コーチング');
  lines.push('  → ビジョン・タイムラインを確認。より具体化するコーチング質問をする。変更があれば記録。');
  lines.push('#2 Today\'s Schedule & Tasks');
  lines.push('  → 今日の予定・タスクを確認。優先順位をAIと議論。変更はCOMMITブロックで記録。');
  lines.push('#3 1-Week Strategic Outlook');
  lines.push('  → 今週の展望を確認・修正。');
  lines.push('#4 Research Facts');
  lines.push('  → RSCリサーチ内容をCOOとして報告・議論。');
  lines.push('#5 AI Task Workspace');
  lines.push('  → 積み残しと今日の開発/調査タスクをCOOとして報告。社長が方向性を決定。');
  lines.push('#6 COO Strategy Report');
  lines.push('  → #4,5を踏まえ今日の最終方針をまとめる。社長が承認。');
  lines.push('#7 Reflection（夕方セッションの場合）');
  lines.push('  → 今日の結果確認。COOから会社報告。明日の方向性を確定。');
  lines.push('');
  lines.push('─'.repeat(60));
  lines.push('【セッション終了時の必須出力フォーマット】');
  lines.push('変更があったセクションをこのフォーマットで出力すること:');
  lines.push('');
  lines.push('===SESSION_OUTPUT_START===');
  lines.push('');
  lines.push('DASHBOARD_UPDATE:');
  lines.push('（更新後のダッシュボード全文をここに）');
  lines.push('END_DASHBOARD');
  lines.push('');
  lines.push('（カレンダー変更がある場合のみ）');
  lines.push('CALENDAR_ADD_TASK: タイトル | YYYY-MM-DD');
  lines.push('CALENDAR_ADD_EVENT: タイトル | YYYY-MM-DD | HH:MM | メインカレンダーorタスクカレンダー');
  lines.push('CALENDAR_COMPLETE: eventId（[完了]にするタスクのID）');
  lines.push('CALENDAR_UPDATE: eventId | calendarId | field | value  # field: title/date/time');
  lines.push('');
  lines.push('（Signal DBに記録する場合）');
  lines.push('SIGNAL_DB: ランク(S/A/B/C) | シグナル本文 | ソース');
  lines.push('');
  lines.push('===SESSION_OUTPUT_END===');
  lines.push('─'.repeat(60));
  lines.push('');

  // 今日のダッシュボードを読み込む
  lines.push('【今日のダッシュボード】');
  lines.push('');
  try {
    const auth = await getAuth();
    const drive = google.drive({ version:'v3', auth });
    const found = await drive.files.list({
      q: `name='Dashboard_${today.compact}.md' and '${DAILY_REPORT}' in parents and trashed=false`,
      fields: 'files(id,name)',
    });
    if (found.data.files.length > 0) {
      const content = await drive.files.get({ fileId:found.data.files[0].id, alt:'media' }, { responseType:'text' });
      lines.push(content.data);
    } else {
      lines.push('（今日のダッシュボードがありません。node drive.js create-dashboard で作成してください）');
    }
  } catch(e) {
    lines.push('（ダッシュボード読み込みエラー: ' + e.message + '）');
  }

  lines.push('');
  lines.push('─'.repeat(60));

  // 最新COOコンテキストを読み込む
  lines.push('【前回セッションのCOOコンテキスト（最新）】');
  lines.push('');
  try {
    const auth = await getAuth();
    const drive = google.drive({ version:'v3', auth });
    const found = await drive.files.list({
      q: `name contains 'COO_Context_' and '${DAILY_REPORT}' in parents and trashed=false`,
      fields: 'files(id,name,modifiedTime)', orderBy:'modifiedTime desc', pageSize:1,
    });
    if (found.data.files.length > 0) {
      const content = await drive.files.get({ fileId:found.data.files[0].id, alt:'media' }, { responseType:'text' });
      lines.push(`ファイル: ${found.data.files[0].name}`);
      lines.push(content.data);
    } else {
      lines.push('（COOコンテキストファイルなし - 初回セッション）');
    }
  } catch(e) {
    lines.push('（COOコンテキスト読み込みエラー）');
  }

  lines.push('');
  lines.push('─'.repeat(60));
  lines.push('【カレンダーID（変更コマンド用）】');
  lines.push('メインカレンダー: ' + MAIN_CAL);
  lines.push('BUN_CEOタスク:   ' + TASK_CAL);
  lines.push('─'.repeat(60));
  lines.push('');
  lines.push('上記をすべて読んだ後、「セッションを開始します」と言ってセッションを始めてください。');
  lines.push('まず今日の日付と天気・気分を確認してから #1 Core Vision のコーチングを始めてください。');
  lines.push('');

  const output = lines.join('\n');
  if (outFile) {
    fs.writeFileSync(outFile, output, 'utf8');
    console.error(`✅ セッションファイルを保存しました: ${outFile}`);
    console.error(`   Antigravityに貼り付けてセッションを開始してください。`);
  } else {
    process.stdout.write(output);
  }
}

main().catch(e => { console.error('エラー:', e.message); process.exit(1); });
