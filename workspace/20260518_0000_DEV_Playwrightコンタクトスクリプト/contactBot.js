"use strict";

const { chromium } = require("playwright");
const { v4: uuidv4 } = require("uuid");
const logger = require("./logger");
const { generateMessageBody } = require("./messageGenerator");
const { detectCaptcha } = require("./captchaDetector");
const { findFormFields } = require("./formDetector");

const TIMEOUT_MS = parseInt(process.env.TIMEOUT_MS) || 30000;
const HEADLESS = process.env.HEADLESS !== "false";

// 送信者情報（固定）
const SENDER = {
  companyName: "ノーススター経営サポート",
  contactPerson: "赤瀬文成",
  email: "bestthink01109@gmail.com",
  phone: "090-XXXX-XXXX", // 必要に応じて変更
  subject: "AI業務自動化についてのご提案",
};

/**
 * 問い合わせフォームへの自動送信
 * @param {Object} params
 * @param {string} params.jobId
 * @param {string} params.url
 * @param {string} params.companyName
 * @param {string} params.pressReleaseTitle
 * @param {string} params.category
 * @param {boolean} params.dryRun
 * @returns {Promise<Object>} 送信結果
 */
async function sendContactForm({
  jobId,
  url,
  companyName,
  pressReleaseTitle,
  category,
  dryRun = false,
}) {
  const startedAt = new Date().toISOString();
  let browser = null;

  const baseResult = {
    job_id: jobId || uuidv4(),
    url,
    company_name: companyName,
    press_release_title: pressReleaseTitle,
    category,
    dry_run: dryRun,
    timestamp: startedAt,
    message_sent: null,
    status: null,
    error_detail: null,
    screenshot_path: null,
    duration_ms: null,
  };

  const t0 = Date.now();

  try {
    logger.info(`[${baseResult.job_id}] Starting form submission for: ${url}`);

    // メッセージ本文生成
    const messageBody = generateMessageBody({
      category,
      companyName,
      pressReleaseTitle,
    });

    baseResult.message_sent = messageBody;

    if (dryRun) {
      logger.info(`[${baseResult.job_id}] DRY RUN - skipping actual submission`);
      return {
        ...baseResult,
        status: "dry_run",
        duration_ms: Date.now() - t0,
        message_sent: messageBody,
      };
    }

    // ブラウザ起動
    browser = await chromium.launch({
      headless: HEADLESS,
      args: [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-accelerated-2d-canvas",
        "--no-first-run",
        "--no-zygote",
        "--disable-gpu",
      ],
    });

    const context = await browser.newContext({
      userAgent:
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
      viewport: { width: 1280, height: 800 },
      locale: "ja-JP",
      timezoneId: "Asia/Tokyo",
    });

    const page = await context.newPage();

    // グローバルタイムアウト設定
    page.setDefaultTimeout(TIMEOUT_MS);
    page.setDefaultNavigationTimeout(TIMEOUT_MS);

    // ページアクセス
    logger.info(`[${baseResult.job_id}] Navigating to: ${url}`);
    let navigationOk = false;
    try {
      const response = await page.goto(url, {
        waitUntil: "domcontentloaded",
        timeout: TIMEOUT_MS,
      });
      if (response && response.status() >= 400) {
        throw new Error(`HTTP ${response.status()} for URL: ${url}`);
      }
      navigationOk = true;
    } catch (navErr) {
      logger.warn(`[${baseResult.job_id}] Navigation error: ${navErr.message}`);
      return {
        ...baseResult,
        status: "skipped",
        error_detail: `Navigation failed: ${navErr.message}`,
        duration_ms: Date.now() - t0,
      };
    }

    // CAPTCHA検出
    const hasCaptcha = await detectCaptcha(page);
    if (hasCaptcha) {
      logger.warn(`[${baseResult.job_id}] CAPTCHA detected. Skipping.`);
      const screenshotPath = await takeScreenshot(
        page,
        baseResult.job_id,
        "captcha"
      );
      return {
        ...baseResult,
        status: "skipped",
        error_detail: "CAPTCHA detected",
        screenshot_path: screenshotPath,
        duration_ms: Date.now() - t0,
      };
    }

    // フォームフィールド検出
    logger.info(`[${baseResult.job_id}] Detecting form fields...`);
    const formFields = await findFormFields(page);

    if (!formFields.formFound) {
      logger.warn(
        `[${baseResult.job_id}] No contact form found. Skipping.`
      );
      const screenshotPath = await takeScreenshot(
        page,
        baseResult.job_id,
        "no_form"
      );
      return {
        ...baseResult,
        status: "skipped",
        error_detail: "No contact form found",
        screenshot_path: screenshotPath,
        duration_ms: Date.now() - t0,
      };
    }

    logger.info(
      `[${baseResult.job_id}] Form detected. Fields: ${JSON.stringify(
        Object.keys(formFields).filter(
          (k) => k !== "formFound" && formFields[k]
        )
      )}`
    );

    // フォーム入力
    await fillFormFields(page, formFields, {
      companyName: SENDER.companyName,
      contactPerson: SENDER.contactPerson,
      email: SENDER.email,
      phone: SENDER.phone,
      subject: SENDER.subject,
      body: messageBody,
    });

    // CAPTCHA再チェック（入力後）
    const hasCaptchaAfterFill = await detectCaptcha(page);
    if (hasCaptchaAfterFill) {
      logger.warn(
        `[${baseResult.job_id}] CAPTCHA appeared after filling. Skipping.`
      );
      const screenshotPath = await takeScreenshot(
        page,
        baseResult.job_id,
        "captcha_after_fill"
      );
      return {
        ...baseResult,
        status: "skipped",
        error_detail: "CAPTCHA appeared after filling form",
        screenshot_path: screenshotPath,
        duration_ms: Date.now() - t0,
      };
    }

    // 送信前スクリーンショット
    const screenshotBeforePath = await takeScreenshot(
      page,
      baseResult.job_id,
      "before_submit"
    );

    // 送信ボタンクリック
    logger.info(`[${baseResult.job_id}] Clicking submit button...`);
    const submitResult = await clickSubmitButton(page, formFields);

    if (!submitResult.clicked) {
      logger.warn(
        `[${baseResult.job_id}] Submit button not found or not clickable.`
      );
      return {
        ...baseResult,
        status: "failed",
        error_detail: "Submit button not found or not clickable",
        screenshot_path: screenshotBeforePath,
        duration_ms: Date.now() - t0,
      };
    }

    // 送信後の確認待ち
    await waitForSubmissionConfirmation(page);

    // 送信後スクリーンショット
    const screenshotAfterPath = await takeScreenshot(
      page,
      baseResult.job_id,
      "after_submit"
    );

    // 成功確認
    const successConfirmed = await checkSubmissionSuccess(page);

    logger.info(
      `[${baseResult.job_id}] Submission ${
        successConfirmed ? "SUCCESS" : "UNCERTAIN"
      } for ${url}`
    );

    return {
      ...baseResult,
      status: successConfirmed ? "success" : "uncertain",
      screenshot_path: screenshotAfterPath,
      duration_ms: Date.now() - t0,
    };
  } catch (err) {
    logger.error(
      `[${baseResult.job_id}] Unexpected error: ${err.message}`,
      { stack: err.stack }
    );

    // タイムアウトエラー判定
    const isTimeout =
      err.message.includes("Timeout") || err.message.includes("timeout");

    return {
      ...baseResult,
      status: isTimeout ? "skipped" : "failed",
      error_detail: isTimeout ? `Timeout: ${err.message}` : err.message,
      duration_ms: Date.now() - t0,
    };
  } finally {
    if (browser) {
      await browser.close().catch((e) => {
        logger.warn(`Browser close error: ${e.message}`);
      });
    }
  }
}

/**
 * フォームフィールドへの入力
 */
async function fillFormFields(page, formFields, senderInfo) {
  const { companyName, contactPerson, email, phone, subject, body } =
    senderInfo;

  // ヘルパー: セレクタが存在すれば入力
  async function fillIfExists(selector, value) {
    if (!selector || !value) return false;
    try {
      const el = page.locator(selector).first();
      const count = await el.count();
      if (count === 0) return false;
      await el.scrollIntoViewIfNeeded({ timeout: 5000 });
      await el.fill(String(value), { timeout: 5000 });
      return true;
    } catch (err) {
      logger.warn(`Fill error for [${selector}]: ${err.message}`);
      return false;
    }
  }

  // 会社名
  if (formFields.companyField) {
    await fillIfExists(formFields.companyField, companyName);
  }

  // 担当者名
  if (formFields.nameField) {
    await fillIfExists(formFields.nameField, contactPerson);
  }

  // 名前を姓名で分割する場合
  if (formFields.lastNameField) {
    await fillIfExists(formFields.lastNameField, "赤瀬");
  }
  if (formFields.firstNameField) {
    await fillIfExists(formFields.firstNameField, "文成");
  }

  // フリガナ対応
  if (formFields.lastNameKanaField) {
    await fillIfExists(formFields.lastNameKanaField, "アカセ");
  }
  if (formFields.firstNameKanaField) {
    await fillIfExists(formFields.firstNameKanaField, "フミナリ");
  }
  if (formFields.nameKanaField) {
    await fillIfExists(formFields.nameKanaField, "アカセフミナリ");
  }

  // メール
  if (formFields.emailField) {
    await fillIfExists(formFields.emailField, email);
  }
  if (formFields.emailConfirmField) {
    await fillIfExists(formFields.emailConfirmField, email);
  }

  // 電話
  if (formFields.phoneField) {
    await fillIfExists(formFields.phoneField, phone);
  }

  // 件名
  if (formFields.subjectField) {
    await fillIfExists(formFields.subjectField, subject);
  }

  // 本文
  if (formFields.bodyField) {
    await fillIfExists(formFields.bodyField, body);
  }

  // セレクト（お問い合わせ種別など）- 「その他」or最初の選択肢
  if (formFields.categorySelectField) {
    try {
      const selectEl = page.locator(formFields.categorySelectField).first();
      const count = await selectEl.count();
      if (count > 0) {
        // 「その他」「お問い合わせ」などを優先選択
        const options = await selectEl.locator("option").allTextContents();
        const preferredLabels = [
          "その他",
          "お問い合わせ",
          "ご相談",
          "その他のお問い合わせ",
          "一般",
        ];
        let selectedValue = null;
        for (const label of preferredLabels) {
          const found = options.find((o) =>
            o.trim().includes(label)
          );
          if (found) {
            selectedValue = found.trim();
            break;
          }
        }
        if (!selectedValue && options.length > 1) {
          selectedValue = options[1].trim(); // 先頭はプレースホルダーが多いので2番目
        }
        if (selectedValue) {
          await selectEl.selectOption({ label: selectedValue });
        }
      }
    } catch (err) {
      logger.warn(`Select field error: ${err.message}`);
    }
  }

  // チェックボックス（プライバシーポリシー同意）
  if (formFields.privacyCheckbox) {
    try {
      const checkbox = page.locator(formFields.privacyCheckbox).first();
      const count = await checkbox.count();
      if (count > 0) {
        const isChecked = await checkbox.isChecked();
        if (!isChecked) {
          await checkbox.check({ timeout: 5000 });
        }
      }
    } catch (err) {
      logger.warn(`Privacy checkbox error: ${err.message}`);
    }
  }

  logger.info("Form fields filled successfully");
}

/**
 * 送信ボタンのクリック
 */
async function clickSubmitButton(page, formFields) {
  const submitSelectors = formFields.submitButton
    ? [formFields.submitButton]
    : [];

  // フォールバックセレクタ
  submitSelectors.push(
    'button[type="submit"]',
    'input[type="submit"]',
    'button:has-text("送信")',
    'button:has-text("確認")',
    'button:has-text("次へ")',
    'button:has-text("Send")',
    'button:has-text("Submit")',
    'input[value="送信"]',
    'input[value="確認する"]',
    'input[value="送信する"]',
    'input[value="Submit"]',
    ".submit-btn",
    ".send-btn",
    "#submit",
    "#send",
    'a:has-text("送信する")'
  );

  for (const selector of submitSelectors) {
    try {
      const btn = page.locator(selector).first();
      const count = await btn.count();
      if (count === 0) continue;

      const isVisible = await btn.isVisible({ timeout: 3000 });
      if (!isVisible) continue;

      const isDisabled = await btn.isDisabled();
      if (isDisabled) continue;

      await btn.scrollIntoViewIfNeeded({ timeout: 5000 });
      await btn.click({ timeout: 10000 });
      logger.info(`Submit button clicked with selector: ${selector}`);
      return { clicked: true, selector };
    } catch (err) {
      logger.warn(`Submit button [${selector}] click failed: ${err.message}`);
    }
  }

  return { clicked: false, selector: null };
}

/**
 * 送信後の確認待ち
 */
async function waitForSubmissionConfirmation(page) {
  try {
    await Promise.race([
      page.waitForNavigation({ timeout: 15000, waitUntil: "domcontentloaded" }),
      page.waitForSelector(
        [
          ':has-text("ありがとう")',
          ':has-text("送信しました")',
          ':has-text("完了")',
          ':has-text("受け付けました")',
          ':has-text("Thank you")',
          ':has-text("success")',
          ".complete",
          ".thanks",
          "#complete",
          "#thanks",
        ].join(", "),
        { timeout: 15000 }
      ),
      sleep(5000), // 5秒待機をフォールバック
    ]);
  } catch (_) {
    // タイムアウトしても続行
    await sleep(3000);
  }
}

/**
 * 送信成功の確認
 */
async function checkSubmissionSuccess(page) {
  const successKeywords = [
    "ありがとう",
    "送信しました",
    "完了",
    "受け付けました",
    "お問い合わせ",
    "送信が完了",
    "Thank you",
    "success",
    "successfully",
    "submitted",
    "confirmation",
    "確認",
  ];

  try {
    const bodyText = await page.evaluate(
      () => document.body.innerText || document.body.textContent || ""
    );
    const lowerBody = bodyText.toLowerCase();

    return successKeywords.some((kw) =>
      lowerBody.includes(kw.toLowerCase())
    );
  } catch (_) {
    return false;
  }
}

/**
 * スクリーンショット取得
 */
async function takeScreenshot(page, jobId, stage) {
  const fs = require("fs");
  const path = require("path");

  const screenshotDir = path.join(
    process.env.LOG_DIR || "./logs",
    "screenshots"
  );

  try {
    fs.mkdirSync(screenshotDir, { recursive: true });
    const filename = `${jobId}_${stage}_${Date.now()}.png`;
    const filepath = path.join(screenshotDir, filename);
    await page.screenshot({ path: filepath, fullPage: true, timeout: 10000 });
    logger.info(`Screenshot saved: ${filepath}`);
    return filepath;
  } catch (err) {
    logger.warn(`Screenshot failed: ${err.message}`);
    return null;
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

module.exports = { sendContactForm };