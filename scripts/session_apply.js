#!/usr/bin/env node
/**
 * NorthStar OS - セッション反映スクリプト
 * 使い方: node session_apply.js <セッション出力ファイル>
 *
 * Antigravityなどのセッション出力テキストを解析して
 * Google Drive / カレンダー / Signal DB に反映する。
 *
 * 出力テキストを /tmp/session_output.txt などに保存してから実行:
 *   node session_apply.js /tmp/session_output.txt
 */
const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');

const KEY_FILE     = path.join(process.env.HOME, 'Downloads/fifth-sprite-492523-i8-8a32ca4d8877.json');
const OAUTH_FILE   = path.join(process.env.HOME, 'Downloads/client_secret_750072023351-kej7sa596e299guqi9h60jgtf1p6m0vo.apps.googleusercontent.com.json');
const TOKEN_FILE   = path.join(__dirname, 'oauth_tokens.json');
const DAILY_REPORT = '1SGCPerV8CCHT6CcDI8-E6G2JbbmNmsp8';
const SIGNAL_DB_ID = '1iCRjElopMprCT8l-yPvriGWVjWizRXuh';
const MAIN_CAL     = 'bestthink01109@gmail.com';
const TASK_CAL     = 'a0c7e0a0c3b9038b4a54b546d6119480d08d047ac3676811ea6fd1b00da46dc2@group.calendar.google.com';

async function getAuth() {
  return new google.auth.GoogleAuth({ keyFile: KEY_FILE, scopes: ['https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/calendar'] });
}
async function getOAuth() {
  const c = JSON.parse(fs.readFileSync(OAUTH_FILE)).installed;
  const auth = new google.auth.OAuth2(c.client_id, c.client_secret, c.redirect_uris[0]);
  auth.setCredentials(JSON.parse(fs.readFileSync(TOKEN_FILE)));
  auth.on('tokens', t => {
    const cur = JSON.parse(fs.readFileSync(TOKEN_FILE));
    fs.writeFileSync(TOKEN_FILE, JSON.stringify({...cur,...t}, null, 2));
  });
  return auth;
}
function getTodayJST() {
  const j = new Date(Date.now() + 9*60*60*1000);
  const y = j.getUTCFullYear(), m = String(j.getUTCMonth()+1).padStart(2,'0'), d = String(j.getUTCDate()).padStart(2,'0');
  return { date:`${y}-${m}-${d}`, compact:`${y}${m}${d}` };
}

function parseOutput(text) {
  const start = text.indexOf('===SESSION_OUTPUT_START===');
  const end   = text.indexOf('===SESSION_OUTPUT_END===');
  if (start === -1 || end === -1) {
    console.log('⚠️  SESSION_OUTPUT ブロックが見つかりません。全テキストをダッシュボード更新として扱います。');
    return { dashboard: text, calendarOps: [], signals: [] };
  }
  const block = text.substring(start + '===SESSION_OUTPUT_START==='.length, end).trim();

  let dashboard = null;
  const dashMatch = block.match(/DASHBOARD_UPDATE:\n([\s\S]*?)\nEND_DASHBOARD/);
  if (dashMatch) dashboard = dashMatch[1].trim();

  const calendarOps = [];
  block.split('\n').forEach(line => {
    const l = line.trim();
    if (l.startsWith('CALENDAR_ADD_TASK:')) {
      const parts = l.replace('CALENDAR_ADD_TASK:','').trim().split('|').map(s=>s.trim());
      calendarOps.push({ op:'add_task', title:parts[0], date:parts[1] });
    } else if (l.startsWith('CALENDAR_ADD_EVENT:')) {
      const parts = l.replace('CALENDAR_ADD_EVENT:','').trim().split('|').map(s=>s.trim());
      const calId = parts[3] && parts[3].includes('@') ? parts[3] : MAIN_CAL;
      calendarOps.push({ op:'add_event', title:parts[0], date:parts[1], time:parts[2], calId });
    } else if (l.startsWith('CALENDAR_COMPLETE:')) {
      calendarOps.push({ op:'complete', eventId:l.replace('CALENDAR_COMPLETE:','').trim() });
    } else if (l.startsWith('CALENDAR_UPDATE:')) {
      const parts = l.replace('CALENDAR_UPDATE:','').trim().split('|').map(s=>s.trim());
      calendarOps.push({ op:'update', eventId:parts[0], calId:parts[1], field:parts[2], value:parts[3] });
    }
  });

  const signals = [];
  block.split('\n').forEach(line => {
    const l = line.trim();
    if (l.startsWith('SIGNAL_DB:')) {
      const parts = l.replace('SIGNAL_DB:','').trim().split('|').map(s=>s.trim());
      signals.push({ rank:parts[0]||'B', text:parts[1]||'', source:parts[2]||'DASHBOARD_SESSION' });
    }
  });

  return { dashboard, calendarOps, signals };
}

async function applyDashboard(dashboard) {
  const today = getTodayJST();
  const auth = await getOAuth();
  const drive = google.drive({ version:'v3', auth });
  const found = await drive.files.list({
    q: `name='Dashboard_${today.compact}.md' and '${DAILY_REPORT}' in parents and trashed=false`,
    fields: 'files(id,name)',
  });
  const { Readable } = require('stream');
  if (found.data.files.length > 0) {
    await drive.files.update({ fileId:found.data.files[0].id, media:{mimeType:'text/plain', body:Readable.from([dashboard])} });
    console.log(`✅ Dashboard更新: Dashboard_${today.compact}.md`);
  } else {
    const res = await drive.files.create({
      requestBody: { name:`Dashboard_${today.compact}.md`, mimeType:'text/plain', parents:[DAILY_REPORT] },
      media: { mimeType:'text/plain', body:Readable.from([dashboard]) }, fields:'id,name',
    });
    console.log(`✅ Dashboard作成: ${res.data.name}`);
  }
}

async function applyCalendarOps(ops) {
  if (ops.length === 0) return;
  const auth = await getAuth();
  const calendar = google.calendar({ version:'v3', auth });
  for (const op of ops) {
    try {
      if (op.op === 'add_task') {
        const next = new Date(op.date+'T00:00:00+09:00'); next.setDate(next.getDate()+1);
        const res = await calendar.events.insert({ calendarId:TASK_CAL, requestBody:{
          summary:op.title, start:{date:op.date}, end:{date:next.toISOString().substring(0,10)} }});
        console.log(`✅ タスク追加: ${op.title} (${op.date}) | id: ${res.data.id}`);
      } else if (op.op === 'add_event') {
        const h = parseInt(op.time.split(':')[0]), min = op.time.split(':')[1]||'00';
        const endH = String((h+1)%24).padStart(2,'0');
        const res = await calendar.events.insert({ calendarId:op.calId||MAIN_CAL, requestBody:{
          summary:op.title,
          start:{dateTime:`${op.date}T${String(h).padStart(2,'0')}:${min}:00+09:00`,timeZone:'Asia/Tokyo'},
          end:  {dateTime:`${op.date}T${endH}:${min}:00+09:00`,timeZone:'Asia/Tokyo'} }});
        console.log(`✅ 予定追加: ${op.title} (${op.date} ${op.time}) | id: ${res.data.id}`);
      } else if (op.op === 'complete') {
        const ev = await calendar.events.get({ calendarId:TASK_CAL, eventId:op.eventId });
        const cur = ev.data.summary||'';
        const newTitle = cur.startsWith('[完了]') ? cur : `[完了] ${cur}`;
        await calendar.events.patch({ calendarId:TASK_CAL, eventId:op.eventId, requestBody:{summary:newTitle, colorId:'8'} });
        console.log(`✅ タスク完了: ${cur} → ${newTitle}`);
      } else if (op.op === 'update') {
        let patch = {};
        if (op.field==='title'||op.field==='summary') {
          patch.summary = op.value;
        } else if (op.field==='date') {
          const ev = await calendar.events.get({ calendarId:op.calId, eventId:op.eventId });
          if (ev.data.start.dateTime) {
            const tp = ev.data.start.dateTime.substring(11,16), ep = ev.data.end.dateTime.substring(11,16);
            patch.start = {dateTime:`${op.value}T${tp}:00+09:00`,timeZone:'Asia/Tokyo'};
            patch.end   = {dateTime:`${op.value}T${ep}:00+09:00`,timeZone:'Asia/Tokyo'};
          } else {
            const nx = new Date(op.value+'T00:00:00+09:00'); nx.setDate(nx.getDate()+1);
            patch.start = {date:op.value}; patch.end = {date:nx.toISOString().substring(0,10)};
          }
        } else if (op.field==='time') {
          const ev = await calendar.events.get({ calendarId:op.calId, eventId:op.eventId });
          const dp = (ev.data.start.dateTime||ev.data.start.date).substring(0,10);
          const h2 = parseInt(op.value.split(':')[0]), m2 = op.value.split(':')[1]||'00';
          const eh = String((h2+1)%24).padStart(2,'0');
          patch.start = {dateTime:`${dp}T${String(h2).padStart(2,'0')}:${m2}:00+09:00`,timeZone:'Asia/Tokyo'};
          patch.end   = {dateTime:`${dp}T${eh}:${m2}:00+09:00`,timeZone:'Asia/Tokyo'};
        }
        await calendar.events.patch({ calendarId:op.calId, eventId:op.eventId, requestBody:patch });
        console.log(`✅ 予定更新: ${op.field}="${op.value}" | ${op.eventId}`);
      }
    } catch(e) { console.error(`❌ カレンダー操作失敗 (${op.op}): ${e.message}`); }
  }
}

async function applySignals(signals) {
  if (signals.length === 0) return;
  const auth = await getOAuth();
  const drive = google.drive({ version:'v3', auth });
  let current = '';
  try {
    const res = await drive.files.get({ fileId:SIGNAL_DB_ID, alt:'media' }, { responseType:'text' });
    current = res.data;
  } catch(e) { console.warn('Signal DB読み込みエラー:', e.message); }
  const nowJST = new Date(Date.now()+9*60*60*1000).toISOString().replace('T',' ').substring(0,16);
  function esc(s) {
    if (!s) return '';
    s = String(s);
    return (s.includes(',')||s.includes('"')||s.includes('\n')) ? `"${s.replace(/"/g,'""')}"` : s;
  }
  const newRows = signals.map(s=>[nowJST,s.source||'DASHBOARD_SESSION',s.rank,s.text,'未対応',''].map(esc).join(',')).join('\n');
  const updated = (current.endsWith('\n') ? current : current+'\n') + newRows + '\n';
  const { Readable } = require('stream');
  await drive.files.update({ fileId:SIGNAL_DB_ID, media:{mimeType:'text/plain', body:Readable.from([updated])} });
  console.log(`✅ Signal DB更新: ${signals.length}件追加`);
  signals.forEach(s => console.log(`  [${s.rank}] ${s.text}`));
}

async function main() {
  const inputFile = process.argv[2];
  if (!inputFile) {
    console.error('使い方: node session_apply.js <セッション出力ファイル>');
    console.error('例:     node session_apply.js /tmp/session_output.txt');
    process.exit(1);
  }
  if (!fs.existsSync(inputFile)) {
    console.error(`ファイルが見つかりません: ${inputFile}`);
    process.exit(1);
  }
  const text = fs.readFileSync(inputFile, 'utf8');
  const { dashboard, calendarOps, signals } = parseOutput(text);

  console.log('=== セッション反映開始 ===');
  console.log(`ダッシュボード更新: ${dashboard ? 'あり' : 'なし'}`);
  console.log(`カレンダー操作: ${calendarOps.length}件`);
  console.log(`Signal DB: ${signals.length}件`);
  console.log('');

  if (dashboard) await applyDashboard(dashboard);
  await applyCalendarOps(calendarOps);
  await applySignals(signals);

  console.log('');
  console.log('=== 反映完了 ===');
}

main().catch(e => { console.error('エラー:', e.message); process.exit(1); });
