// Draws each pack's covers from the "cover" section of its pack.yaml: cover.jpg (square, for the
// catalogue) and book-cover.jpg (portrait 0.72, the book cover inside the app).
// Needs Node and Playwright with Chromium: `node tools/render_covers.mjs`.
import { readdirSync, readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const packsDir = join(root, 'packs');

/** The few "cover:" fields used here, read without a YAML library. */
function readCover(yamlText) {
  const block = yamlText.split('\ncover:\n')[1]?.split(/\n\S/)[0] ?? '';
  const field = name => block.match(new RegExp(`^\\s+${name}:\\s*(.+)$`, 'm'))?.[1].trim().replace(/^"(.*)"$/, '$1');
  const colors = JSON.parse(field('colors') ?? '["#1f6f43", "#7cb342"]');
  return { emoji: field('emoji'), title: field('title'), colors };
}

function html({ emoji, title, colors }, width, height) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>
    html, body { margin: 0; }
    body {
      width: ${width}px; height: ${height}px; overflow: hidden;
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      background: radial-gradient(circle at 30% 20%, ${colors[1]} 0%, ${colors[0]} 70%);
      font-family: "DejaVu Sans", "Noto Sans", sans-serif; color: #fff; text-align: center;
    }
    .emoji { font-size: ${Math.round(width * 0.36)}px; line-height: 1; filter: drop-shadow(0 12px 18px rgba(0,0,0,.25)); }
    h1 { margin: ${Math.round(width * 0.05)}px 24px 0; font-size: ${Math.round(width * 0.085)}px; font-weight: 800; letter-spacing: -0.5px; }
    .brand { position: absolute; bottom: ${Math.round(height * 0.05)}px; font-size: ${Math.round(width * 0.04)}px; opacity: .8; font-weight: 700; letter-spacing: 3px; }
  </style></head><body>
    <div class="emoji">${emoji}</div><h1>${title}</h1><div class="brand">MIGA</div>
  </body></html>`;
}

const browser = await chromium.launch();
const page = await browser.newPage();
for (const id of readdirSync(packsDir)) {
  const yamlPath = join(packsDir, id, 'pack.yaml');
  if (!existsSync(yamlPath)) continue;
  const cover = readCover(readFileSync(yamlPath, 'utf8'));
  for (const [file, width, height] of [['cover.jpg', 720, 720], ['book-cover.jpg', 720, 1000]]) {
    await page.setViewportSize({ width, height });
    await page.setContent(html(cover, width, height));
    await page.screenshot({ path: join(packsDir, id, file), type: 'jpeg', quality: 88 });
    console.log(`${id}/${file}`);
  }
}
await browser.close();
