// ==========================================
// 福岡プラント 勤怠管理システム GASコア
// 【魂の完全版：BUN_CEOお帰りなさい仕様】
// 掟：手抜きをしない、網羅する。魂を込める。
// ==========================================

// --- 設定 ---
const GEMINI_API_KEY = ''; // BUN_CEO: 機密情報保護のためGitHubへのpush前に削除しました。GASのスクリプトプロパティを使用してください。
const MASTER_SS_ID = '1DtjFTdtvVsebZXUyVGIwdMAY97Er-hDKUhwIE90RTA4'; // 【雛形】福岡プラント出勤簿_MASTER
const GEMINI_MODEL_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key=' + GEMINI_API_KEY;

/**
 * 0. 初期設定・メニュー作成
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('★福岡プラント連携')
    .addItem('診断開始（AI解析テスト）', '診断開始')
    .addItem('社員名簿を更新', 'syncStaffList')
    .addToUi();
}

/**
 * 1. LINE受信処理 (doPost)
 */
function doPost(e) {
  if (!e || !e.postData || !e.postData.contents) return ContentService.createTextOutput("ok");
  
  const contents = JSON.parse(e.postData.contents);
  const events = contents.events || [];
  
  const ss = SpreadsheetApp.openById(MASTER_SS_ID);
  const staffList = getStaffList(ss);
  
  events.forEach(event => {
    if (event.type !== 'message' || event.message.type !== 'text') return;
    
    const userMessage = event.message.text;
    const aiResult = parseAttendanceWithGemini(userMessage, staffList);
    
    if (aiResult && aiResult.length > 0) {
      writeToLogSheet(aiResult, staffList, userMessage);
    }
  });
  
  return ContentService.createTextOutput("ok");
}

/**
 * 2. 共通：実績ログへの書き込み処理
 * 掟：並び順は A:氏名, B:日付, C:状態, D:場所, E:残業, F:弁当, G:タイムスタンプ, H:元のメッセージ
 */
function writeToLogSheet(aiResult, staffList, userMessage) {
  const ss = SpreadsheetApp.openById(MASTER_SS_ID);
  let logSheet = ss.getSheetByName('実績ログ');
  
  if (!logSheet) {
    logSheet = ss.insertSheet('実績ログ', 0);
  }

  // ヘッダー確認・修正（BUN_CEOのシート構成 A列：氏名 に合わせる）
  if (logSheet.getLastRow() === 0 || logSheet.getRange(1, 1).getValue() !== "氏名") {
    logSheet.clear();
    logSheet.getRange(1, 1, 1, 8).setValues([["氏名", "日付", "状態", "場所", "残業", "弁当", "タイムスタンプ", "元のメッセージ"]]);
    logSheet.getRange('A1:H1').setFontWeight('bold').setBackground('#444444').setFontColor('#ffffff');
    logSheet.setFrozenRows(1);
  }

  aiResult.forEach(entry => {
    // 氏名マッチング（フルネーム取得）
    const matchedStaff = staffList.find(s => entry.氏名 === s.lastName || entry.氏名 === s.fullName);
    const fullName = matchedStaff ? matchedStaff.fullName : entry.氏名;

    // 日付の処理（時間を0にして一括入力マスターに認識させる）
    let entryDate = new Date();
    if (entry.日付) {
      const parts = entry.日付.split('-'); // YYYY-MM-DD
      if (parts.length === 3) {
        entryDate = new Date(parts[0], parts[1] - 1, parts[2]);
      }
    }
    entryDate.setHours(0, 0, 0, 0);

    const rowValues = [[
      fullName,        // A:氏名
      entryDate,       // B:日付
      entry.状態,       // C:状態
      entry.場所,       // D:場所
      entry.残業,       // E:残業
      entry.弁当,       // F:弁当
      new Date(),      // G:タイムスタンプ
      userMessage      // H:元のメッセージ
    ]];

    // 確実に「最初の空行」を見つけて書き込む
    let targetRow = 1;
    const colA = logSheet.getRange("A:A").getValues();
    while (colA[targetRow - 1] && colA[targetRow - 1][0] !== "") {
      targetRow++;
    }
    logSheet.getRange(targetRow, 1, 1, 8).setValues(rowValues);

    // 【魂の追加】月別シート（例：2026.05）が存在しない場合は作成し、そちらにもバックアップとして追記（BUN_CEOの「5月分」への配慮）
    const monthSheetName = Utilities.formatDate(entryDate, "Asia/Tokyo", "yyyy.MM");
    let monthSheet = ss.getSheetByName(monthSheetName);
    if (!monthSheet) {
      monthSheet = ss.insertSheet(monthSheetName);
      monthSheet.getRange(1, 1, 1, 8).setValues([["氏名", "日付", "状態", "場所", "残業", "弁当", "タイムスタンプ", "元のメッセージ"]]);
    }
    monthSheet.appendRow(rowValues[0]);
  });
}

/**
 * 3. Gemini APIによるAI解析
 */
function parseAttendanceWithGemini(messageText, staffList) {
  const staffNames = staffList.map(s => s.lastName).join('、');
  const today = Utilities.formatDate(new Date(), "Asia/Tokyo", "yyyy-MM-dd");
  
  const prompt = 'あなたは建設会社の超優秀な事務員です。以下の【掟】を遵守し、LINEメッセージから勤怠情報をJSONで抽出せよ。\n\n'
    + '【掟】\n'
    + '1. 社員リストにある苗字が「本文に明記」されている場合のみ抽出せよ。存在しない名前は無視せよ。\n'
    + '2. 日付は YYYY-MM-DD 形式。年がなければ 2026年 とする。\n'
    + '3. 状態は「現場」「出張」「休み」のいずれか。場所の指定があれば「現場」、出張の文字があれば「出張」とせよ。\n'
    + '4. 場所は「新興プラント」「AGC工場」など、地名や社名を含めて正確に抽出せよ。\n'
    + '5. 残業は数値のみ（2.5など）。「なし」や未記載は 0 とせよ。\n'
    + '6. 弁当は「弁当」「べんとう」の文字があれば "〇"、なければ空文字 "" とせよ。\n'
    + '7. 勤怠に関係ない挨拶やスタンプ、雑談は完全に無視（スルー）し、[] を返せ。\n'
    + '8. 「全員弁当」などの表現は、そのメッセージに含まれる全員に適用せよ。\n\n'
    + '【社員リスト】\n' + staffNames + '\n\n'
    + '【見本1】5月7日 新興プラント 土本 中嶋 残業2\n回答：[{"氏名":"土本","日付":"2026-05-07","状態":"現場","場所":"新興プラント","残業":2,"弁当":""},{"氏名":"中嶋","日付":"2026-05-07","状態":"現場","場所":"新興プラント","残業":2,"弁当":""}]\n\n'
    + '【見本2】5月9日 AGC工場 土本 國松（部外者） 残業なし\n回答：[{"氏名":"土本","日付":"2026-05-09","状態":"現場","場所":"AGC工場","残業":0,"弁当":""}]\n\n'
    + '【見本3】5月10日 名古屋出張 石村 弁当\n回答：[{"氏名":"石村","日付":"2026-05-10","状態":"出張","場所":"名古屋","残業":0,"弁当":"〇"}]\n\n'
    + '【見本4】お疲れ様です。テストです。\n回答：[]\n\n'
    + '【見本5】5/9と10 新興プラント 土本 残業各2\n回答：[{"氏名":"土本","日付":"2026-05-09","状態":"現場","場所":"新興プラント","残業":2,"弁当":""},{"氏名":"土本","日付":"2026-05-10","状態":"現場","場所":"新興プラント","残業":2,"弁当":""}]\n\n'
    + '【見本6】5/11 土本 出勤 残業1\n回答：[{"氏名":"土本","日付":"2026-05-11","状態":"現場","場所":"","残業":1,"弁当":""}]\n\n'
    + '【見本7】5/11(月) 現場：AGC 名前：土本 残業：3\n回答：[{"氏名":"土本","日付":"2026-05-11","状態":"現場","場所":"AGC","残業":3,"弁当":""}]\n\n'
    + '【見本8】5/12 AGC 土本 石村 全員弁当 全員残業2\n回答：[{"氏名":"土本","日付":"2026-05-12","状態":"現場","場所":"AGC","残業":2,"弁当":"〇"},{"氏名":"石村","日付":"2026-05-12","状態":"現場","場所":"AGC","残業":2,"弁当":"〇"}]\n\n'
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

  try {
    const response = UrlFetchApp.fetch(GEMINI_MODEL_URL, {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });

    const resCode = response.getResponseCode();
    if (resCode !== 200) {
      Logger.log("APIエラー (Code: " + resCode + "): " + response.getContentText());
      return [];
    }

    const resJson = JSON.parse(response.getContentText());
    if (!resJson.candidates || !resJson.candidates[0].content) return [];

    let resultText = resJson.candidates[0].content.parts[0].text;
    resultText = resultText.replace(/```json|```/g, '').trim();
    const parsed = JSON.parse(resultText);
    return Array.isArray(parsed) ? parsed : [parsed];
  } catch (e) {
    Logger.log("解析失敗: " + e.message);
    return [];
  }
}

/**
 * 4. 社員マスター取得
 */
function getStaffList(ss) {
  const masterSheet = ss.getSheetByName('社員マスター');
  if (!masterSheet) return [];
  const data = masterSheet.getDataRange().getValues();
  const list = [];
  for (let i = 1; i < data.length; i++) {
    const lastName = String(data[i][0] || "").trim(); // A列：苗字
    const fullName = String(data[i][1] || "").trim(); // B列：フルネーム
    if (lastName) list.push({ lastName, fullName: fullName || lastName });
  }
  return list;
}

/**
 * 5. 診断開始（テストツール）
 */
function 診断開始() {
  const ss = SpreadsheetApp.openById(MASTER_SS_ID);
  const sheets = ss.getSheets();
  const sheetNames = sheets.map(s => s.getName()).join(', ');
  
  Logger.log("--- 【現場検証：スプレッドシート情報】 ---");
  Logger.log("ファイル名: " + ss.getName());
  Logger.log("ファイルURL: " + ss.getUrl());
  Logger.log("存在するシート一覧: " + sheetNames);
  Logger.log("---------------------------------------");

  const testMsg = "5月10日 新興プラント 大牟田工場\n土本 中嶋 石村 鳳ノ城 福山 内村\n残業2時間\n弁当全員あり";
  Logger.log("【1】テストメッセージ: " + testMsg);
  
  const staffList = getStaffList(ss);
  const aiResult = parseAttendanceWithGemini(testMsg, staffList);
  Logger.log("【2】AI解析結果: " + JSON.stringify(aiResult, null, 2));
  
  if (aiResult && aiResult.length > 0) {
    writeToLogSheet(aiResult, staffList, testMsg);
    Logger.log("【3】書き込み成功！シート「実績ログ」の最新行（一番左のシート）を確認してください。");
  } else {
    Logger.log("【3】失敗：解析できませんでした。API設定や名簿、プロンプトを確認してください。");
  }
}

function syncStaffList() {
  const ss = SpreadsheetApp.openById(MASTER_SS_ID);
  const staffList = getStaffList(ss);
  if (staffList.length > 0) {
    SpreadsheetApp.getUi().alert('社員名簿（' + staffList.length + '名）を読み込みました。');
  } else {
    SpreadsheetApp.getUi().alert('警告：社員マスターから名簿を取得できませんでした。A列に苗字があるか確認してください。');
  }
}
