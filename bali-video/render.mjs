// Render scene.html frame-by-frame with Playwright and pipe to ffmpeg.
// Usage: node render.mjs            -> out/frames piped to video (silent)
//        node render.mjs --stills 1,5,7.5  -> PNG previews
import { createRequire } from 'module';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_PATH || '/opt/node22/lib/node_modules/playwright');

const FPS = 30, DUR = 15;
const dir = path.dirname(new URL(import.meta.url).pathname);
const out = path.join(dir, 'out');
fs.mkdirSync(out, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
await page.goto('file://' + path.join(dir, 'scene.html'));
// force all font subsets used anywhere in the video to load
await page.evaluate(async () => {
  for (let t = 0; t < 15; t += 0.1) { window.render(t); document.body.offsetHeight; await document.fonts.ready; }
});
await page.evaluate(() => document.fonts.ready);

const stillsArg = process.argv.indexOf('--stills');
if (stillsArg > 0) {
  for (const s of process.argv[stillsArg + 1].split(',')) {
    await page.evaluate(t => window.render(t), parseFloat(s));
    await page.screenshot({ path: path.join(out, `still_${s}.png`) });
  }
} else {
  const ff = spawn('ffmpeg', ['-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', path.join(out, 'silent.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = 0; f < FPS * DUR; f++) {
    await page.evaluate(t => window.render(t), f / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
}
await browser.close();
