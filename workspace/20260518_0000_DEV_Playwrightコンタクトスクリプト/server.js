"use strict";

require("dotenv").config();

const express = require("express");
const helmet = require("helmet");
const rateLimit = require("express-rate-limit");
const { v4: uuidv4 } = require("uuid");
const Joi = require("joi");

const contactBot = require("./src/contactBot");
const logger = require("./src/logger");
const { appendToGoogleSheets } = require("./src/googleSheets");
const { saveLogEntry } = require("./src/logStore");

const app = express();
const PORT = process.env.PORT || 3001;
const API_SECRET = process.env.API_SECRET || "";

// ─── Middleware ────────────────────────────────────────────────────────────────
app.use(helmet());
app.use(express.json({ limit: "1mb" }));

// Rate limiting: 60 requests per minute
const limiter = rateLimit({
  windowMs: 60 * 1000,
  max: 60,
  standardHeaders: true,
  legacyHeaders: false,
  message: { success: false, error: "Rate limit exceeded. Try again later." },
});
app.use(limiter);

// Optional API key authentication
app.use((req, res, next) => {
  if (!API_SECRET) return next();
  const provided = req.headers["x-api-key"] || req.query.api_key;
  if (provided !== API_SECRET) {
    return res.status(401).json({ success: false, error: "Unauthorized" });
  }
  next();
});

// ─── Validation schema ─────────────────────────────────────────────────────────
const sendSchema = Joi.object({
  url: Joi.string().uri({ scheme: ["http", "https"] }).required(),
  company_name: Joi.string().max(200).required(),
  press_release_title: Joi.string().max(500).default(""),
  category: Joi.string()
    .valid("介護", "建設", "DX", "製造", "物流", "医療", "不動産", "その他")
    .default("その他"),
  dry_run: Joi.boolean().default(false),
});

const batchSchema = Joi.object({
  targets: Joi.array()
    .items(
      Joi.object({
        url: Joi.string().uri({ scheme: ["http", "https"] }).required(),
        company_name: Joi.string().max(200).required(),
        press_release_title: Joi.string().max(500).default(""),
        category: Joi.string()
          .valid("介護", "建設", "DX", "製造", "物流", "医療", "不動産", "その他")
          .default("その他"),
      })
    )
    .min(1)
    .max(50)
    .required(),
  dry_run: Joi.boolean().default(false),
  delay_ms: Joi.number().integer().min(1000).max(60000).default(5000),
});

// ─── Routes ────────────────────────────────────────────────────────────────────

/**
 * GET /health
 * ヘルスチェック
 */
app.get("/health", (_req, res) => {
  res.json({
    success: true,
    service: "contact-bot",
    version: "1.0.0",
    timestamp: new Date().toISOString(),
  });
});

/**
 * POST /send
 * 1件の問い合わせフォーム送信
 */
app.post("/send", async (req, res) => {
  const jobId = uuidv4();
  logger.info(`[${jobId}] POST /send received`, { body: req.body });

  // Validate input
  const { error, value } = sendSchema.validate(req.body);
  if (error) {
    logger.warn(`[${jobId}] Validation error: ${error.message}`);
    return res.status(400).json({
      success: false,
      job_id: jobId,
      error: error.details.map((d) => d.message).join(", "),
    });
  }

  const { url, company_name, press_release_title, category, dry_run } = value;

  try {
    const result = await contactBot.sendContactForm({
      jobId,
      url,
      companyName: company_name,
      pressReleaseTitle: press_release_title,
      category,
      dryRun: dry_run,
    });

    // Save log entry
    await saveLogEntry(result);

    // Append to Google Sheets (non-blocking on error)
    appendToGoogleSheets(result).catch((err) => {
      logger.error(`[${jobId}] Google Sheets append failed: ${err.message}`);
    });

    const httpStatus = result.status === "success" ? 200 : 422;
    return res.status(httpStatus).json({
      success: result.status === "success",
      job_id: jobId,
      result,
    });
  } catch (err) {
    logger.error(`[${jobId}] Unexpected error: ${err.message}`, {
      stack: err.stack,
    });
    return res.status(500).json({
      success: false,
      job_id: jobId,
      error: "Internal server error",
    });
  }
});

/**
 * POST /send-batch
 * 複数の問い合わせフォームを順番に送信
 */
app.post("/send-batch", async (req, res) => {
  const batchId = uuidv4();
  logger.info(`[${batchId}] POST /send-batch received`, {
    count: req.body?.targets?.length,
  });

  const { error, value } = batchSchema.validate(req.body);
  if (error) {
    return res.status(400).json({
      success: false,
      batch_id: batchId,
      error: error.details.map((d) => d.message).join(", "),
    });
  }

  const { targets, dry_run, delay_ms } = value;

  // Respond immediately with batch ID (async processing)
  res.json({
    success: true,
    batch_id: batchId,
    message: `Processing ${targets.length} targets asynchronously`,
    targets_count: targets.length,
  });

  // Process in background
  (async () => {
    const results = [];
    for (let i = 0; i < targets.length; i++) {
      const target = targets[i];
      const jobId = `${batchId}-${i + 1}`;
      logger.info(
        `[${batchId}] Processing target ${i + 1}/${targets.length}: ${target.url}`
      );

      try {
        const result = await contactBot.sendContactForm({
          jobId,
          url: target.url,
          companyName: target.company_name,
          pressReleaseTitle: target.press_release_title || "",
          category: target.category || "その他",
          dryRun: dry_run,
        });

        results.push(result);
        await saveLogEntry(result);
        appendToGoogleSheets(result).catch((err) => {
          logger.error(`[${jobId}] Google Sheets error: ${err.message}`);
        });
      } catch (err) {
        logger.error(`[${jobId}] Error processing target: ${err.message}`);
        const failResult = {
          job_id: jobId,
          url: target.url,
          company_name: target.company_name,
          category: target.category,
          status: "error",
          timestamp: new Date().toISOString(),
          message_sent: null,
          error_detail: err.message,
        };
        results.push(failResult);
        await saveLogEntry(failResult);
      }

      // Delay between submissions (except last)
      if (i < targets.length - 1) {
        await sleep(delay_ms);
      }
    }

    const summary = {
      batch_id: batchId,
      total: results.length,
      success: results.filter((r) => r.status === "success").length,
      skipped: results.filter((r) => r.status === "skipped").length,
      failed: results.filter((r) => r.status === "failed" || r.status === "error")
        .length,
      completed_at: new Date().toISOString(),
    };
    logger.info(`[${batchId}] Batch completed`, summary);

    // Save batch summary
    await saveLogEntry({ type: "batch_summary", ...summary, results });
  })();
});

/**
 * GET /logs
 * 送信ログ取得（直近100件）
 */
app.get("/logs", async (req, res) => {
  try {
    const { getRecentLogs } = require("./src/logStore");
    const limit = Math.min(parseInt(req.query.limit) || 100, 500);
    const logs = await getRecentLogs(limit);
    res.json({ success: true, count: logs.length, logs });
  } catch (err) {
    logger.error(`GET /logs error: ${err.message}`);
    res.status(500).json({ success: false, error: "Failed to retrieve logs" });
  }
});

// ─── 404 handler ───────────────────────────────────────────────────────────────
app.use((_req, res) => {
  res.status(404).json({ success: false, error: "Endpoint not found" });
});

// ─── Error handler ─────────────────────────────────────────────────────────────
app.use((err, _req, res, _next) => {
  logger.error(`Unhandled error: ${err.message}`);
  res.status(500).json({ success: false, error: "Internal server error" });
});

// ─── Start server ──────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  logger.info(`Contact Bot API server running on port ${PORT}`);
});

// ─── Utility ───────────────────────────────────────────────────────────────────
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

module.exports = app;