#!/usr/bin/env node
/**
 * Google Drive / Calendar Helper - Claude Code用
 * サービスアカウントで認証してGoogle Drive/Calendarを操作する
 *
 * 使い方:
 *   node drive.js list [folderId]                          - フォルダ内のファイル一覧
 *   node drive.js read <fileId>                            - ファイルの内容を読む
 *   node drive.js search <keyword>                         - キーワードでファイル検索
 *   node drive.js mkdir <name> [parentId]                  - フォルダ作成
 *   node drive.js write <fileId> [filePath]                - ファイルを更新（ファイルまたはstdin）
 *   node drive.js create <name> <parentId> [filePath]      - 新規テキストファイル作成
 *
 *   node drive.js today-dashboard                          - 今日のDashboardファイル情報
 *   node drive.js read-today                               - 今日のDashboard内容を読む
 *   node drive.js write-today [filePath]                   - 今日のDashboardを更新
 *   node drive.js create-dashboard                         - 今日のDashboardを新規作成
 *
 *   node drive.js events [calendarId]                      - 今後1週間の予定一覧
 *   node drive.js events-range <calId> <from> <to>         - 期間指定で予定一覧
 *   node drive.js get-event <calId> <eventId>              - イベント詳細取得
 *   node drive.js add-event <calId> <title> <date> [time]  - 予定追加
 *   node drive.js add-task <title> <date>                  - BUN_CEOタスク追加
 *   node drive.js complete-task <eventId> [calId]          - タスクを[完了]にする
 *   node drive.js update-event <calId> <eventId> <field> <value>  - 予定更新
 *                                                            field: title/date/time
 *   node drive.js calendars                                - カレンダー一覧
 *
 * 前提条件:
 *   - ~/Downloads/ にサービスアカウントJSONキーファイルが必要
 *   - ~/Downloads/ にOAuth2クライアントJSONファイルが必要
 *   - 同ディレクトリに oauth_tokens.json が必要（初回: node drive.js auth-setup）
 *   - npm install googleapis
 */

const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');

// ─── 設定（環境に合わせて変更）────────────────────────────────────
const KEY_FILE = path.join(process.env.HOME, 'Downloads/fifth-sprite-492523-i8-8a32ca4d8877.json');
const OAUTH_CLIENT_FILE = path.join(process.env.HOME, 'Downloads/client_secret_750072023351-kej7sa596e299guqi9h60jgtf1p6m0vo.apps.googleusercontent.com.json');
const TOKEN_FILE = path.join(__dirname, 'oauth_tokens.json');

const SCOPES = [
  'https://www.googleapis.com/auth/drive',
  'https://www.googleapis.com/auth/calendar',
];
const DRIVE_WRITE_SCOPES = ['https://www.googleapis.com/auth/drive'];

// カレンダーID定数
const MAIN_CAL = 'bestthink01109@gmail.com';
const TASK_CAL = 'a0c7e0a0c3b9038b4a54b546d6119480d08d047ac3676811ea6fd1b00da46dc2@group.calendar.google.com';

// ダッシュボード保存先フォルダID
const DAILY_REPORT_FOLDER = '1SGCPerV8CCHT6CcDI8-E6G2JbbmNmsp8';

// ─── 認証 ─────────────────────────────────────────────────────────

// サービスアカウント認証（読み取り・Calendar）
async function getAuth() {
  const auth = new google.auth.GoogleAuth({ keyFile: KEY_FILE, scopes: SCOPES });
  return auth;
}

// ユーザーOAuth2認証（Drive書き込み用）
async function getOAuthClient() {
  if (!fs.existsSync(OAUTH_CLIENT_FILE)) {
    throw new Error('OAuth2クライアントファイルが見つかりません: ' + OAUTH_CLIENT_FILE);
  }
  const clientData = JSON.parse(fs.readFileSync(OAUTH_CLIENT_FILE));
  const { client_id, client_secret, redirect_uris } = clientData.installed;
  const oauth2Client = new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);

  if (!fs.existsSync(TOKEN_FILE)) {
    throw new Error('OAuth2トークンが未設定です。先に実行してください: node drive.js auth-setup');
  }
  const tokens = JSON.parse(fs.readFileSync(TOKEN_FILE));
  oauth2Client.setCredentials(tokens);

  // トークン自動更新時に保存
  oauth2Client.on('tokens', (newTokens) => {
    const current = JSON.parse(fs.readFileSync(TOKEN_FILE));
    const merged = { ...current, ...newTokens };
    fs.writeFileSync(TOKEN_FILE, JSON.stringify(merged, null, 2));
  });
  return oauth2Client;
}

// OAuth2セットアップ（初回のみ実行）
async function authSetup() {
  const clientData = JSON.parse(fs.readFileSync(OAUTH_CLIENT_FILE));
  const { client_id, client_secret, redirect_uris } = clientData.installed;
  const oauth2Client = new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);

  const authUrl = oauth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: DRIVE_WRITE_SCOPES,
    prompt: 'consent',
  });

  console.log('以下のURLをブラウザで開いて認証してください:\n');
  console.log(authUrl);
  console.log('\n認証後に表示されるコードを入力してください:');

  const readline = require('readline');
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const code = await new Promise(resolve => rl.question('コード: ', answer => { rl.close(); resolve(answer.trim()); }));

  const { tokens } = await oauth2Client.getToken(code);
  fs.writeFileSync(TOKEN_FILE, JSON.stringify(tokens, null, 2));
  console.log('✅ OAuth2認証完了! トークン保存:', TOKEN_FILE);
}

// ─── ユーティリティ ───────────────────────────────────────────────

function readStdin() {
  return new Promise(resolve => {
    let data = '';
    process.stdin.on('data', chunk => data += chunk);
    process.stdin.on('end', () => resolve(data));
  });
}

function getTodayJST() {
  const now = new Date();
  const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  const y = jst.getUTCFullYear();
  const m = String(jst.getUTCMonth() + 1).padStart(2, '0');
  const d = String(jst.getUTCDate()).padStart(2, '0');
  const weekDay = ['日', '月', '火', '水', '木', '金', '土'][jst.getUTCDay()];
  return {
    date: `${y}-${m}-${d}`,
    label: `${y}年${m}月${d}日（${weekDay}）`,
    compact: `${y}${m}${d}`,
  };
}

function fmtEventTime(e) {
  const s = e.start?.dateTime || e.start?.date || '';
  return s.includes('T') ? s.substring(11, 16) : '終日';
}

function fmtEventDate(e) {
  const s = e.start?.dateTime || e.start?.date || '';
  return s.substring(5, 10).replace('-', '/');
}

// ─── Drive操作 ────────────────────────────────────────────────────

async function listFiles(folderId = 'root') {
  const auth = await getAuth();
  const drive = google.drive({ version: 'v3', auth });
  const response = await drive.files.list({
    q: `'${folderId}' in parents and trashed=false`,
    fields: 'files(id, name, mimeType, modifiedTime, size)',
    pageSize: 100, orderBy: 'name',
  });
  const files = response.data.files || [];
  files.forEach(f => {
    const type = f.mimeType === 'application/vnd.google-apps.folder' ? '[DIR]' : '[FILE]';
    const size = f.size ? ` (${Math.round(f.size / 1024)}KB)` : '';
    console.log(`${type} ${f.name}${size} | id: ${f.id}`);
  });
}

async function readFile(fileId) {
  const auth = await getAuth();
  const drive = google.drive({ version: 'v3', auth });
  const meta = await drive.files.get({ fileId, fields: 'name, mimeType' });
  const mimeType = meta.data.mimeType;
  if (mimeType.startsWith('application/vnd.google-apps')) {
    const exportMime = mimeType.includes('spreadsheet') ? 'text/csv'
      : mimeType.includes('document') ? 'text/plain' : 'text/plain';
    const response = await drive.files.export({ fileId, mimeType: exportMime }, { responseType: 'text' });
    console.log(`=== ${meta.data.name} ===`);
    console.log(response.data);
  } else {
    const response = await drive.files.get({ fileId, alt: 'media' }, { responseType: 'text' });
    console.log(`=== ${meta.data.name} ===`);
    console.log(response.data);
  }
}

async function writeFile(fileId, filePath) {
  const auth = await getOAuthClient();
  const drive = google.drive({ version: 'v3', auth });
  const content = filePath ? fs.readFileSync(filePath, 'utf8') : await readStdin();
  const { Readable } = require('stream');
  await drive.files.update({ fileId, media: { mimeType: 'text/plain', body: Readable.from([content]) } });
  console.log(`✅ 書き込み完了: ${fileId}`);
}

async function createFile(name, parentId, filePath) {
  const auth = await getOAuthClient();
  const drive = google.drive({ version: 'v3', auth });
  let content = '';
  if (filePath) { content = fs.readFileSync(filePath, 'utf8'); }
  else if (!process.stdin.isTTY) { content = await readStdin(); }
  const { Readable } = require('stream');
  const response = await drive.files.create({
    requestBody: { name, mimeType: 'text/plain', ...(parentId && { parents: [parentId] }) },
    media: { mimeType: 'text/plain', body: Readable.from([content]) },
    fields: 'id, name, webViewLink',
  });
  console.log(`✅ 作成完了: ${response.data.name}`);
  console.log(`id: ${response.data.id}`);
  console.log(`url: ${response.data.webViewLink}`);
  return response.data;
}

async function searchFiles(keyword) {
  const auth = await getAuth();
  const drive = google.drive({ version: 'v3', auth });
  const response = await drive.files.list({
    q: `name contains '${keyword}' and trashed=false`,
    fields: 'files(id, name, mimeType, parents, modifiedTime)', pageSize: 50,
  });
  const files = response.data.files || [];
  if (files.length === 0) { console.log('見つかりませんでした'); return; }
  files.forEach(f => {
    const type = f.mimeType === 'application/vnd.google-apps.folder' ? '[DIR]' : '[FILE]';
    console.log(`${type} ${f.name} | id: ${f.id} | 更新: ${f.modifiedTime}`);
  });
}

async function mkdir(name, parentId) {
  const auth = await getAuth();
  const drive = google.drive({ version: 'v3', auth });
  const response = await drive.files.create({
    requestBody: { name, mimeType: 'application/vnd.google-apps.folder', ...(parentId && { parents: [parentId] }) },
    fields: 'id, name',
  });
  console.log(`フォルダ作成完了: ${response.data.name} (id: ${response.data.id})`);
}

async function listShared() {
  const auth = await getAuth();
  const drive = google.drive({ version: 'v3', auth });
  const response = await drive.files.list({
    q: `sharedWithMe=true and trashed=false`,
    fields: 'files(id, name, mimeType, modifiedTime)', pageSize: 100,
  });
  const files = response.data.files || [];
  if (files.length === 0) { console.log('共有されているファイルはありません'); return; }
  files.forEach(f => {
    const type = f.mimeType === 'application/vnd.google-apps.folder' ? '[DIR]' : '[FILE]';
    console.log(`${type} ${f.name} | id: ${f.id}`);
  });
}

// ─── Dashboard操作 ────────────────────────────────────────────────

async function findTodayDashboard() {
  const auth = await getAuth();
  const drive = google.drive({ version: 'v3', auth });
  const { compact } = getTodayJST();
  const filename = `Dashboard_${compact}.md`;
  const response = await drive.files.list({
    q: `name='${filename}' and '${DAILY_REPORT_FOLDER}' in parents and trashed=false`,
    fields: 'files(id, name, webViewLink)',
  });
  const files = response.data.files || [];
  return files.length > 0 ? files[0] : null;
}

async function todayDashboard() {
  const { compact } = getTodayJST();
  const file = await findTodayDashboard();
  if (!file) { console.log(`Dashboard_${compact}.md は未作成です。create-dashboard で作成してください。`); return; }
  console.log(`id: ${file.id}\nname: ${file.name}\nurl: ${file.webViewLink}`);
}

async function readTodayDashboard() {
  const file = await findTodayDashboard();
  if (!file) { console.log('今日のダッシュボードが見つかりません。create-dashboard で作成してください。'); return; }
  await readFile(file.id);
}

async function writeTodayDashboard(filePath) {
  const file = await findTodayDashboard();
  if (!file) { console.log('今日のダッシュボードが見つかりません。create-dashboard で作成してください。'); return; }
  await writeFile(file.id, filePath);
}

async function createDashboard() {
  const auth = await getAuth();
  const drive = google.drive({ version: 'v3', auth });
  const calendar = google.calendar({ version: 'v3', auth });
  const { compact, label, date } = getTodayJST();
  const filename = `Dashboard_${compact}.md`;

  const existing = await findTodayDashboard();
  if (existing) {
    console.log(`既存: ${filename} (id: ${existing.id})`);
    console.log(`url: ${existing.webViewLink}`);
    return;
  }

  const timeMin = new Date(date + 'T00:00:00+09:00').toISOString();
  const timeMax = new Date(new Date(date + 'T00:00:00+09:00').getTime() + 7 * 24 * 60 * 60 * 1000).toISOString();

  const [mainCal, taskCal] = await Promise.all([
    calendar.events.list({ calendarId: MAIN_CAL, timeMin, timeMax, singleEvents: true, orderBy: 'startTime', maxResults: 30 }),
    calendar.events.list({ calendarId: TASK_CAL, timeMin, timeMax, singleEvents: true, orderBy: 'startTime', maxResults: 30 }),
  ]);

  const allEvents = mainCal.data.items || [];
  const allTasks = taskCal.data.items || [];
  const todayEvents = allEvents.filter(e => (e.start?.dateTime || e.start?.date || '').substring(0, 10) === date);
  const weekEvents = allEvents.filter(e => (e.start?.dateTime || e.start?.date || '').substring(0, 10) > date);
  const todayTasks = allTasks.filter(e => (e.start?.dateTime || e.start?.date || '').substring(0, 10) <= date);
  const weekTasks = allTasks.filter(e => (e.start?.dateTime || e.start?.date || '').substring(0, 10) > date);

  const fmtSchedule = e => `・${fmtEventTime(e)} ${e.summary || '(無題)'}  [id:${e.id}]`;
  const fmtTask = e => `・[ ] ${e.summary || '(無題)'}  [id:${e.id}]`;
  const fmtWeek = e => `・${fmtEventDate(e)} ${e.summary || '(無題)'}  [id:${e.id}]`;

  // CoreVision.md がDriveにあれば読み込む
  let coreVision = '（CoreVision.md を Daily_Report フォルダに配置してください）';
  try {
    const cvSearch = await drive.files.list({
      q: `name='CoreVision.md' and '${DAILY_REPORT_FOLDER}' in parents and trashed=false`,
      fields: 'files(id)',
    });
    if (cvSearch.data.files.length > 0) {
      const cvResp = await drive.files.get({ fileId: cvSearch.data.files[0].id, alt: 'media' }, { responseType: 'text' });
      coreVision = cvResp.data;
    }
  } catch (e) { /* use default */ }

  const content = `# 📊 NorthStar Dashboard | ${label}\n\n` +
    `> n8n自動作成: ${new Date().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })}\n\n---\n\n` +
    `## 1. Core Vision\n\n${coreVision}\n\n---\n\n` +
    `## 2. Today's Schedule & Tasks（ALL）\n\n### 📅 本日の予定\n` +
    `${todayEvents.length ? todayEvents.map(fmtSchedule).join('\n') : '予定なし'}\n\n### ✅ 本日のタスク\n` +
    `${todayTasks.length ? todayTasks.map(fmtTask).join('\n') : 'タスクなし'}\n\n---\n\n` +
    `## 3. 1-Week Strategic Outlook\n\n### 📆 今週の予定\n` +
    `${weekEvents.length ? weekEvents.slice(0, 10).map(fmtWeek).join('\n') : '予定なし'}\n\n### 📋 今週のタスク\n` +
    `${weekTasks.length ? weekTasks.slice(0, 10).map(fmtWeek).join('\n') : 'タスクなし'}\n\n---\n\n` +
    `## 4. Research Facts\n> n8n朝6:00 自動入力\n\n[本日未更新]\n\n---\n\n` +
    `## 5. AI Task Workspace\n\n[COO記入欄]\n\n---\n\n` +
    `## 6. COO Strategy Report【決断の書】\n\n[本日の最終方針]\n\n【 】Massive Action Switch\n\n---\n\n` +
    `## 7. Reflection (Check & Act)\n> n8n夕19:00 自動入力\n\n### 社長の今日の結果\n[未記入]\n\n### COOからの会社報告\n[自動入力]\n\n### 明日の方向性\n[夕セッションで確定]\n`;

  const oauthClient = await getOAuthClient();
  const driveUser = google.drive({ version: 'v3', auth: oauthClient });
  const { Readable } = require('stream');
  const response = await driveUser.files.create({
    requestBody: { name: filename, mimeType: 'text/plain', parents: [DAILY_REPORT_FOLDER] },
    media: { mimeType: 'text/plain', body: Readable.from([content]) },
    fields: 'id, name, webViewLink',
  });
  console.log(`✅ Dashboard作成完了: ${response.data.name}`);
  console.log(`id: ${response.data.id}`);
  console.log(`url: ${response.data.webViewLink}`);
}

// ─── Calendar操作 ─────────────────────────────────────────────────

async function listCalendarEvents(calendarId = MAIN_CAL) {
  const auth = await getAuth();
  const calendar = google.calendar({ version: 'v3', auth });
  const now = new Date();
  const oneWeekLater = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
  const response = await calendar.events.list({
    calendarId, timeMin: now.toISOString(), timeMax: oneWeekLater.toISOString(),
    singleEvents: true, orderBy: 'startTime', maxResults: 30,
  });
  const events = response.data.items || [];
  if (events.length === 0) { console.log('予定はありません'); return; }
  events.forEach(e => {
    const start = e.start.dateTime || e.start.date;
    console.log(`[${start}] ${e.summary} | id: ${e.id}`);
  });
}

async function listEventsRange(calendarId, dateFrom, dateTo) {
  const auth = await getAuth();
  const calendar = google.calendar({ version: 'v3', auth });
  const response = await calendar.events.list({
    calendarId,
    timeMin: new Date(dateFrom + 'T00:00:00+09:00').toISOString(),
    timeMax: new Date(dateTo + 'T23:59:59+09:00').toISOString(),
    singleEvents: true, orderBy: 'startTime', maxResults: 50,
  });
  const events = response.data.items || [];
  if (events.length === 0) { console.log('予定はありません'); return; }
  events.forEach(e => {
    const start = e.start.dateTime || e.start.date;
    console.log(`[${start}] ${e.summary} | id: ${e.id}`);
  });
}

async function getEvent(calendarId, eventId) {
  const auth = await getAuth();
  const calendar = google.calendar({ version: 'v3', auth });
  const event = await calendar.events.get({ calendarId, eventId });
  console.log(JSON.stringify(event.data, null, 2));
}

async function addEvent(calendarId, title, date, time) {
  const auth = await getAuth();
  const calendar = google.calendar({ version: 'v3', auth });
  let start, end;
  if (time) {
    const h = parseInt(time.split(':')[0]);
    const min = time.split(':')[1] || '00';
    const endH = String((h + 1) % 24).padStart(2, '0');
    start = { dateTime: `${date}T${String(h).padStart(2,'0')}:${min}:00+09:00`, timeZone: 'Asia/Tokyo' };
    end = { dateTime: `${date}T${endH}:${min}:00+09:00`, timeZone: 'Asia/Tokyo' };
  } else {
    const next = new Date(date + 'T00:00:00+09:00');
    next.setDate(next.getDate() + 1);
    start = { date };
    end = { date: next.toISOString().substring(0, 10) };
  }
  const response = await calendar.events.insert({ calendarId, requestBody: { summary: title, start, end } });
  console.log(`✅ 予定追加: ${title} (${date}${time ? ' ' + time : ''}) | id: ${response.data.id}`);
  return response.data;
}

async function addTask(title, date) { return addEvent(TASK_CAL, title, date, null); }

async function completeTask(eventId, calendarId) {
  const cal = calendarId || TASK_CAL;
  const auth = await getAuth();
  const calendar = google.calendar({ version: 'v3', auth });
  const event = await calendar.events.get({ calendarId: cal, eventId });
  const currentTitle = event.data.summary || '';
  const newTitle = currentTitle.startsWith('[完了]') ? currentTitle : `[完了] ${currentTitle}`;
  await calendar.events.patch({ calendarId: cal, eventId, requestBody: { summary: newTitle, colorId: '8' } });
  console.log(`✅ 完了: ${currentTitle} → ${newTitle}`);
}

async function updateEvent(calendarId, eventId, field, value) {
  const auth = await getAuth();
  const calendar = google.calendar({ version: 'v3', auth });
  const event = await calendar.events.get({ calendarId, eventId });
  const current = event.data;
  let patch = {};
  if (field === 'title' || field === 'summary') {
    patch.summary = value;
  } else if (field === 'date') {
    if (current.start.dateTime) {
      const tp = current.start.dateTime.substring(11, 16);
      const ep = current.end.dateTime.substring(11, 16);
      patch.start = { dateTime: `${value}T${tp}:00+09:00`, timeZone: 'Asia/Tokyo' };
      patch.end = { dateTime: `${value}T${ep}:00+09:00`, timeZone: 'Asia/Tokyo' };
    } else {
      const next = new Date(value + 'T00:00:00+09:00');
      next.setDate(next.getDate() + 1);
      patch.start = { date: value };
      patch.end = { date: next.toISOString().substring(0, 10) };
    }
  } else if (field === 'time') {
    const dp = (current.start.dateTime || current.start.date).substring(0, 10);
    const h = parseInt(value.split(':')[0]);
    const min = value.split(':')[1] || '00';
    const endH = String((h + 1) % 24).padStart(2, '0');
    patch.start = { dateTime: `${dp}T${String(h).padStart(2,'0')}:${min}:00+09:00`, timeZone: 'Asia/Tokyo' };
    patch.end = { dateTime: `${dp}T${endH}:${min}:00+09:00`, timeZone: 'Asia/Tokyo' };
  }
  await calendar.events.patch({ calendarId, eventId, requestBody: patch });
  console.log(`✅ 更新: ${field}="${value}" | eventId: ${eventId}`);
}

async function listCalendars() {
  const auth = await getAuth();
  const calendar = google.calendar({ version: 'v3', auth });
  const response = await calendar.calendarList.list();
  const calendars = response.data.items || [];
  calendars.forEach(c => console.log(`${c.summary} | id: ${c.id}`));
}

// ─── メイン処理 ───────────────────────────────────────────────────

const command = process.argv[2];
const arg1 = process.argv[3];
const arg2 = process.argv[4];
const arg3 = process.argv[5];
const arg4 = process.argv[6];

switch (command) {
  case 'auth-setup':    authSetup().catch(console.error); break;
  case 'list':          listFiles(arg1).catch(console.error); break;
  case 'read':          readFile(arg1).catch(console.error); break;
  case 'search':        searchFiles(arg1).catch(console.error); break;
  case 'mkdir':         mkdir(arg1, arg2).catch(console.error); break;
  case 'shared':        listShared().catch(console.error); break;
  case 'write':         writeFile(arg1, arg2).catch(console.error); break;
  case 'create':        createFile(arg1, arg2, arg3).catch(console.error); break;
  case 'today-dashboard':   todayDashboard().catch(console.error); break;
  case 'read-today':        readTodayDashboard().catch(console.error); break;
  case 'write-today':       writeTodayDashboard(arg1).catch(console.error); break;
  case 'create-dashboard':  createDashboard().catch(console.error); break;
  case 'calendars':     listCalendars().catch(console.error); break;
  case 'events':        listCalendarEvents(arg1).catch(console.error); break;
  case 'events-range':  listEventsRange(arg1, arg2, arg3).catch(console.error); break;
  case 'get-event':     getEvent(arg1, arg2).catch(console.error); break;
  case 'add-event':     addEvent(arg1, arg2, arg3, arg4).catch(console.error); break;
  case 'add-task':      addTask(arg1, arg2).catch(console.error); break;
  case 'complete-task': completeTask(arg1, arg2).catch(console.error); break;
  case 'update-event':  updateEvent(arg1, arg2, arg3, arg4).catch(console.error); break;
  default:
    console.log('使い方: node drive.js <command> [args]');
    console.log('GitHub: https://github.com/bestthink01109/northstar-os/blob/main/scripts/drive.js');
}
