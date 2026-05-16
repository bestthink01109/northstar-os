// ==========================================
// 福岡プラント 勤怠管理システム GASコア
// 【一括入力マスター直接書き込み版】
// doPost → キュー → 毎分トリガーで解析 → 一括入力マスターに書き込み
// ==========================================

const MASTER_SS_ID = '1z8dGrmxz1igWwzjKGlcqaIutlMLcPOBiicbN69xi_DE'; // 新MASTER（Excelベース変換版）
const QUEUE_SHEET_NAME = '処理キュー';
const MONTHLY_FOLDER_ID = '1RnCoqFwCiPG2aF3G88EGrrSxTUKT1Rry';

function getGeminiApiKey() {
  const key = PropertiesService.getScriptProperties().getProperty('GEMINI_API_KEY');
  if (!key) throw new Error('スクリプトプロパティに GEMINI_API_KEY が設定されていません。');
  return key;
}

/**
 * 0. メニュー作成
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('★福岡プラント連携')
    .addItem('診断開始（AI解析テスト）', '診断開始')
    .addItem('キューを今すぐ処理', 'processQueue')
    .addItem('社員名簿を更新', 'syncStaffList')
    .addItem('出勤簿を整形する', 'applyFormatToCurrentFile')
    .addItem('全員分PDFを出力', 'exportAllSheetsToPDF')
    .addToUi();
}

/**
 * 1. LINE検証用（GETに200を返す）
 */
function doGet(e) {
  return ContentService.createTextOutput("ok");
}

/**
 * 2. LINE受信処理 (doPost) — キューに積むだけ・超軽量
 */
function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return ContentService.createTextOutput("ok");
    }
    const contents = JSON.parse(e.postData.contents);
    const events = contents.events || [];
    if (events.length === 0) return ContentService.createTextOutput("ok");

    const ss = SpreadsheetApp.openById(MASTER_SS_ID);
    let queueSheet = ss.getSheetByName(QUEUE_SHEET_NAME);
    if (!queueSheet) {
      queueSheet = ss.insertSheet(QUEUE_SHEET_NAME);
      queueSheet.getRange(1, 1, 1, 3).setValues([['受信日時(JST)', 'メッセージ', '状態']]);
    }
    events.forEach(event => {
      if (event.type !== 'message' || event.message.type !== 'text') return;
      const ts = Utilities.formatDate(new Date(), "Asia/Tokyo", "yyyy-MM-dd HH:mm:ss");
      const userId = (event.source && event.source.userId) ? event.source.userId : 'no_id';
      // sourceの全情報をデバッグ用に記録
      const sourceInfo = event.source ? JSON.stringify(event.source) : 'no_source';
      queueSheet.appendRow([ts, event.message.text, '未処理', userId, sourceInfo]);
    });
  } catch (err) {
    Logger.log("doPost エラー: " + err.message);
  }
  return ContentService.createTextOutput("ok");
}

/**
 * 3. キュー処理（毎分トリガーで自動実行）
 */
function processQueue() {
  const ss = SpreadsheetApp.openById(MASTER_SS_ID);
  const queueSheet = ss.getSheetByName(QUEUE_SHEET_NAME);
  if (!queueSheet || queueSheet.getLastRow() < 2) return;

  const staffList = getStaffList(ss);
  const data = queueSheet.getDataRange().getValues();

  for (let i = 1; i < data.length; i++) {
    if (data[i][2] !== '未処理') continue;

    const userMessage = String(data[i][1]);
    queueSheet.getRange(i + 1, 3).setValue('処理中');

    try {
      const aiResult = parseAttendanceWithGemini(userMessage, staffList);
      if (aiResult && aiResult.length > 0) {
        // 月別SSを確保し、一括入力マスターと実績ログの両方に書き込む
        const monthlySS = ensureMonthlySSExists(aiResult);
        writeToMasterSheet(monthlySS, aiResult, staffList);
        writeToResultLog(monthlySS, aiResult, userMessage);
        queueSheet.getRange(i + 1, 3).setValue('完了');
      } else {
        queueSheet.getRange(i + 1, 3).setValue('スキップ（勤怠情報なし）');
        notifySkipToLine(userMessage, 'Geminiが勤怠情報を検出できませんでした');
      }
    } catch (err) {
      queueSheet.getRange(i + 1, 3).setValue('エラー: ' + err.message);
      Logger.log("processQueue エラー [行" + (i+1) + "]: " + err.message);
    }
  }
}

/**
 * 4. 毎分トリガー設定（初回1回だけ実行）
 */
function setupTrigger() {
  ScriptApp.getProjectTriggers().forEach(trigger => {
    if (trigger.getHandlerFunction() === 'processQueue') ScriptApp.deleteTrigger(trigger);
  });
  ScriptApp.newTrigger('processQueue').timeBased().everyMinutes(1).create();
  Logger.log('毎分トリガーを設定しました。');
}

/**
 * 5. 一括入力マスターへの書き込み（核心処理）
 *
 * シート構造:
 *   Row1: タイトル
 *   Row2: A=氏名, B=項目, C=1日, D=2日...
 *   Row3: B=出勤状態
 *   Row4: A=土本 凱斗, B=現場名   ← 氏名はこの行(現場名行)のA列
 *   Row5: B=残業
 *   Row6: B=弁当
 *   Row7: B=出勤状態（次の社員）
 *   ...
 */
function writeToMasterSheet(ss, aiResult, staffList) {
  // Excelから変換したSSではシート名が「実績」、旧MASTERでは「一括入力マスター」
  const inputSheet = ss.getSheetByName('実績') || ss.getSheetByName('一括入力マスター');
  if (!inputSheet) {
    Logger.log('実績/一括入力マスターシートが見つかりません。シート一覧: ' + ss.getSheets().map(s => s.getName()).join(', '));
    return;
  }
  Logger.log('書込先シート: ' + inputSheet.getName());

  // 現場マスタ（ゆらぎ辞書 + 種別）を読み込む
  const siteData = getSiteMasterData(ss);
  Logger.log('現場マスタ: マッピング' + Object.keys(siteData.mappings).length + '件, 種別' + Object.keys(siteData.types).length + '件');

  const data = inputSheet.getDataRange().getValues();

  aiResult.forEach(entry => {
    // 現場名をゆらぎ辞書で正規化
    if (entry.場所 && siteData.mappings[entry.場所.trim()]) {
      Logger.log('現場名正規化: ' + entry.場所 + ' → ' + siteData.mappings[entry.場所.trim()]);
      entry.場所 = siteData.mappings[entry.場所.trim()];
    }
    // 氏名の解決（苗字→フルネーム）
    const matchedStaff = staffList.find(s => entry.氏名 === s.lastName || entry.氏名 === s.fullName);
    const fullName = matchedStaff ? matchedStaff.fullName : entry.氏名;

    // 日付から「日」を取得
    const dateStr = entry.日付;
    if (!dateStr || !/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
      Logger.log('日付フォーマット不正: ' + dateStr);
      return;
    }
    const day = parseInt(dateStr.split('-')[2]); // 1〜31
    const colNum = day + 2; // C列(3)=1日, D列(4)=2日 ... → day + 2

    // A列からフルネームを検索（「現場名」行にA列の氏名が記載）
    let nameRow = -1;
    for (let r = 2; r < data.length; r++) {
      const cellVal = String(data[r][0] || '').trim();
      if (cellVal === fullName) {
        nameRow = r + 1; // 1-based行番号
        break;
      }
    }

    if (nameRow === -1) {
      Logger.log('一括入力マスターで氏名が見つかりません: ' + fullName);
      return;
    }

    // nameRow = 出勤状態の行（氏名はA列の出勤状態行に記載）
    // nameRow   = 出勤状態
    // nameRow+1 = 現場名
    // nameRow+2 = 残業
    // nameRow+3 = 弁当
    inputSheet.getRange(nameRow,     colNum).setValue(entry.状態 || '出勤');
    inputSheet.getRange(nameRow + 1, colNum).setValue(entry.場所 || '');
    inputSheet.getRange(nameRow + 2, colNum).setValue(entry.残業 !== undefined ? entry.残業 : '');
    inputSheet.getRange(nameRow + 3, colNum).setValue(entry.弁当 || '');

    // 個人シートのAA列（現場区分: 工場/現場/出張）に種別を書き込む
    // GeminiがAA="出張"を返した場合はそれを優先、なければマスタから種別を取得
    const siteType = (entry.AA && entry.AA.trim())
      ? entry.AA.trim()
      : (entry.場所 ? siteData.types[entry.場所] || '' : '');
    // 未知の現場名はマスタに自動追加
    if (entry.場所 && !siteData.types[entry.場所]) {
      addSiteToMaster(ss, entry.場所, entry.場所);
    }
    const personalSheet = ss.getSheetByName(fullName);
    if (personalSheet && siteType) {
      personalSheet.getRange(day + 3, 27).setValue(siteType); // AA列=27、row=day+3
      Logger.log('AA列書込: ' + fullName + ' ' + dateStr + ' → ' + siteType);
    }

    Logger.log('[書込完了] ' + fullName + ' ' + dateStr + ' → 行' + nameRow + ' 列' + colNum);
  });
}

/**
 * 6. 月別スプレッドシートの確保（MASTERをコピー）
 * スクリプトプロパティ不要。フォルダを検索して自動で判断。
 * 戻り値：月別SSのSpreadsheetオブジェクト
 */
function ensureMonthlySSExists(aiResult) {
  if (!aiResult || aiResult.length === 0 || !aiResult[0].日付) {
    throw new Error('日付が取得できません');
  }

  const firstDate = aiResult[0].日付;
  const yearMonth = firstDate.substring(0, 7).replace('-', ''); // YYYYMM
  const fileName = yearMonth + '_福岡プラント出勤簿';
  const folder = DriveApp.getFolderById(MONTHLY_FOLDER_ID);

  // フォルダ内で同名ファイルを検索（手動操作ゼロ）
  const files = folder.getFilesByName(fileName);
  if (files.hasNext()) {
    const file = files.next();
    const existingSS = SpreadsheetApp.openById(file.getId());
    // 設定C2を当月1日に更新（念のため毎回）
    updateSettingDate(existingSS, firstDate);
    Logger.log('既存の月別SS使用: ' + fileName);
    return existingSS;
  }

  // 存在しない場合はMASTERをコピーして新規作成
  const masterFile = DriveApp.getFileById(MASTER_SS_ID);
  const newFile = masterFile.makeCopy(fileName, folder);

  // 不要シートを削除（実績ログ・個人シート・設定・集計は残す）
  const newSS = SpreadsheetApp.openById(newFile.getId());
  const deleteSheets = ['処理キュー', 'ログ確認', '診断ログ', '2026.05', '2026.04'];
  newSS.getSheets().forEach(sheet => {
    if (deleteSheets.includes(sheet.getName())) {
      if (newSS.getSheets().length > 1) newSS.deleteSheet(sheet);
    }
  });

  // 実績シートのデータ部分（C3以降）をクリア（古いデータの混入防止）
  const inputSheet = newSS.getSheetByName('実績') || newSS.getSheetByName('一括入力マスター');
  if (inputSheet) {
    const lastRow = inputSheet.getLastRow();
    const lastCol = inputSheet.getLastColumn();
    if (lastRow >= 3 && lastCol >= 3) {
      inputSheet.getRange(3, 3, lastRow - 2, lastCol - 2).clearContent();
    }
  }

  // 実績ログのデータ部分をクリア（ヘッダー行はそのまま）
  const logSheet = newSS.getSheetByName('実績ログ');
  if (logSheet && logSheet.getLastRow() > 1) {
    logSheet.getRange(2, 1, logSheet.getLastRow() - 1, logSheet.getLastColumn()).clearContent();
  }

  // 設定C2を当月1日に更新
  updateSettingDate(newSS, firstDate);

  // 集計シートのC列（Row3以降）に社員マスターから社員名を自動入力
  const masterSS = SpreadsheetApp.openById(MASTER_SS_ID);
  const staffList = getStaffList(masterSS);
  const summarySheet = newSS.getSheetByName('集計');
  if (summarySheet && staffList.length > 0) {
    staffList.forEach((staff, index) => {
      summarySheet.getRange(index + 3, 3).setValue(staff.fullName);
    });
    Logger.log('集計シートC列に社員名を入力しました（' + staffList.length + '名）');
  }

  formatAttendanceSheets(newSS);
  applyRow2Names(newSS);
  Logger.log('月別SSを新規作成しました: ' + fileName);
  return newSS;
}

/**
 * 7. 設定シートのC2（基準年月）を当月1日に更新
 * ExcelからのSS変換後もシート名「設定」は共通
 */
function updateSettingDate(ss, dateStr) {
  const settingSheet = ss.getSheetByName('設定');
  if (!settingSheet) {
    Logger.log('設定シートが見つかりません');
    return;
  }
  const parts = dateStr.split('-');
  const targetDate = new Date(Number(parts[0]), Number(parts[1]) - 1, 1);
  settingSheet.getRange('C2').setValue(targetDate);
  Logger.log('設定!C2 → ' + parts[0] + '/' + parts[1] + '/1 に更新');
}

/**
 * 8. 実績ログへの書き込み（確認用）
 */
function writeToResultLog(ss, aiResult, userMessage) {
  let logSheet = ss.getSheetByName('実績ログ');
  if (!logSheet) {
    logSheet = ss.insertSheet('実績ログ');
    logSheet.getRange(1, 1, 1, 8).setValues([["氏名", "日付", "状態", "場所", "残業", "弁当", "タイムスタンプ", "元のメッセージ"]]);
    logSheet.getRange('A1:H1').setFontWeight('bold').setBackground('#444444').setFontColor('#ffffff');
    logSheet.setFrozenRows(1);
  }
  const ts = Utilities.formatDate(new Date(), "Asia/Tokyo", "yyyy-MM-dd HH:mm:ss");
  aiResult.forEach(entry => {
    logSheet.appendRow([
      entry.氏名, entry.日付, entry.状態, entry.場所,
      entry.残業, entry.弁当, ts, userMessage
    ]);
  });
}

/**
 * 8. Gemini APIによるAI解析
 */
function parseAttendanceWithGemini(messageText, staffList) {
  const staffNames = staffList.map(s => s.lastName).join('、');
  const today = Utilities.formatDate(new Date(), "Asia/Tokyo", "yyyy-MM-dd");

  const prompt = 'あなたは建設会社の超優秀な事務員です。以下の【掟】を遵守し、LINEメッセージから勤怠情報をJSONで抽出せよ。\n\n'
    + '【掟】\n'
    + '1. 社員リストにある苗字が「本文に明記」されている場合のみ抽出せよ。存在しない名前は無視せよ。\n'
    + '2. 日付は YYYY-MM-DD 形式。年がなければ 2026年 とする。\n'
    + '3. 状態は「出勤」「休日」「休出」「振出」「振休」「有給」「欠勤」「特別」のいずれか。場所や「定時」があれば「出勤」、出張も「出勤」とせよ（AA列で区別）。「休み」「公休」は「休日」、休日出勤は「休出」とせよ。\n'
    + '4. 場所は「新興プラント」「AGC工場」など地名・社名を正確に抽出せよ。出張の場合は行先地名（例：名古屋）を場所に入れよ。\n'
    + '5. 残業は数値のみ（2.5など）。「なし」「定時」や未記載は 0 とせよ。\n'
    + '6. 弁当は「弁当」「べんとう」があれば "〇"、なければ "" とせよ。\n'
    + '7. 勤怠に無関係な挨拶・雑談は完全無視し、[] を返せ。\n'
    + '8. 「全員弁当」等は、そのメッセージの全員に適用せよ。\n'
    + '9. AA区分は「工場」「現場」「出張」のいずれか。メッセージに「出張」が含まれる場合は「出張」、それ以外は場所がある場合でも "" とせよ（GAS側でマスタ参照して自動設定）。\n\n'
    + '【社員リスト】\n' + staffNames + '\n\n'
    + '【見本1】5月7日 新興プラント 土本 中嶋 残業2\n回答：[{"氏名":"土本","日付":"2026-05-07","状態":"出勤","場所":"新興プラント","残業":2,"弁当":"","AA":""},{"氏名":"中嶋","日付":"2026-05-07","状態":"出勤","場所":"新興プラント","残業":2,"弁当":"","AA":""}]\n\n'
    + '【見本2】5月9日 AGC工場 土本 國松（部外者） 残業なし\n回答：[{"氏名":"土本","日付":"2026-05-09","状態":"出勤","場所":"AGC工場","残業":0,"弁当":"","AA":""}]\n\n'
    + '【見本3】5月10日 名古屋出張 石村 弁当\n回答：[{"氏名":"石村","日付":"2026-05-10","状態":"出勤","場所":"名古屋","残業":0,"弁当":"〇","AA":"出張"}]\n\n'
    + '【見本4】お疲れ様です。テストです。\n回答：[]\n\n'
    + '【見本5】5/9と10 新興プラント 土本 残業各2\n回答：[{"氏名":"土本","日付":"2026-05-09","状態":"出勤","場所":"新興プラント","残業":2,"弁当":"","AA":""},{"氏名":"土本","日付":"2026-05-10","状態":"出勤","場所":"新興プラント","残業":2,"弁当":"","AA":""}]\n\n'
    + '【見本6】5/11 土本 出勤 残業1\n回答：[{"氏名":"土本","日付":"2026-05-11","状態":"出勤","場所":"","残業":1,"弁当":"","AA":""}]\n\n'
    + '【見本7】5/11(月) 現場：AGC 名前：土本 残業：3\n回答：[{"氏名":"土本","日付":"2026-05-11","状態":"出勤","場所":"AGC","残業":3,"弁当":"","AA":""}]\n\n'
    + '【見本8】5/12 AGC 土本 石村 全員弁当 全員残業2\n回答：[{"氏名":"土本","日付":"2026-05-12","状態":"出勤","場所":"AGC","残業":2,"弁当":"〇","AA":""},{"氏名":"石村","日付":"2026-05-12","状態":"出勤","場所":"AGC","残業":2,"弁当":"〇","AA":""}]\n\n'
    + '【対象メッセージ】\n今日：' + today + '\n入力：' + messageText;

  const payload = {
    contents: [{ parts: [{ text: prompt }] }],
    safetySettings: [
      { category: "HARM_CATEGORY_HARASSMENT", threshold: "BLOCK_NONE" },
      { category: "HARM_CATEGORY_HATE_SPEECH", threshold: "BLOCK_NONE" },
      { category: "HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold: "BLOCK_NONE" },
      { category: "HARM_CATEGORY_DANGEROUS_CONTENT", threshold: "BLOCK_NONE" }
    ]
  };

  const geminiApiKey = getGeminiApiKey();
  const geminiModelUrl = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key=' + geminiApiKey;

  const response = UrlFetchApp.fetch(geminiModelUrl, {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  const resCode = response.getResponseCode();
  if (resCode !== 200) throw new Error("Gemini APIエラー (Code: " + resCode + ")");

  const resJson = JSON.parse(response.getContentText());
  if (!resJson.candidates || !resJson.candidates[0].content) return [];

  let resultText = resJson.candidates[0].content.parts[0].text;
  resultText = resultText.replace(/```json|```/g, '').trim();
  const parsed = JSON.parse(resultText);
  return Array.isArray(parsed) ? parsed : [parsed];
}

/**
 * 8. 社員マスター取得
 */
function getStaffList(ss) {
  // Excelから変換したSSでは「社員マスタ」（ーなし）
  const masterSheet = ss.getSheetByName('社員マスター') || ss.getSheetByName('社員マスタ');
  if (!masterSheet) {
    Logger.log('社員マスターシートが見つかりません。シート一覧: ' + ss.getSheets().map(s => s.getName()).join(', '));
    return [];
  }
  const data = masterSheet.getDataRange().getValues();
  const list = [];
  for (let i = 1; i < data.length; i++) {
    let lastName = String(data[i][0] || '').trim();
    let fullName = String(data[i][1] || '').trim();

    // A列が空でB列に値がある場合（Excelから変換したSS：A列空,B列=苗字,C列=フルネーム）
    if (!lastName && fullName) {
      lastName = fullName;
      fullName = String(data[i][2] || '').trim();
    }

    if (lastName) list.push({ lastName, fullName: fullName || lastName });
  }
  Logger.log('社員リスト取得: ' + list.map(s => s.lastName + '/' + s.fullName).join(', '));
  return list;
}

/**
 * 9. 診断開始（手動テスト）
 */
function 診断開始() {
  const ss = SpreadsheetApp.openById(MASTER_SS_ID);
  Logger.log("シート一覧: " + ss.getSheets().map(s => s.getName()).join(', '));

  const staffList = getStaffList(ss);
  Logger.log("社員リスト: " + JSON.stringify(staffList));

  const testMsg = "5月14日 AGC 新興プラント\n坂井 土本\n残業2時間";
  Logger.log("テストメッセージ: " + testMsg);

  const aiResult = parseAttendanceWithGemini(testMsg, staffList);
  Logger.log("AI解析結果: " + JSON.stringify(aiResult, null, 2));

  if (aiResult && aiResult.length > 0) {
    const monthlySS = ensureMonthlySSExists(aiResult);
    writeToMasterSheet(monthlySS, aiResult, staffList);
    Logger.log("書込完了。月別SS「" + monthlySS.getName() + "」の「一括入力マスター」シートを確認してください。");
  } else {
    Logger.log("失敗：解析できませんでした。");
  }
}

/**
 * 10. 社員名簿の更新確認
 */
function syncStaffList() {
  const ss = SpreadsheetApp.openById(MASTER_SS_ID);
  const staffList = getStaffList(ss);
  let diagSheet = ss.getSheetByName('診断ログ');
  if (!diagSheet) diagSheet = ss.insertSheet('診断ログ');
  const ts = Utilities.formatDate(new Date(), "Asia/Tokyo", "yyyy-MM-dd HH:mm:ss");
  if (staffList.length > 0) {
    const msg = '【OK】社員名簿（' + staffList.length + '名）読込完了';
    diagSheet.appendRow([ts, msg, staffList.map(s => s.fullName).join('、')]);
    Logger.log(msg);
  } else {
    const msg = '【警告】社員マスターから名簿を取得できませんでした';
    diagSheet.appendRow([ts, msg, '']);
    Logger.log(msg);
  }
}

/**
 * 新マスターSSの診断・修正
 */
/**
 * 202605 SSの内容を診断してDriveにテキストで書き出す
 */
function exportDiag() {
  const folder = DriveApp.getFolderById(MONTHLY_FOLDER_ID);
  const files = folder.getFilesByName('202605_福岡プラント出勤簿');
  if (!files.hasNext()) { Logger.log('202605 SSが見つかりません'); return; }

  const ss = SpreadsheetApp.openById(files.next().getId());
  const lines = [];

  lines.push('=== シート一覧 ===');
  ss.getSheets().forEach(s => lines.push('  ' + s.getName()));

  const settingSheet = ss.getSheetByName('設定');
  lines.push('\n=== 設定!C2（基準年月） ===');
  lines.push(settingSheet ? String(settingSheet.getRange('C2').getValue()) : '設定シートなし');

  const staffSheet = ss.getSheetByName('社員マスター') || ss.getSheetByName('社員マスタ');
  lines.push('\n=== 社員マスタ（A1:C8） ===');
  if (staffSheet) {
    staffSheet.getRange('A1:C8').getValues().forEach(r => { if(r[0]||r[1]) lines.push(r.join('\t')); });
  } else {
    lines.push('社員マスタシートなし');
  }

  const jissekiSheet = ss.getSheetByName('実績') || ss.getSheetByName('一括入力マスター');
  lines.push('\n=== 実績シート名 ===');
  lines.push(jissekiSheet ? jissekiSheet.getName() : 'シートなし');
  if (jissekiSheet) {
    lines.push('\n=== 実績A1:B35（氏名・項目）===');
    jissekiSheet.getRange('A1:B35').getValues().forEach((r, i) => {
      if (r[0] || r[1]) lines.push((i+1) + ': ' + r.join('\t'));
    });
    lines.push('\n=== 実績P列（14日分）===');
    jissekiSheet.getRange('P1:P35').getValues().forEach((r, i) => {
      if (r[0]) lines.push('P' + (i+1) + ': ' + r[0]);
    });
  }

  const logSheet = ss.getSheetByName('実績ログ');
  lines.push('\n=== 実績ログ（先頭10行）===');
  if (logSheet && logSheet.getLastRow() > 1) {
    logSheet.getRange(1, 1, Math.min(10, logSheet.getLastRow()), 8).getValues()
      .forEach(r => lines.push(r.join('\t')));
  } else {
    lines.push('実績ログなし or 空');
  }

  const result = lines.join('\n');
  Logger.log(result);
  const ts = Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyyMMdd_HHmmss');
  const diagFile = DriveApp.getFolderById('1SGCPerV8CCHT6CcDI8-E6G2JbbmNmsp8').createFile('diag_202605_' + ts + '.txt', result);
  Logger.log('診断ファイルID: ' + diagFile.getId());
}

/**
 * 新MASTERのSS修正（初回1回だけ実行）
 * 1. C列曜日: TEXT(B,"aaa")→CHOOSE(WEEKDAY)に修正
 * 2. AI2ラベル: 「前月最終週の累計:」を追加
 * 3. ログシート追加: 処理キュー・実績ログ
 * 4. 設定C2を2026/5/1に設定
 */
function fixNewMasterSS() {
  const NEW_MASTER_ID = '1z8dGrmxz1igWwzjKGlcqaIutlMLcPOBiicbN69xi_DE';
  const ss = SpreadsheetApp.openById(NEW_MASTER_ID);
  const allSheets = ss.getSheets().map(s => s.getName());
  Logger.log('【シート一覧】' + allSheets.join(', '));

  // 設定C2を2026/5/1に修正（B4=DATE(D2,G2,1)の起点）
  const settingSheet = ss.getSheetByName('設定');
  if (settingSheet) {
    settingSheet.getRange('C2').setValue(new Date(2026, 4, 1)); // 2026/5/1
    Logger.log('設定!C2 → 2026/5/1 に設定');
  }

  const skipSheets = ['実績', '設定', '社員マスタ', '集計', '処理キュー', '実績ログ'];
  const personalSheets = allSheets.filter(n => !skipSheets.includes(n));

  personalSheets.forEach(name => {
    const sheet = ss.getSheetByName(name);

    // 1. C列の曜日数式を修正（C4:C34）
    for (let row = 4; row <= 34; row++) {
      sheet.getRange(row, 3).setFormula(
        '=IF(B' + row + '="","",CHOOSE(WEEKDAY(B' + row + ',1),"日","月","火","水","木","金","土"))'
      );
    }

    // 2. AI2に「前月最終週の累計:」ラベルを追加
    sheet.getRange('AI2').setValue('前月最終週の累計:');
    sheet.getRange('AI2').setHorizontalAlignment('right');

    Logger.log(name + ': C列曜日修正 + AI2ラベル追加完了');
  });

  // 3. ログシートを追加
  const logsToAdd = [
    { name: '処理キュー', headers: [['受信日時(JST)', 'メッセージ', '状態']] },
    { name: '実績ログ',   headers: [['氏名', '日付', '状態', '場所', '残業', '弁当', 'タイムスタンプ', '元のメッセージ']] }
  ];
  logsToAdd.forEach(({name, headers}) => {
    if (!ss.getSheetByName(name)) {
      const sheet = ss.insertSheet(name);
      sheet.getRange(1, 1, 1, headers[0].length).setValues(headers);
      sheet.getRange(1, 1, 1, headers[0].length).setFontWeight('bold').setBackground('#444444').setFontColor('#ffffff');
      sheet.setFrozenRows(1);
      Logger.log(name + ' シートを追加');
    }
  });

  Logger.log('✅ 全修正完了');
}

/**
 * 個人出勤簿シートの書式整形
 */
function formatAttendanceSheets(ss) {
  ss = ss || SpreadsheetApp.getActiveSpreadsheet();
  const SKIP = ['実績','設定','社員マスタ','集計','処理キュー','実績ログ','診断ログ'];
  const personalSheets = ss.getSheets().filter(s => !SKIP.includes(s.getName()));
  personalSheets.forEach(sheet => {
    const lastCol = 31;
    // タイトル行（Row1）ネイビー
    sheet.getRange(1, 1, 1, lastCol)
      .setBackground('#1F3864').setFontColor('#FFFFFF')
      .setFontFamily('游ゴシック').setFontSize(20).setFontWeight('bold')
      .setHorizontalAlignment('center').setVerticalAlignment('middle');
    // 年月・氏名行（Row2）淡ブルー
    sheet.getRange(2, 1, 1, lastCol)
      .setBackground('#DEEAF1').setFontColor('#1F3864')
      .setFontFamily('游ゴシック').setFontSize(14).setFontWeight('bold')
      .setHorizontalAlignment('center').setVerticalAlignment('middle');
    // ヘッダー行（Row3）スチールブルー
    sheet.getRange(3, 1, 1, lastCol)
      .setBackground('#2E75B6').setFontColor('#FFFFFF')
      .setFontFamily('游ゴシック').setFontSize(11).setFontWeight('bold')
      .setHorizontalAlignment('center').setVerticalAlignment('middle').setWrap(true);
    // データ行（Row4〜34）白ベース
    sheet.getRange(4, 1, 31, lastCol)
      .setBackground('#FFFFFF').setFontColor('#2C3E50')
      .setFontFamily('游ゴシック').setFontSize(10)
      .setHorizontalAlignment('center').setVerticalAlignment('middle');
    // 合計行（Row35）淡イエロー
    sheet.getRange(35, 1, 1, lastCol)
      .setBackground('#FFF2CC').setFontColor('#1F3864')
      .setFontFamily('游ゴシック').setFontSize(12).setFontWeight('bold')
      .setHorizontalAlignment('center').setVerticalAlignment('middle');
    // 集計エリア（Row37〜41）薄グレー
    sheet.getRange(37, 1, 5, lastCol)
      .setBackground('#F2F2F2').setFontColor('#1F3864')
      .setFontFamily('游ゴシック').setFontSize(9)
      .setHorizontalAlignment('center').setVerticalAlignment('middle');
    // 行ごとのフォントサイズ調整
    sheet.getRange(37, 1, 1, lastCol).setFontSize(9);  // 見出し行
    sheet.getRange(38, 1, 1, lastCol).setFontSize(10); // 日数値行
    sheet.getRange(40, 1, 1, lastCol).setFontSize(9);  // 見出し行
    sheet.getRange(41, 1, 1, lastCol).setFontSize(9);  // 時間値行
    // 条件付き書式：土曜=淡ブルー、日曜=淡コーラル
    const dataRange = sheet.getRange('A4:AE34');
    const existingRules = sheet.getConditionalFormatRules();
    const filtered = existingRules.filter(r => {
      const fc = r.getBooleanCondition();
      if (!fc) return true;
      const formula = fc.getCriteriaValues()[0];
      return !formula || (!formula.includes('"土"') && !formula.includes('"日"'));
    });
    const satRule = SpreadsheetApp.newConditionalFormatRule()
      .whenFormulaSatisfied('=$C4="土"').setBackground('#DEEAF1')
      .setRanges([dataRange]).build();
    const sunRule = SpreadsheetApp.newConditionalFormatRule()
      .whenFormulaSatisfied('=$C4="日"').setBackground('#FCE4D6')
      .setRanges([dataRange]).build();
    sheet.setConditionalFormatRules([...filtered, satRule, sunRule]);
    // 枠線（A列は非表示なのでB列から外枠を設定）
    sheet.getRange(1, 2, 41, lastCol - 1)
      .setBorder(true, true, true, true, null, null, '#1F3864', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
    sheet.getRange(3, 1, 1, lastCol)
      .setBorder(null, null, true, null, null, null, '#1F3864', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
    sheet.getRange(35, 1, 1, lastCol)
      .setBorder(true, null, true, null, null, null, '#C9A227', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
    sheet.getRange(4, 1, 31, lastCol)
      .setBorder(null, null, null, null, true, true, '#B8CCE4', SpreadsheetApp.BorderStyle.SOLID);
    // 行高の最適化（A4縦で下の余白が出ないよう調整）
    sheet.setRowHeight(1, 44);
    sheet.setRowHeight(2, 30);
    sheet.setRowHeight(3, 28);
    for (let r = 4; r <= 34; r++) sheet.setRowHeight(r, 24);
    sheet.setRowHeight(35, 28);
    sheet.setRowHeight(36, 10);
    sheet.setRowHeight(37, 28);
    sheet.setRowHeight(38, 28);
    sheet.setRowHeight(39, 10);
    sheet.setRowHeight(40, 28);
    sheet.setRowHeight(41, 28);

    // A4縦に最適化した列幅設定
    const colWidths = [
      21,              // A: 行番号
      36,              // B: 日付（狭める）
      42, 35, 35,      // C: 曜日（広げる）、D〜E: 出勤状態
      35, 35, 35, 35,  // F〜I: 現場名（4列）
      35, 35,          // J〜K: 出社時間（37-38行統一）
      36, 36,          // L〜M: 現場開始
      36, 36,          // N〜O: 現場終了
      36, 36,          // P〜Q: 退社時間
      42, 42, 42, 42, 42, 42, 42, 42, 42,  // R〜Z: 時間各列（広げる）
      28, 28, 28, 28, 28  // AA〜AE: 備考
    ];
    colWidths.forEach((w, i) => sheet.setColumnWidth(i + 1, w));

    // F〜I列（現場名）: フォント8pt + 折り返しオフ（縮小表示に近い効果）
    sheet.getRange(4, 6, 34, 4)
      .setFontSize(8)
      .setWrap(false);

    // C41: 縮小表示（フォント7ptで収める）
    sheet.getRange(41, 3).setFontSize(7).setWrap(false);

    // 35行目（合計行）の高さを広げる
    sheet.setRowHeight(35, 32);

    // D列（4列目）にドロップダウン：勤怠区分
    const dRule = SpreadsheetApp.newDataValidation()
      .requireValueInList(['出勤', '休日', '休出', '振出', '振休', '有給', '欠勤', '特別'], true)
      .setAllowInvalid(true)
      .build();
    sheet.getRange(4, 4, 31, 1).setDataValidation(dRule);

    // AA列（27列目）にドロップダウン：現場区分
    const aaRule = SpreadsheetApp.newDataValidation()
      .requireValueInList(['工場', '現場', '出張'], true)
      .setAllowInvalid(true)
      .build();
    sheet.getRange(4, 27, 31, 1).setDataValidation(aaRule);

    // A列（1列目）を非表示
    sheet.hideColumns(1, 1);

    // AF(32)以降の列表示制御
    // ・AF〜AJ(32〜36): 未使用または実績参照列 → 非表示
    // ・AK(37)「例外出社」/ AL(38)「例外退社」: ユーザー入力列 → 表示（印刷範囲外なのでPDFには出ない）
    // ・AM(39)以降: 未使用・計算補助列 → 非表示
    const totalCols = sheet.getLastColumn();
    if (totalCols > 31) {
      // AF〜AJ を非表示（5列）
      if (totalCols >= 36) sheet.hideColumns(32, 5);
      // AK・AL を表示（例外出社/退社）
      if (totalCols >= 38) {
        sheet.showColumns(37, 2);
        sheet.setColumnWidth(37, 42);
        sheet.setColumnWidth(38, 42);
      }
      // AM(39)以降を非表示
      if (totalCols >= 39) sheet.hideColumns(39, totalCols - 38);
    }

    // X2（氏名ラベル）を右揃えに設定
    sheet.getRange(2, 24).setHorizontalAlignment('right');

    Logger.log('整形完了: ' + sheet.getName());
  });
  SpreadsheetApp.flush();
  Logger.log('✅ 全シート整形完了');
}

function applyFormatToCurrentFile() {
  formatAttendanceSheets(SpreadsheetApp.getActiveSpreadsheet());
  SpreadsheetApp.getUi().alert('✅ 書式の適用が完了しました');
}

/**
 * スクリプトプロパティにBOSSのLINE User IDを保存（初回1回実行）
 */
function setBossLineUserId() {
  PropertiesService.getScriptProperties().setProperty('BOSS_LINE_USER_ID', 'U465d9c8a020c1dbd130a7f2f1f8cb326');
  Logger.log('✅ BOSS_LINE_USER_ID を保存しました');
}

/**
 * スキップ発生時に社長のLINEに通知
 */
function notifySkipToLine(message, reason) {
  const token = PropertiesService.getScriptProperties().getProperty('LINE_CHANNEL_TOKEN');
  const bossId = PropertiesService.getScriptProperties().getProperty('BOSS_LINE_USER_ID');
  if (!token || !bossId) {
    Logger.log('LINE通知スキップ: LINE_CHANNEL_TOKEN または BOSS_LINE_USER_ID が未設定');
    return;
  }
  const preview = message.length > 50 ? message.substring(0, 50) + '...' : message;
  const text = '⚠️ 勤怠スキップ発生\n' + reason + '\n\n内容:\n' + preview;
  try {
    UrlFetchApp.fetch('https://api.line.me/v2/bot/message/push', {
      method: 'post',
      headers: {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
      },
      payload: JSON.stringify({
        to: bossId,
        messages: [{ type: 'text', text: text }]
      }),
      muteHttpExceptions: true
    });
  } catch(e) {
    Logger.log('LINE通知エラー: ' + e.message);
  }
}

// 月別SSの整形（run-gas経由用）
function formatMonthlySSById(ssId) {
  const ss = SpreadsheetApp.openById(ssId || '18z2alGnfRlvsuSKUlsd1x0z9SXPxbbxf_HETCMGqUlw');
  formatAttendanceSheets(ss);
}

// スキップ通知テスト（設定確認用）
function testSkipNotify() {
  const token = PropertiesService.getScriptProperties().getProperty('LINE_CHANNEL_TOKEN');
  const bossId = PropertiesService.getScriptProperties().getProperty('BOSS_LINE_USER_ID');
  Logger.log('TOKEN存在: ' + (token ? 'YES (' + token.length + '文字)' : 'NO'));
  Logger.log('BOSS_ID: ' + (bossId || 'NO'));
  notifySkipToLine('テストメッセージ', '通知テスト');
  Logger.log('通知送信完了');
}

/**
 * 個人シートをA1:AE41の範囲でPDF化してDriveに保存
 * ssId: 対象スプレッドシートID（省略時はアクティブSS）
 * folderId: 保存先フォルダID（省略時はMONTHLY_FOLDER_ID）
 */
function exportAllSheetsToPDF(ssId, folderId) {
  ssId = ssId || SpreadsheetApp.getActiveSpreadsheet().getId();
  folderId = folderId || MONTHLY_FOLDER_ID;

  const ss = SpreadsheetApp.openById(ssId);
  const ssName = ss.getName();
  const folder = DriveApp.getFolderById(folderId);
  const SKIP = ['実績','設定','社員マスタ','集計','処理キュー','実績ログ','診断ログ'];
  const token = ScriptApp.getOAuthToken();

  ss.getSheets().filter(s => !SKIP.includes(s.getName())).forEach(sheet => {
    const gid = sheet.getSheetId();
    // range=A1:AE41 で印刷範囲を固定
    const url = `https://docs.google.com/spreadsheets/d/${ssId}/export`
      + `?format=pdf&gid=${gid}`
      + `&range=A1%3AAE41`      // A1:AE41
      + `&portrait=true`         // 縦向き(A4タテ)
      + `&fitw=true`             // 幅に合わせる
      + `&top_margin=0.5&bottom_margin=0.5&left_margin=0.5&right_margin=0.5`
      + `&sheetnames=false&printtitle=false&pagenumbers=false`
      + `&gridlines=false`;

    const res = UrlFetchApp.fetch(url, {
      headers: { Authorization: 'Bearer ' + token },
      muteHttpExceptions: true
    });

    // ファイル名の全角スペースを半角に変換（開けない問題の回避）
    const fileName = (ssName + '_' + sheet.getName() + '.pdf').replace(/　/g, ' ');
    // 同名の古いPDFを先に削除
    const existing = folder.getFilesByName(fileName);
    while (existing.hasNext()) existing.next().setTrashed(true);
    const pdfFile = folder.createFile(res.getBlob().setName(fileName));
    // リンクを知っている全員が閲覧可能に設定
    pdfFile.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
    Logger.log('PDF保存: ' + fileName + ' | ' + pdfFile.getUrl());
  });
  Logger.log('✅ 全シートPDF出力完了');
}

// 古いPDFを一括削除（IDリストをゴミ箱へ）
function trashOldPDFs() {
  const oldIds = [
    '1IAcEcbTlSCZsIDxIvXCcuAZcmeX_HRVl',
    '1CVnzD1t8YaCA0SW6EVy216n5L_d2JFt_',
    '1QWTw8nC7lxGomhtV0hfgfmiRqFs7zYBL',
    '1uG7SDDh51VXc7ZSeegKICtVg2wzLIxHf',
    '1b5ZJeapCd3Iw797_3odjCZ76LSuMp1un',
    '1CKor4xZrdB_wsuFqEfT0kqaExIxK2YjP',
    '1sLxu9Oon2KkUmK3U9RgQlZlbXsBP9kqs',
    '1czT8VPu5v1ekf0-p88yMm-fIC9DCyQQK',
    // 全角スペース版（追加分）
    '1wiA334J9Z1y21F5u4l4d6YDJwezsZdQv',
    '1DrUsQ55DNykR8a2JxX4Rh8jM2YXCUUsc',
    '1vIX9K2D1-5bAnV-SO7_otAcdUKwl7bql',
    '1dngFJCLwXrXDkNnxjRTyEzwWbQpuQiTs',
    '12KUP1RJOKaE9z7JStH-o65Glk06217TY',
    '18wbQv9O1agay_d9tSCm38QV-HYdIAKOr',
  ];
  oldIds.forEach(id => {
    try { DriveApp.getFileById(id).setTrashed(true); Logger.log('削除: ' + id); }
    catch(e) { Logger.log('削除スキップ: ' + id); }
  });
  Logger.log('✅ 古いPDF削除完了');
}

function checkPDFFile() {
  const id = '1caXShQBYHdXLINCopYarvYqO2krmxdVu';
  try {
    const f = DriveApp.getFileById(id);
    Logger.log('名前: ' + f.getName());
    Logger.log('サイズ: ' + f.getSize() + ' bytes');
    Logger.log('MIME: ' + f.getMimeType());
    Logger.log('オーナー: ' + f.getOwner().getEmail());
    Logger.log('共有: ' + f.getSharingAccess());
    Logger.log('権限: ' + f.getSharingPermission());
    Logger.log('URL: ' + f.getUrl());
  } catch(e) {
    Logger.log('エラー: ' + e.message);
  }
}

// ============================================================
// 現場マスタ管理（ゆらぎ正規化 + 種別判定 + 自動追加）
// ============================================================

/** 初期登録する既知の現場データ */
const SITE_MASTER_DEFAULTS = [
  { name: 'AGC工場',      type: '工場', variations: ['AGC', '旭硝子', 'AGC旭硝子'] },
  { name: '新興プラント', type: '現場', variations: ['新興', '新興産業'] },
];

/**
 * 現場マスタシートを MASTER SS + 202605 SS に作成・初期登録
 * 「現場マスタ」シート: A=正規名 / B=種別 / C=ゆらぎ(カンマ区切り) / D=登録日 / E=備考
 */
function setupSiteMaster() {
  const targets = [SpreadsheetApp.openById(MASTER_SS_ID)];
  const folder = DriveApp.getFolderById(MONTHLY_FOLDER_ID);
  const files = folder.getFilesByName('202605_福岡プラント出勤簿');
  if (files.hasNext()) targets.push(SpreadsheetApp.openById(files.next().getId()));

  const results = [];
  targets.forEach(ss => {
    let sheet = ss.getSheetByName('現場マスタ');
    if (!sheet) sheet = ss.insertSheet('現場マスタ');

    // ヘッダー
    const hdrs = ['正規名', '種別(工場/現場/出張)', 'ゆらぎ（カンマ区切り）', '登録日', '備考'];
    sheet.getRange(1, 1, 1, hdrs.length).setValues([hdrs])
      .setFontWeight('bold').setBackground('#2E75B6').setFontColor('#FFFFFF');
    sheet.setFrozenRows(1);
    sheet.setColumnWidth(1, 150); sheet.setColumnWidth(2, 120);
    sheet.setColumnWidth(3, 200); sheet.setColumnWidth(4, 100); sheet.setColumnWidth(5, 200);

    // 既存エントリ取得
    const lastRow = sheet.getLastRow();
    const existingNames = lastRow > 1
      ? sheet.getRange(2, 1, lastRow - 1, 1).getValues().flat().map(String).filter(Boolean)
      : [];

    const today = Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy-MM-dd');
    let added = 0;
    SITE_MASTER_DEFAULTS.forEach(site => {
      if (!existingNames.includes(site.name)) {
        sheet.appendRow([site.name, site.type, site.variations.join(','), today, '']);
        added++;
      }
    });
    results.push(ss.getName() + ': ' + added + '件追加（既存' + existingNames.length + '件）');
  });
  SpreadsheetApp.flush();
  return '✅ 現場マスタ設定完了\n' + results.join('\n');
}

/**
 * 現場マスタシートからマッピング・種別データを取得
 * @returns { mappings: {ゆらぎ→正規名}, types: {正規名→種別} }
 */
function getSiteMasterData(ss) {
  const sheet = ss.getSheetByName('現場マスタ');
  if (!sheet || sheet.getLastRow() < 2) return { mappings: {}, types: {} };

  const data = sheet.getRange(2, 1, sheet.getLastRow() - 1, 3).getValues();
  const mappings = {}, types = {};
  data.forEach(row => {
    const name = String(row[0]).trim();
    const type = String(row[1]).trim();
    const variStr = String(row[2]).trim();
    if (!name) return;
    mappings[name] = name;
    types[name] = type;
    variStr.split(',').forEach(v => {
      const vt = v.trim();
      if (vt) { mappings[vt] = name; types[vt] = type; }
    });
  });
  return { mappings, types };
}

/**
 * 未知の現場名を現場マスタに自動追加して社長LINEに通知
 */
function addSiteToMaster(ss, siteName, sourceMsg) {
  const sheet = ss.getSheetByName('現場マスタ');
  if (!sheet) return;
  const lastRow = sheet.getLastRow();
  if (lastRow > 1) {
    const existing = sheet.getRange(2, 1, lastRow - 1, 1).getValues().flat().map(String);
    if (existing.includes(siteName)) return;
  }
  const today = Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy-MM-dd');
  sheet.appendRow([siteName, '不明', '', today, 'LINE自動追加: ' + String(sourceMsg).substring(0, 40)]);
  notifySkipToLine(
    '📍 新しい現場名を検出しました\n現場名: ' + siteName + '\n\n現場マスタに「不明」で追加しました。\n種別（工場/現場/出張）を設定してください。',
    '新規現場名自動追加'
  );
  Logger.log('現場マスタ自動追加: ' + siteName);
}

// 後方互換（設定シートのゆらぎ辞書は現場マスタに移行済み）
function getLocationMappings(ss) {
  return getSiteMasterData(ss).mappings;
}

// 後方互換（現場マスタに統合済み）
function setupFuzzyLocationDict() {
  return setupSiteMaster();
}

/**
 * Phase 2 修正：全個人シートのRow38集計式をD列新仕様に合わせて書き換える
 * 対象：指定SSまたはMASTER SS + 202605 SS の両方
 *
 * Row38修正内容:
 *   C38: 出勤日数 = COUNTIF(D4:D34,"出勤")+COUNTIF(D4:D34,"振出")  ← 旧:"工場/現場/出張"
 *   D38: 有給日数 = COUNTIF(D4:D34,"有給")                         ← 範囲修正
 *   E38: 休出日数 = COUNTIF(D4:D34,"休出")                         ← 範囲修正
 *   F38: 特別日数 = COUNTIF(D4:D34,"特別")                         ← 旧:$C$5:$C$35（曜日列！）
 *   G38: 欠勤日数 = COUNTIF(D4:D34,"欠勤")                         ← 旧:$C$5:$C$35（曜日列！）
 *
 * Row37のC〜G列ラベルも新仕様に更新する
 * D列ドロップダウン（D4:D34）を設定する
 */
function fixPhase2Formulas(ssId) {
  const targets = [];

  // 202605 SS
  const folder = DriveApp.getFolderById(MONTHLY_FOLDER_ID);
  const files = folder.getFilesByName('202605_福岡プラント出勤簿');
  if (files.hasNext()) targets.push(SpreadsheetApp.openById(files.next().getId()));

  // MASTER SS
  targets.push(SpreadsheetApp.openById(MASTER_SS_ID));

  // ssId が指定されていれば追加（重複除去）
  if (ssId && ssId !== MASTER_SS_ID) targets.push(SpreadsheetApp.openById(ssId));

  const SKIP = ['実績','設定','社員マスタ','集計','処理キュー','実績ログ','診断ログ'];
  const D_RULE = SpreadsheetApp.newDataValidation()
    .requireValueInList(['出勤','休日','休出','振出','振休','有給','欠勤','特別'], true)
    .setAllowInvalid(true).build();
  const AA_RULE = SpreadsheetApp.newDataValidation()
    .requireValueInList(['工場','現場','出張'], true)
    .setAllowInvalid(true).build();

  const results = [];

  targets.forEach(ss => {
    const ssName = ss.getName();
    ss.getSheets().filter(s => !SKIP.includes(s.getName())).forEach(sheet => {
      const name = sheet.getName();

      // Row37 ラベル（C〜G）
      sheet.getRange(37, 3).setValue('出勤日数');
      sheet.getRange(37, 4).setValue('有給');
      sheet.getRange(37, 5).setValue('休出');
      sheet.getRange(37, 6).setValue('特別');
      sheet.getRange(37, 7).setValue('欠勤');

      // Row38 集計式
      sheet.getRange(38, 3).setFormula('=COUNTIF(D4:D34,"出勤")+COUNTIF(D4:D34,"振出")');
      sheet.getRange(38, 4).setFormula('=COUNTIF(D4:D34,"有給")');
      sheet.getRange(38, 5).setFormula('=COUNTIF(D4:D34,"休出")');
      sheet.getRange(38, 6).setFormula('=COUNTIF(D4:D34,"特別")');
      sheet.getRange(38, 7).setFormula('=COUNTIF(D4:D34,"欠勤")');

      // D列ドロップダウン（D4:D34）
      sheet.getRange(4, 4, 31, 1).setDataValidation(D_RULE);
      // AA列ドロップダウン（AA4:AA34）
      sheet.getRange(4, 27, 31, 1).setDataValidation(AA_RULE);

      results.push('[修正済] ' + ssName + ' > ' + name);
    });
    SpreadsheetApp.flush();
  });

  const summary = results.join('\n');
  Logger.log(summary);
  return '✅ Phase2修正完了\n' + summary;
}

/**
 * P4残業参照を OFFSET方式で修正（最重要バグ修正）
 *
 * 問題: P4の数式が全員「'実績'!C5」(土本固定)を参照していた
 *       → 日付が変わっても列がズレず、坂井など他の社員の残業が反映されない
 *
 * 修正: OFFSET('実績'!$C$1, $AH$2-1, ROW()-4) を使用
 *   ・$AH$2 = 各社員の残業行番号（MATCH式で動的取得）
 *   ・ROW()-4 = 日付に対応するカラムオフセット（day1=0, day2=1...）
 *
 * 元Excel参照行（確認済み）:
 *   土本=5, 中嶋=9, 坂井=13, 石村=17, 鳳ノ城=21, 福山=25, 内村=29
 */
function fixOvertimeFormulas() {
  const SKIP = ['実績','設定','社員マスタ','集計','処理キュー','実績ログ','診断ログ','現場マスタ'];

  // AH2ヘルパー: 実績シートから自社員の残業行を動的取得（AB2=シート名=社員フルネーム）
  const AH2_FORMULA = "=IFERROR(MATCH(AB2,'実績'!$A:$A,0)+2,5)";

  // 新P4数式: OFFSETで社員別・日別に正しい実績セルを参照
  const NEW_P4 = '=IF($AL4<>"",$AL4,IF(OR($D4="出勤",$D4="休出",$D4="振出"),IF(WEEKDAY($B4,2)=6,15/24,17/24)+IFERROR(IF(ISNUMBER(OFFSET(\'実績\'!$C$1,$AH$2-1,ROW()-4)),OFFSET(\'実績\'!$C$1,$AH$2-1,ROW()-4)/24,0),0),IF(IF($J4<>"",$J4,$L4)<>"",IF($J4<>"",$J4,$L4)+IF(WEEKDAY($B4,2)=6,7/24,9/24)+IFERROR(IF(ISNUMBER(OFFSET(\'実績\'!$C$1,$AH$2-1,ROW()-4)),OFFSET(\'実績\'!$C$1,$AH$2-1,ROW()-4)/24,0),0),"")))'

  const targets = [SpreadsheetApp.openById(MASTER_SS_ID)];
  const folder = DriveApp.getFolderById(MONTHLY_FOLDER_ID);
  const files = folder.getFilesByName('202605_福岡プラント出勤簿');
  if (files.hasNext()) targets.push(SpreadsheetApp.openById(files.next().getId()));

  const results = [];
  targets.forEach(ss => {
    ss.getSheets().filter(s => !SKIP.includes(s.getName())).forEach(sheet => {
      // AH2 = MATCH式で社員の残業行番号を取得するヘルパーセル
      sheet.getRange(2, 34).setFormula(AH2_FORMULA);  // AH2 = col 34

      // P4:P34 に新しいOFFSET数式を適用（GASが行番号を自動調整）
      sheet.getRange(4, 16, 31, 1).setFormula(NEW_P4);

      results.push('[修正] ' + ss.getName() + ' > ' + sheet.getName());
    });
    SpreadsheetApp.flush();
  });

  const msg = '✅ P4残業OFFSET修正完了\n' + results.join('\n');
  Logger.log(msg);
  return msg;
}

/**
 * AH2とP4の修正状態を全社員シートで検証
 */
function verifyOvertimeFix() {
  const SKIP = ['実績','設定','社員マスタ','集計','処理キュー','実績ログ','診断ログ','現場マスタ'];
  const folder = DriveApp.getFolderById(MONTHLY_FOLDER_ID);
  const files = folder.getFilesByName('202605_福岡プラント出勤簿');
  const ss = files.hasNext() ? SpreadsheetApp.openById(files.next().getId()) : SpreadsheetApp.openById(MASTER_SS_ID);

  const lines = ['=== ' + ss.getName() + ' AH2・P4検証 ==='];
  ss.getSheets().filter(s => !SKIP.includes(s.getName())).forEach(sheet => {
    const ah2Val = sheet.getRange(2, 34).getValue();   // AH2実際の値
    const ah2Formula = sheet.getRange(2, 34).getFormula(); // AH2数式
    const p4Formula = sheet.getRange(4, 16).getFormula().substring(0, 60); // P4数式冒頭
    lines.push(sheet.getName() + ' | AH2値=' + ah2Val + ' | AH2式=' + (ah2Formula ? 'MATCH式あり' : 'なし') + ' | P4先頭=' + p4Formula);
  });
  return lines.join('\n');
}

/**
 * J4・P4の完全な数式をテキストで返す（修正前の確認用）
 */
function getTimeCellFormulas() {
  const folder = DriveApp.getFolderById(MONTHLY_FOLDER_ID);
  const files = folder.getFilesByName('202605_福岡プラント出勤簿');
  const ss = files.hasNext() ? SpreadsheetApp.openById(files.next().getId()) : SpreadsheetApp.openById(MASTER_SS_ID);
  const SKIP = ['実績','設定','社員マスタ','集計','処理キュー','実績ログ','診断ログ'];
  const sheet = ss.getSheets().find(s => !SKIP.includes(s.getName()));
  const j4 = sheet.getRange(4, 10).getFormula();
  const p4 = sheet.getRange(4, 16).getFormula();
  const result = 'J4=' + j4 + '\n\nP4=' + p4;
  Logger.log(result);
  return result;
}

/**
 * J4/P4の数式の旧D列値「現場/出張」を新値「出勤」に修正 + AK/AL列を表示
 * → 202605 SS・MASTER SS の全個人シートに適用（1回限り実行）
 */
function fixColumnFormulasAndVisibility() {
  const SKIP = ['実績','設定','社員マスタ','集計','処理キュー','実績ログ','診断ログ'];

  // 202605 SS を参照元として取得
  const folder = DriveApp.getFolderById(MONTHLY_FOLDER_ID);
  const files = folder.getFilesByName('202605_福岡プラント出勤簿');
  const refSS = files.hasNext() ? SpreadsheetApp.openById(files.next().getId()) : SpreadsheetApp.openById(MASTER_SS_ID);
  const refSheet = refSS.getSheets().find(s => !SKIP.includes(s.getName()));

  // 現在のJ4・P4数式を読み取り
  const origJ4 = refSheet.getRange(4, 10).getFormula();
  const origP4 = refSheet.getRange(4, 16).getFormula();

  // 旧D列値 "現場" "出張" を "出勤" に置換
  // 確認済みパターン: OR($D4="現場",$D4="出張",$D4="休出",$D4="振出")
  //              → OR($D4="出勤",$D4="休出",$D4="振出")
  const fixDCol = (f) =>
    f.replace(/"現場",\$D\d+="出張",/g, '"出勤",')  // メインパターン: 現場,出張 → 出勤
     .replace(/,\$D\d+="現場"/g, '')                 // 末尾に現場が残った場合の除去
     .replace(/,\$D\d+="出張"/g, '');                // 末尾に出張が残った場合の除去

  const newJ4 = fixDCol(origJ4);
  // P4はOFFSET方式に置き換え（fixOvertimeFormulasと同じ）
  const NEW_P4_OFFSET = '=IF($AL4<>"",$AL4,IF(OR($D4="出勤",$D4="休出",$D4="振出"),IF(WEEKDAY($B4,2)=6,15/24,17/24)+IFERROR(IF(ISNUMBER(OFFSET(\'実績\'!$C$1,$AH$2-1,ROW()-4)),OFFSET(\'実績\'!$C$1,$AH$2-1,ROW()-4)/24,0),0),IF(IF($J4<>"",$J4,$L4)<>"",IF($J4<>"",$J4,$L4)+IF(WEEKDAY($B4,2)=6,7/24,9/24)+IFERROR(IF(ISNUMBER(OFFSET(\'実績\'!$C$1,$AH$2-1,ROW()-4)),OFFSET(\'実績\'!$C$1,$AH$2-1,ROW()-4)/24,0),0),"")))'
  const AH2_FORMULA = "=IFERROR(MATCH(AB2,'実績'!$A:$A,0)+2,5)";

  const lines = ['J4 修正後: ' + newJ4, 'P4: OFFSET方式（社員別・日別）に変更'];

  // 適用対象SS（202605 + MASTER）
  const targets = [refSS];
  const masterSS = SpreadsheetApp.openById(MASTER_SS_ID);
  if (refSS.getId() !== MASTER_SS_ID) targets.push(masterSS);

  targets.forEach(ss => {
    ss.getSheets().filter(s => !SKIP.includes(s.getName())).forEach(sheet => {
      const lastCol = sheet.getLastColumn();

      // J4:J34 に修正数式を適用（GASが行番号を自動調整）
      sheet.getRange(4, 10, 31, 1).setFormula(newJ4);
      // P4:P34 にOFFSET方式の数式を適用
      sheet.getRange(2, 34).setFormula(AH2_FORMULA); // AH2ヘルパー
      sheet.getRange(4, 16, 31, 1).setFormula(NEW_P4_OFFSET);

      // ── 列表示/非表示の修正 ──
      // まず AF(32)以降を全非表示
      if (lastCol > 31) sheet.hideColumns(32, lastCol - 31);
      // AK(37)・AL(38)=例外出社/退社 → 表示（ユーザー入力列）
      if (lastCol >= 38) {
        sheet.showColumns(37, 2);
        sheet.setColumnWidth(37, 42); // AK: 例外出社
        sheet.setColumnWidth(38, 42); // AL: 例外退社
      }

      lines.push('[修正] ' + ss.getName() + ' > ' + sheet.getName());
    });
    SpreadsheetApp.flush();
  });

  return '✅ 完了\n' + lines.join('\n');
}

/**
 * 列構造完全診断：非表示列・入力列・数式の全体マップをDriveに書き出す
 */
function diagnoseColumnStructure() {
  const folder = DriveApp.getFolderById(MONTHLY_FOLDER_ID);
  const files = folder.getFilesByName('202605_福岡プラント出勤簿');
  const ss = files.hasNext()
    ? SpreadsheetApp.openById(files.next().getId())
    : SpreadsheetApp.openById(MASTER_SS_ID);

  const SKIP = ['実績','設定','社員マスタ','集計','処理キュー','実績ログ','診断ログ'];
  const sheet = ss.getSheets().find(s => !SKIP.includes(s.getName()));
  if (!sheet) return 'ERROR: 個人シートなし';

  const lastCol = sheet.getLastColumn();
  const lines = [];
  lines.push('=== ' + ss.getName() + ' > ' + sheet.getName() + ' ===');
  lines.push('最終列: ' + lastCol + ' (' + columnToLetter(lastCol) + ')');
  lines.push('');

  // 各列の「非表示」「数式/値」を全列スキャン
  lines.push('--- 全列マップ（Row4の数式/値 + 非表示フラグ）---');
  for (let c = 1; c <= lastCol; c++) {
    const letter = columnToLetter(c);
    const hidden = sheet.isColumnHiddenByUser(c);
    const cell = sheet.getRange(4, c);
    const formula = cell.getFormula();
    const value = cell.getValue();
    const hasFormula = formula !== '';
    const hasValue = value !== '' && value !== null && value !== 0;
    const dv = cell.getDataValidation();

    let desc = letter + '(' + c + ')';
    desc += hidden ? ' [非表示]' : ' [表示]';
    desc += hasFormula ? ' 数式: ' + formula.substring(0, 80) :
            hasValue   ? ' 値: ' + String(value).substring(0, 40) : ' (空)';
    if (dv) desc += ' [DD]';
    lines.push(desc);
  }

  // J/K/L/M/N/O/P/Q の詳細（Row3ヘッダーも含む）
  lines.push('\n--- J〜Q列 Row3ヘッダー ---');
  for (let c = 10; c <= 17; c++) {
    const h3 = sheet.getRange(3, c).getValue();
    lines.push(columnToLetter(c) + '3: ' + h3);
  }

  // Row3全体のヘッダーを出力（A〜AE）
  lines.push('\n--- Row3ヘッダー全列（A〜AE） ---');
  const row3 = sheet.getRange(3, 1, 1, Math.min(lastCol, 35)).getValues()[0];
  row3.forEach((v, i) => {
    if (v) lines.push(columnToLetter(i+1) + '3: ' + v);
  });

  // 非表示列のRow3ヘッダー（AF以降）
  lines.push('\n--- Row3ヘッダー（AF以降、非表示列）---');
  for (let c = 32; c <= lastCol; c++) {
    const h3 = sheet.getRange(3, c).getValue();
    const h4f = sheet.getRange(4, c).getFormula();
    const h4v = sheet.getRange(4, c).getValue();
    if (h3 || h4f || h4v) {
      lines.push(columnToLetter(c) + '3: ' + h3 + ' | 4式: ' + (h4f || '(値:' + h4v + ')').substring(0,60));
    }
  }

  // 非表示列の一覧
  lines.push('\n--- 非表示列一覧 ---');
  const hiddenCols = [];
  for (let c = 1; c <= lastCol; c++) {
    if (sheet.isColumnHiddenByUser(c)) hiddenCols.push(columnToLetter(c) + '(' + c + ')');
  }
  lines.push(hiddenCols.join(', ') || 'なし');

  const content = lines.join('\n');
  const ts = Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyyMMdd_HHmmss');
  const diagFolder = DriveApp.getFolderById('1SGCPerV8CCHT6CcDI8-E6G2JbbmNmsp8');
  const f = diagFolder.createFile('col_structure_' + ts + '.txt', content, MimeType.PLAIN_TEXT);
  return 'DIAG: ' + f.getId() + '\n\n' + content;
}

/**
 * Phase2診断：個人シートのR〜Z列・BA〜BM列の数式をDriveテキストファイルに書き出す
 */
function diagnosePhase2() {
  const folder = DriveApp.getFolderById(MONTHLY_FOLDER_ID);
  const files = folder.getFilesByName('202605_福岡プラント出勤簿');
  const ss = files.hasNext()
    ? SpreadsheetApp.openById(files.next().getId())
    : SpreadsheetApp.openById(MASTER_SS_ID);

  const SKIP = ['実績','設定','社員マスタ','集計','処理キュー','実績ログ','診断ログ'];
  const sheet = ss.getSheets().find(s => !SKIP.includes(s.getName()));
  if (!sheet) { return 'ERROR: 個人シートが見つかりません'; }

  const lines = [];
  lines.push('=== 診断対象: ' + ss.getName() + ' > ' + sheet.getName() + ' ===');
  lines.push('最終列番号: ' + sheet.getLastColumn());
  lines.push('最終行番号: ' + sheet.getLastRow());

  // R〜Z列（18〜26列目）R4:Z35
  const rzFormulas = sheet.getRange(4, 18, 32, 9).getFormulas();
  lines.push('\n--- R〜Z列 サンプル数式（最初に見つかった非空の数式）---');
  ['R','S','T','U','V','W','X','Y','Z'].forEach((col, ci) => {
    const sample = rzFormulas.map(r => r[ci]).find(f => f.trim() !== '');
    lines.push(col + ': ' + (sample || '(空 or 固定値)'));
  });

  // Row35 合計行
  const row35f = sheet.getRange(35, 18, 1, 9).getFormulas()[0];
  lines.push('\n--- Row35合計行 R35:Z35 ---');
  ['R','S','T','U','V','W','X','Y','Z'].forEach((col, ci) => {
    lines.push(col + '35: ' + (row35f[ci] || '(空 or 値)'));
  });

  // BA〜BM列
  const lastCol = sheet.getLastColumn();
  if (lastCol >= 53) {
    const baWidth = Math.min(13, lastCol - 52);
    const baFormulas = sheet.getRange(4, 53, 32, baWidth).getFormulas();
    lines.push('\n--- BA〜BM列 サンプル数式 ---');
    for (let ci = 0; ci < baWidth; ci++) {
      const colL = columnToLetter(53 + ci);
      const sample = baFormulas.map(r => r[ci]).find(f => f.trim() !== '');
      lines.push(colL + ': ' + (sample || '(空 or 固定値)'));
    }
    const baRow35 = sheet.getRange(35, 53, 1, baWidth).getFormulas()[0];
    lines.push('\n--- Row35合計行 BA35:BM35 ---');
    for (let ci = 0; ci < baWidth; ci++) {
      lines.push(columnToLetter(53 + ci) + '35: ' + (baRow35[ci] || '(空 or 値)'));
    }
  } else {
    lines.push('\nBA列以降なし（最終列: ' + lastCol + '）');
  }

  // Row37〜41 集計エリア全数式
  lines.push('\n--- Row37〜41 集計エリア（全列）---');
  const collectRange = sheet.getRange(37, 1, 5, Math.min(lastCol, 35)).getFormulas();
  collectRange.forEach((row, ri) => {
    row.forEach((f, ci) => {
      if (f.trim()) lines.push('R' + (37+ri) + 'C' + (ci+1) + '(' + columnToLetter(ci+1) + (37+ri) + '): ' + f);
    });
  });

  // D4のドロップダウン
  lines.push('\n--- D列ドロップダウン ---');
  const dv = sheet.getRange(4, 4).getDataValidation();
  lines.push(dv ? JSON.stringify(dv.getCriteriaValues()) : 'なし');

  // AA列のドロップダウン
  lines.push('\n--- AA列ドロップダウン ---');
  const aaDv = sheet.getRange(4, 27).getDataValidation();
  lines.push(aaDv ? JSON.stringify(aaDv.getCriteriaValues()) : 'なし');

  const content = lines.join('\n');
  const ts = Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyyMMdd_HHmmss');
  const diagFolder = DriveApp.getFolderById('1SGCPerV8CCHT6CcDI8-E6G2JbbmNmsp8');
  const f = diagFolder.createFile('phase2_diag_' + ts + '.txt', content, MimeType.PLAIN_TEXT);
  return 'DIAG保存: ' + f.getId() + '\n\n' + content;
}

function columnToLetter(col) {
  let result = '';
  while (col > 0) {
    col--;
    result = String.fromCharCode(65 + (col % 26)) + result;
    col = Math.floor(col / 26);
  }
  return result;
}

// 月別SS新規作成時にRow2の氏名を設定（X2=「氏名：」右揃え、AB2=氏名）
function applyRow2Names(ss) {
  const SKIP = ['実績','設定','社員マスタ','集計','処理キュー','実績ログ','診断ログ'];
  ss.getSheets().filter(s => !SKIP.includes(s.getName())).forEach(sheet => {
    const sheetName = sheet.getName();
    sheet.getRange(2, 24).setValue('氏名：').setHorizontalAlignment('right'); // X2
    sheet.getRange(2, 28).setValue(sheetName); // AB2（結合セル先頭）
    sheet.getRange(2, 37).setValue('社長印'); // 社長印
    Logger.log(sheetName + ': Row2設定完了');
  });
}

// Row2の「氏名：」と氏名の位置を修正（W列・Y列に配置）
function fixRow2Layout() {
  const ss = SpreadsheetApp.openById('18z2alGnfRlvsuSKUlsd1x0z9SXPxbbxf_HETCMGqUlw');
  const SKIP = ['実績','設定','社員マスタ','集計','処理キュー','実績ログ','診断ログ'];
  ss.getSheets().filter(s => !SKIP.includes(s.getName())).forEach(sheet => {
    // Row2全体をスキャンして氏名ラベルと氏名の現在位置をクリア
    const row2 = sheet.getRange(2, 1, 1, 31).getValues()[0];
    row2.forEach((val, i) => {
      if (String(val).includes('氏名')) sheet.getRange(2, i + 1).clearContent();
    });

    // 氏名はシート名から直接取得（最も確実）
    const sheetName = sheet.getName();

    // W2（23列目）に「氏名：」を設定
    sheet.getRange(2, 23).setValue('氏名：');

    // Y2（25列目）に氏名を設定
    sheet.getRange(2, 25).setValue(sheetName);

    Logger.log(sheet.getName() + ': Row2レイアウト修正完了 → W2=氏名：, Y2=' + sheetName);
  });
}
