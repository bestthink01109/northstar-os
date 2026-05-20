const fs = require('fs');
const http = require('http');

// APIキーとワークフローID
const apiKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxN2YwNGEyZS1iOWNhLTRjYmUtOTIxNS1kNjhkMDRjMDE0NjUiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiNjFlMWVjMDAtZGI3Ni00NjczLTk3NDItZGYzZDU2ZjA3ZjFiIiwiaWF0IjoxNzc4MTE3NzUxfQ.qX2xzujJHJyfQI0QezWozkv7-4xmYDbjppZfQZFlODQ";
const wfId = "ht60IBCItF9vt1vO";
const driveFolderId = "1I_68Pimq8jKjq6xfPMAeD22oeAHc8mTf";

console.log("==================================================");
console.log("MKT_PRタイムズ Drive成果物保存 2ステップアップロード修正 (完全版)");
console.log("==================================================");

// 1. 最新のワークフロー定義をAPIから直接取得する
console.log("[INFO] 最新のワークフロー定義を n8n API から取得します...");

const getReq = http.request({
  hostname: '162.43.78.67',
  port: 5678,
  path: `/api/v1/workflows/${wfId}`,
  method: 'GET',
  headers: {
    'X-N8N-API-KEY': apiKey,
    'Accept': 'application/json'
  }
}, (res) => {
  let data = '';
  res.on('data', d => data += d);
  res.on('end', () => {
    if (res.statusCode !== 200) {
      console.error(`[ERROR] ワークフロー取得に失敗しました。ステータス: ${res.statusCode}`);
      process.exit(1);
    }
    
     let wf = JSON.parse(data);
    console.log(`[INFO] ワークフロー取得成功: '${wf.name}' (nodes=${wf.nodes.length})`);
    
    // バックアップを保存
    fs.writeFileSync('ht60IBCItF9vt1vO_backup_before_fix.json', JSON.stringify(wf, null, 2));
    
    // LINE通知ノードのエラー時継続設定を適用
    let foundLineNode = false;
    wf.nodes = wf.nodes.map(n => {
      if (n.name === "LINE通知") {
        foundLineNode = true;
        return {
          ...n,
          "onError": "continueRegular"
        };
      }
      return n;
    });
    if (foundLineNode) {
      console.log("[INFO] 'LINE通知' ノードに onError: 'continueRegular' を適用しました。");
    } else {
      console.log("[WARN] 'LINE通知' ノードが見つかりませんでした。");
    }

    // 2. 不要なノードを除去（置換対象のノードを削除）
    wf.nodes = wf.nodes.filter(n => 
      n.name !== "Drive成果物保存" && 
      n.name !== "Drive_メタデータ作成" && 
      n.name !== "Drive_コンテンツアップロード"
    );
    
    // 3. 新しいノード（メタデータ作成 + コンテンツアップロード）を定義
    const metaNode = {
      "id": "mkt-drive-meta-create",
      "name": "Drive_メタデータ作成",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4,
      "position": [3000, 300],
      "parameters": {
        "method": "POST",
        "url": "https://www.googleapis.com/drive/v3/files",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Authorization",
              "value": "=Bearer {{ $('Drive OAuth取得').first().json.access_token }}"
            },
            {
              "name": "Content-Type",
              "value": "application/json"
            }
          ]
        },
        "sendBody": true,
        "contentType": "raw",
        "rawContentType": "application/json",
        // 完璧な n8n Expression を構築する
        "body": "={{ JSON.stringify({ name: $('Drive保存準備（成果物整形）').first().json.filename, parents: ['" + driveFolderId + "'], mimeType: 'text/plain' }) }}",
        "options": {
          "response": {
            "response": {
              // エラーを握り潰さないように neverError: false にする！
              "neverError": false,
              "responseFormat": "json"
            }
          }
        }
      }
    };
    
    const uploadNode = {
      "id": "mkt-drive-content-upload",
      "name": "Drive_コンテンツアップロード",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4,
      "position": [3250, 300],
      "parameters": {
        "method": "PATCH",
        // url も正しい n8n Expression にする
        "url": "=https://www.googleapis.com/upload/drive/v3/files/{{ $('Drive_メタデータ作成').first().json.id }}?uploadType=media",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Authorization",
              "value": "=Bearer {{ $('Drive OAuth取得').first().json.access_token }}"
            },
            {
              "name": "Content-Type",
              "value": "text/plain; charset=UTF-8"
            }
          ]
        },
        "sendBody": true,
        "contentType": "raw",
        "rawContentType": "text/plain; charset=UTF-8",
        "body": "={{ $('Drive保存準備（成果物整形）').first().json.reportContent }}",
        "options": {
          "response": {
            "response": {
              // エラーを握り潰さないように neverError: false にする！
              "neverError": false,
              "responseFormat": "json"
            }
          }
        }
      }
    };
    
    wf.nodes.push(metaNode);
    wf.nodes.push(uploadNode);
    
    // 4. connections の書き換え
    // 旧接続をクリーンアップ
    delete wf.connections["Drive成果物保存"];
    
    // Drive OAuth取得 -> Drive_メタデータ作成
    if (wf.connections["Drive OAuth取得"] && wf.connections["Drive OAuth取得"].main) {
      wf.connections["Drive OAuth取得"].main = wf.connections["Drive OAuth取得"].main.map(connList => {
        return connList.map(conn => {
          if (conn.node === "Drive成果物保存" || conn.node === "Drive_メタデータ作成") {
            return {
              "node": "Drive_メタデータ作成",
              "type": "main",
              "index": 0
            };
          }
          return conn;
        });
      });
    }
    
    // Drive_メタデータ作成 -> Drive_コンテンツアップロード
    wf.connections["Drive_メタデータ作成"] = {
      "main": [
        [
          {
            "node": "Drive_コンテンツアップロード",
            "type": "main",
            "index": 0
          }
        ]
      ]
    };
    
    // Drive_コンテンツアップロード -> 📦成果物管理追記 (接続を追加！)
    wf.connections["Drive_コンテンツアップロード"] = {
      "main": [
        [
          {
            "node": "📦成果物管理追記",
            "type": "main",
            "index": 0
          }
        ]
      ]
    };
    
    // 5. ローカルに修正後のJSONを保存
    fs.writeFileSync('ht60IBCItF9vt1vO_fixed.json', JSON.stringify(wf, null, 2));
    console.log("[INFO] 修正後の定義を ht60IBCItF9vt1vO_fixed.json に書き出しました。");
    
    // 6. n8n API に PUT リクエストを送信して更新
    const payload = {
      name: wf.name,
      nodes: wf.nodes,
      connections: wf.connections,
      settings: wf.settings
    };
    
    const payloadString = JSON.stringify(payload);
    
    console.log("[INFO] n8n APIへの更新(PUT)を開始します...");
    const req = http.request({
      hostname: '162.43.78.67',
      port: 5678,
      path: `/api/v1/workflows/${wfId}`,
      method: 'PUT',
      headers: {
        'X-N8N-API-KEY': apiKey,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payloadString)
      }
    }, (resPut) => {
      let putData = '';
      resPut.on('data', d => putData += d);
      resPut.on('end', () => {
        console.log(`[INFO] HTTPステータス: ${resPut.statusCode}`);
        if (resPut.statusCode === 200) {
          console.log("[SUCCESS] ワークフローの更新に成功しました！");
          
          // アクティブ化
          console.log("[INFO] ワークフローをアクティブ化(POST /activate)します...");
          const actReq = http.request({
            hostname: '162.43.78.67',
            port: 5678,
            path: `/api/v1/workflows/${wfId}/activate`,
            method: 'POST',
            headers: {
              'X-N8N-API-KEY': apiKey
            }
          }, (actRes) => {
            let actData = '';
            actRes.on('data', d => actData += d);
            actRes.on('end', () => {
              console.log(`[INFO] アクティブ化ステータス: ${actRes.statusCode}`);
              console.log("[SUCCESS] ワークフローのアクティブ化が完了しました。");
            });
          });
          actReq.on('error', e => console.error("[ERROR] アクティブ化に失敗:", e));
          actReq.end();
        } else {
          console.error("[ERROR] ワークフローの更新に失敗しました。レスポンス:", putData);
        }
      });
    });
    
    req.on('error', e => console.error("[ERROR] リクエスト送信失敗:", e));
    req.write(payloadString);
    req.end();
  });
});

getReq.on('error', e => {
  console.error("[ERROR] ワークフロー取得に失敗:", e);
});
getReq.end();
