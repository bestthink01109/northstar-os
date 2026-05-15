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

  // 現場名ゆらぎ辞書を設定シートから読み込む
  const locationMappings = getLocationMappings(ss);
  Logger.log('ゆらぎ辞書件数: ' + Object.keys(locationMappings).length);

  const data = inputSheet.getDataRange().getValues();

  aiResult.forEach(entry => {
    // 現場名のゆらぎを正規化
    if (entry.場所 && locationMappings[entry.場所.trim()]) {
      Logger.log('現場名正規化: ' + entry.場所 + ' → ' + locationMappings[entry.場所.trim()]);
      entry.場所 = locationMappings[entry.場所.trim()];
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
    + '3. 状態は「出勤」「休日」「休出」「振出」「振休」「有給」「欠勤」「特別」のいずれか。場所や「定時」があれば「出勤」、出張も「出勤」（AA列で「出張」を別途管理）、「休み」「公休」は「休日」、休日出勤は「休出」とせよ。\n'
    + '4. 場所は「新興プラント」「AGC工場」など、地名や社名を含めて正確に抽出せよ。出張の場合は行先地名を場所に入れよ。\n'
    + '5. 残業は数値のみ（2.5など）。「なし」「定時」や未記載は 0 とせよ。\n'
    + '6. 弁当は「弁当」「べんとう」の文字があれば "〇"、なければ空文字 "" とせよ。\n'
    + '7. 勤怠に関係ない挨拶やスタンプ、雑談は完全に無視（スルー）し、[] を返せ。\n'
    + '8. 「全員弁当」などの表現は、そのメッセージに含まれる全員に適用せよ。\n\n'
    + '【社員リスト】\n' + staffNames + '\n\n'
    + '【見本1】5月7日 新興プラント 土本 中嶋 残業2\n回答：[{"氏名":"土本","日付":"2026-05-07","状態":"出勤","場所":"新興プラント","残業":2,"弁当":""},{"氏名":"中嶋","日付":"2026-05-07","状態":"出勤","場所":"新興プラント","残業":2,"弁当":""}]\n\n'
    + '【見本2】5月9日 AGC工場 土本 國松（部外者） 残業なし\n回答：[{"氏名":"土本","日付":"2026-05-09","状態":"出勤","場所":"AGC工場","残業":0,"弁当":""}]\n\n'
    + '【見本3】5月10日 名古屋出張 石村 弁当\n回答：[{"氏名":"石村","日付":"2026-05-10","状態":"出勤","場所":"名古屋","残業":0,"弁当":"〇"}]\n\n'
    + '【見本4】お疲れ様です。テストです。\n回答：[]\n\n'
    + '【見本5】5/9と10 新興プラント 土本 残業各2\n回答：[{"氏名":"土本","日付":"2026-05-09","状態":"出勤","場所":"新興プラント","残業":2,"弁当":""},{"氏名":"土本","日付":"2026-05-10","状態":"出勤","場所":"新興プラント","残業":2,"弁当":""}]\n\n'
    + '【見本6】5/11 土本 出勤 残業1\n回答：[{"氏名":"土本","日付":"2026-05-11","状態":"出勤","場所":"","残業":1,"弁当":""}]\n\n'
    + '【見本7】5/11(月) 現場：AGC 名前：土本 残業：3\n回答：[{"氏名":"土本","日付":"2026-05-11","状態":"出勤","場所":"AGC","残業":3,"弁当":""}]\n\n'
    + '【見本8】5/12 AGC 土本 石村 全員弁当 全員残業2\n回答：[{"氏名":"土本","日付":"2026-05-12","状態":"出勤","場所":"AGC","残業":2,"弁当":"〇"},{"氏名":"石村","日付":"2026-05-12","状態":"出勤","場所":"AGC","残業":2,"弁当":"〇"}]\n\n'
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

    // AE列(31列目)より後の計算補助列を非表示
    const totalCols = sheet.getLastColumn();
    if (totalCols > 31) sheet.hideColumns(32, totalCols - 31);

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

/**
 * 現場名ゆらぎ辞書：設定シートのマッピングテーブルを読み込む
 * 返値: { "ゆらぎ": "正規名", ... }
 */
function getLocationMappings(ss) {
  const sheet = ss.getSheetByName('設定');
  if (!sheet) return {};
  const mappings = {};
  for (let row = 16; row <= 60; row++) {
    const fuzzy = String(sheet.getRange(row, 2).getValue()).trim();
    if (!fuzzy) break;
    const canonical = String(sheet.getRange(row, 3).getValue()).trim();
    if (canonical) mappings[fuzzy] = canonical;
  }
  return mappings;
}

/**
 * 現場名ゆらぎ辞書の初期設定
 * MASTER SSおよび202605 SSの設定シートRow14以降にマッピングテーブルを書き込む
 * 社長がゆらぎを追加する際はB列:ゆらぎ / C列:正規名 の行を追加するだけでOK
 */
function setupFuzzyLocationDict() {
  const DEFAULT_MAPPINGS = [
    ['AGC',       'AGC工場'],
    ['旭硝子',    'AGC工場'],
    ['AGC旭硝子', 'AGC工場'],
    ['新興',      '新興プラント'],
    ['新興産業',  '新興プラント'],
  ];

  const targets = [SpreadsheetApp.openById(MASTER_SS_ID)];
  const folder = DriveApp.getFolderById(MONTHLY_FOLDER_ID);
  const files = folder.getFilesByName('202605_福岡プラント出勤簿');
  if (files.hasNext()) targets.push(SpreadsheetApp.openById(files.next().getId()));

  const results = [];
  targets.forEach(ss => {
    const sheet = ss.getSheetByName('設定');
    if (!sheet) { results.push(ss.getName() + ': 設定シートなし'); return; }

    // ヘッダー
    const hdr = sheet.getRange(14, 2);
    hdr.setValue('■ 現場名ゆらぎ辞書').setFontWeight('bold')
      .setBackground('#2E75B6').setFontColor('#FFFFFF');
    sheet.getRange(15, 2).setValue('ゆらぎ（入力値）').setFontWeight('bold').setBackground('#DEEAF1');
    sheet.getRange(15, 3).setValue('正規名（統一後）').setFontWeight('bold').setBackground('#DEEAF1');

    // マッピング行（既存があれば上書きしない → 16行目から空を見つけるまで確認）
    const existingCount = (() => {
      let c = 0;
      for (let r = 16; r <= 60; r++) {
        if (sheet.getRange(r, 2).getValue()) c++; else break;
      }
      return c;
    })();

    if (existingCount === 0) {
      DEFAULT_MAPPINGS.forEach((m, i) => {
        sheet.getRange(16 + i, 2).setValue(m[0]);
        sheet.getRange(16 + i, 3).setValue(m[1]);
      });
      results.push(ss.getName() + ': ' + DEFAULT_MAPPINGS.length + '件のデフォルトマッピングを追加');
    } else {
      results.push(ss.getName() + ': 既存マッピング' + existingCount + '件あり（上書きスキップ）');
    }
  });

  SpreadsheetApp.flush();
  const summary = results.join('\n');
  Logger.log(summary);
  return '✅ ゆらぎ辞書セットアップ完了\n' + summary;
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
