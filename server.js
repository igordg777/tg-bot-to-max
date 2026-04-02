/**
 * MAXBoты landing server
 * - Serves static files (index.html, etc.)
 * - POST /api/lead — stores leads to leads.json + optional email notification
 *
 * Config via env vars:
 *   PORT          — HTTP port (default 3000)
 *   SMTP_HOST     — SMTP server (e.g. smtp.yandex.ru)
 *   SMTP_PORT     — SMTP port (default 465)
 *   SMTP_USER     — SMTP login
 *   SMTP_PASS     — SMTP password
 *   NOTIFY_EMAIL  — where to send lead notifications
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = process.env.PORT || 3000;
const LEADS_FILE = path.join(__dirname, 'leads.json');

// ─── Helpers ───────────────────────────────────────────────────────────────

function loadLeads() {
  if (!fs.existsSync(LEADS_FILE)) return [];
  try {
    return JSON.parse(fs.readFileSync(LEADS_FILE, 'utf8'));
  } catch {
    return [];
  }
}

function saveLead(lead) {
  const leads = loadLeads();
  leads.push(lead);
  fs.writeFileSync(LEADS_FILE, JSON.stringify(leads, null, 2), 'utf8');
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => { body += chunk.toString(); });
    req.on('end', () => {
      try { resolve(JSON.parse(body)); }
      catch { reject(new Error('Invalid JSON')); }
    });
    req.on('error', reject);
  });
}

function serveStatic(req, res) {
  const safePath = req.url === '/' ? '/index.html' : req.url.split('?')[0];
  const filePath = path.join(__dirname, safePath);
  const ext = path.extname(filePath);
  const mimeTypes = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
  };

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('404 Not Found');
      return;
    }
    res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'application/octet-stream' });
    res.end(data);
  });
}

async function sendEmailNotification(lead) {
  const { SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, NOTIFY_EMAIL } = process.env;
  if (!SMTP_HOST || !SMTP_USER || !SMTP_PASS || !NOTIFY_EMAIL) return;

  let nodemailer;
  try { nodemailer = require('nodemailer'); }
  catch { return; }

  const transporter = nodemailer.createTransport({
    host: SMTP_HOST,
    port: parseInt(SMTP_PORT || '465'),
    secure: parseInt(SMTP_PORT || '465') === 465,
    auth: { user: SMTP_USER, pass: SMTP_PASS },
  });

  await transporter.sendMail({
    from: `"MAXBoты Лендинг" <${SMTP_USER}>`,
    to: NOTIFY_EMAIL,
    subject: `Новая заявка от ${lead.name} (${lead.company})`,
    text: [
      `Имя: ${lead.name}`,
      `Компания: ${lead.company}`,
      `Телефон: ${lead.phone}`,
      `Тариф: ${lead.tariff || 'не выбран'}`,
      `Сообщение: ${lead.message || '—'}`,
      `Время: ${lead.submittedAt}`,
    ].join('\n'),
  });
}

// ─── Request handler ───────────────────────────────────────────────────────

const server = http.createServer(async (req, res) => {
  const parsedUrl = url.parse(req.url, true);

  if (req.method === 'POST' && parsedUrl.pathname === '/api/lead') {
    let body;
    try {
      body = await readBody(req);
    } catch {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Invalid request body' }));
      return;
    }

    const { name, company, phone } = body;
    if (!name || !company || !phone) {
      res.writeHead(422, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'name, company and phone are required' }));
      return;
    }

    const lead = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      name: String(name).trim().slice(0, 200),
      company: String(company).trim().slice(0, 200),
      phone: String(phone).trim().slice(0, 30),
      tariff: body.tariff ? String(body.tariff).trim().slice(0, 100) : '',
      message: body.message ? String(body.message).trim().slice(0, 2000) : '',
      submittedAt: new Date().toISOString(),
    };

    saveLead(lead);
    console.log(`[lead] ${lead.submittedAt} | ${lead.name} | ${lead.company} | ${lead.phone}`);

    sendEmailNotification(lead).catch(err => {
      console.error('[email] notification failed:', err.message);
    });

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ok: true, id: lead.id }));
    return;
  }

  serveStatic(req, res);
});

server.listen(PORT, () => {
  console.log(`MAXBoты landing running at http://localhost:${PORT}`);
  console.log(`Leads stored in: ${LEADS_FILE}`);
  if (!process.env.SMTP_HOST) {
    console.log('Tip: set SMTP_HOST / SMTP_USER / SMTP_PASS / NOTIFY_EMAIL for email notifications');
  }
});
