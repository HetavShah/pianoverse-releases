// Every picture and clip on pianoverse.in, straight from the app's renderer (needs the app's vite preview on :4173).
//   node render.mjs <work dir> drawn   the effects: a MIDI file on the drawn keyboard (no video), stills and loops
//   node render.mjs <work dir> video   the app's own screens, editing a real take (website/source: a landscape video and
//                                      its project, the notes found in its sound), its loops and stills
// A loop's frames go to <work>/<name>/00000.jpg…; a still to <work>/<name>.jpg; a screen to <work>/ui-<name>.png.
// ONLY=name,name renders just those.
import { createRequire } from 'module';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
const APP = process.env.PIANOVERSE_APP ?? new URL('../../../pianoverse', import.meta.url).pathname;
const { chromium } = createRequire(APP + '/package.json')('playwright');
const SITE = new URL('../..', import.meta.url).pathname;
const [WORK0, JOB] = process.argv.slice(2);
const WORK = resolve(WORK0); mkdirSync(WORK, { recursive: true });
const ONLY = process.env.ONLY ? process.env.ONLY.split(',') : null;
const want = (name) => !ONLY || ONLY.includes(name);

const FPS = 24;
/** the loops: the busy stretch of the piece, plus a second to cross-fade the end into the start */
const FROM = 30, SECS = 8, FADE = 1;
/** the take's loops: the busiest stretch of the 12 s clip; the looks the hero's cursor picks */
const TAKE_FROM = 2, TAKE_SECS = 8;
const TAKE_LOOKS = [['gold', 'Gold Leaf'], ['ocean', 'Ocean Gem'], ['synth', 'Synthwave']];

const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome', args: ['--enable-unsafe-webgpu', '--use-webgpu-adapter=swiftshader', '--enable-features=Vulkan', '--use-vulkan=swiftshader', '--disable-vulkan-surface', '--autoplay-policy=no-user-gesture-required'] });
const page = await b.newPage({ viewport: { width: 1440, height: 900 } });
page.on('pageerror', (e) => console.log('[pageerror]', e.message));
page.on('dialog', (d) => d.accept());
// the silent clock video the desktop app makes with FFmpeg for a project without a video
mkdirSync(`${WORK}/clock`, { recursive: true });
await page.route('**/clock-*.mp4', (r) => {
  const s = Number(/clock-(\d+)/.exec(r.request().url())[1]);
  const f = `${WORK}/clock/clock-${s}.mp4`;
  if (!existsSync(f)) execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=64x36:r=60', '-t', String(s), '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', '-g', '60', '-movflags', '+faststart', f]);
  return r.fulfill({ path: f, contentType: 'video/mp4' });
});
await page.route('**/piano-site.pvpiano', (r) => r.fulfill({ path: `${SITE}/assets/piano/salamander-v1.pvpiano`, contentType: 'application/octet-stream' }));
await page.addInitScript(() => { window.__pvHeadless = true; localStorage.clear(); window.__pvClockVideo = (s) => `/clock-${s}.mp4`; window.__pvPianoUrl = '/piano-site.pvpiano'; });
process.chdir(APP);
await page.goto('http://localhost:4173/'); await page.waitForTimeout(800);

const setProject = (patch) => page.evaluate((patch) => { const p = window.pianoverseProject; window.pianoverseSetProject({ ...p, ...patch, look: { ...p.look, ...patch.look }, stage: p.stage && { ...p.stage, ...patch.stage } }); }, patch);
const pickLook = async (name) => {
  await page.evaluate(() => window.pianoverseGoStep('style')); await page.waitForTimeout(800);
  await page.keyboard.press('0'); await page.waitForTimeout(400);
  await page.click(`.look-card:has(.name:text-is("${name}"))`); await page.waitForTimeout(900);
};
/** one frame from the renderer: out = [w, h]; view = a part of the picture, in its pixels; alpha: the effects alone, on
 *  a transparent background (the export's effects pass), as a PNG */
const frame = (t, out, view, alpha = false) => page.evaluate(async ([t, out, view, alpha]) => {
  const r = window.pianoverse.renderer, p = window.pianoverseProject;
  let f;
  if (p.stage) f = window.pianoverseFrameAt(t);
  else {
    // the video: on the frame wanted, copied to a canvas (reading the element itself loses the software GPU)
    const v = document.querySelector('video');
    if (Math.abs(v.currentTime - t) > 1e-3) { v.currentTime = t; await new Promise((res) => v.addEventListener('seeked', res, { once: true })); }
    f = document.createElement('canvas'); f.width = v.videoWidth; f.height = v.videoHeight; f.getContext('2d').drawImage(v, 0, 0);
  }
  r.setProject(p); r.setOutput(out); r.setScale(1); r.setView(view ? { x: view[0], y: view[1], w: view[2], h: view[3] } : null);
  await r.texturesReady();
  r.alphaOut = alpha;
  const img = await r.capture(f, t);
  r.alphaOut = false;
  r.setOutput(null); r.setScale(0.5); r.setView(null);
  const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
  c.getContext('2d').putImageData(new ImageData(new Uint8ClampedArray(img.data), img.width, img.height), 0, 0);
  return alpha ? c.toDataURL('image/png') : c.toDataURL('image/jpeg', 0.93);
}, [t, out, view ?? null, alpha]);
const write = (path, url) => writeFileSync(path, Buffer.from(url.split(',')[1], 'base64'));
const still = async (name, t, out, view) => { if (!want(name) || (!ONLY && existsSync(`${WORK}/${name}.jpg`))) return; write(`${WORK}/${name}.jpg`, await frame(t, out, view)); console.log('still', name); };
const loop = async (name, out, view, secs = SECS, from = FROM) => {
  if (!want(name)) return;
  mkdirSync(`${WORK}/${name}`, { recursive: true });
  const n = Math.round((secs + FADE) * FPS);
  // a run that stopped part way carries on where it was
  const done = readdirSync(`${WORK}/${name}`).length;
  for (let i = Math.max(0, done - 1); i < n; i++) {
    write(`${WORK}/${name}/${String(i).padStart(5, '0')}.jpg`, await frame(from + i / FPS, out, view));
    if (i % 48 === 0) console.log('loop', name, i, '/', n);
  }
};
/** the app's screen as it is, the preview filled in (headless runs don't draw it) */
const screen = async (name) => {
  if (!want('ui-' + name)) return;
  const cv = await page.$('canvas.preview-canvas');
  if (cv) {
    const size = await page.evaluate(() => { const c = document.querySelector('canvas.preview-canvas'); return [c.width * 2, c.height * 2]; });
    const url = await frame(await page.evaluate(() => window.pianoverseClock().t), size);
    await page.evaluate(async (url) => {
      document.querySelectorAll('.pv-shot').forEach((e) => e.remove());
      const cv = document.querySelector('canvas.preview-canvas'), el = document.createElement('img');
      el.src = url; el.className = 'pv-shot';
      Object.assign(el.style, { position: 'absolute', inset: '0', width: '100%', height: '100%', zIndex: 2, pointerEvents: 'none' });
      cv.parentElement.appendChild(el); await el.decode();
    }, url);
  }
  await page.waitForTimeout(300);
  await page.screenshot({ path: `${WORK}/ui-${name}.png` }); console.log('screen', name);
};

if (JOB === 'drawn') {
  // a MIDI file, no video: the keyboard drawn, the keys the piece uses
  await page.click('text=New project'); await page.waitForTimeout(600);
  await page.locator('.file-card', { hasText: 'No video?' }).locator('input[type=file]').first().setInputFiles('test/fixtures/interstellar-shifted.mid');
  await page.waitForFunction(() => window.pianoverseProject?.stage && window.pianoverseProject.notes.length > 0, null, { timeout: 30000 });
  await page.waitForFunction(() => { const v = document.querySelector('video'); return v && v.readyState >= 2 && v.duration > 10; }, null, { timeout: 30000 });
  await setProject({ stage: { range: 'piece' } }); await page.waitForTimeout(1500);
  const T = FROM + 3.75;
  const LOOKS = [['gold', 'Gold Leaf'], ['lagoon', 'Lagoon'], ['ember', 'Ember'], ['neon', 'Neon Night'], ['aurora', 'Aurora'], ['swan', 'Swan']];
  // the looks gallery
  for (const [id, name] of LOOKS) {
    await pickLook(name);
    await still(`look-${id}`, T, [1280, 720]);
  }
  await pickLook('Gold Leaf');
  const base = await page.evaluate(() => window.pianoverseProject.look);
  const reset = () => page.evaluate((l) => { const p = window.pianoverseProject; window.pianoverseSetProject({ ...p, look: l }); }, base);
  // the saber, close: the left half of the keys
  await loop('saber', [960, 540], [120, 500, 1040, 585], 6);
  for (const [id, patch] of [['flame', { saberStyle: 'flame' }], ['electric', { saberStyle: 'electric' }]]) {
    await setProject({ look: patch }); await page.waitForTimeout(600);
    await still(`saber-${id}`, T, [960, 540], [120, 500, 1040, 585]);
  }
  await reset();
  // notes and particles in Lagoon: untextured notes, so the shapes read
  await pickLook('Lagoon');
  const lagoon = await page.evaluate(() => window.pianoverseProject.look);
  for (const [id, patch] of [['glass', { noteDim: '3d', note3d: 'glass' }], ['gem', { noteDim: '3d', note3d: 'gem' }], ['hollow', { noteDim: '2d', note2d: 'hollow' }], ['soft', { noteDim: '2d', note2d: 'soft' }]]) {
    await setProject({ look: patch }); await page.waitForTimeout(600);
    await still(`notes-${id}`, T, [960, 540], [520, 60, 840, 472]);
  }
  await page.evaluate((l) => { const p = window.pianoverseProject; window.pianoverseSetProject({ ...p, look: l }); }, lagoon);
  for (const [id, patch] of [['fountain', { partMode: 'fountain' }], ['vortex', { partMode: 'vortex' }], ['explode', { partMode: 'plume', partAmount: 1.6, partSpeed: 2.6, partSwirl: 0.4, partLife: 0.7, partSpread: 0.4, partGravity: 0.35 }], ['streaks', { partMode: 'plume', partAmount: 0.9, partSpeed: 1.6, partSwirl: 0.6, partLife: 1.1, partRays: true, partRayLen: 2.2, partRise: 1.2 }]]) {
    await setProject({ look: patch }); await page.waitForTimeout(600);
    await loop(`part-${id}`, [640, 360], [300, 500, 1040, 585], 4);
  }
  await pickLook('Gold Leaf');
  // the opening title and the end card
  if (want('title-open') || want('title-end')) {
    await page.evaluate(() => window.pianoverseGoStep('titles')); await page.waitForTimeout(1200);
    await page.locator('.toggle-row', { hasText: 'Show an opening title' }).locator('input').check(); await page.waitForTimeout(800);
    await page.fill('.title-line input[type=text] >> nth=0', 'Interstellar'); await page.waitForTimeout(500);
    await page.locator('.card-opt', { hasText: 'Particles' }).first().click().catch(() => {}); await page.waitForTimeout(600);
    const intro = await page.evaluate(() => window.pianoverseClock().loop?.range ?? [-2.5, 0]);
    await still('title-open', intro[0] + (intro[1] - intro[0]) * 0.62, [1280, 720]);
    await page.click('.titles-tabs >> text=End card'); await page.waitForTimeout(300);
    await page.locator('.toggle-row', { hasText: 'Show an end card' }).locator('input').check(); await page.waitForTimeout(900);
    const outro = await page.evaluate(() => window.pianoverseClock().loop?.range ?? null);
    if (outro) await still('title-end', outro[0] + (outro[1] - outro[0]) * 0.7, [1280, 720]);
  }
}

if (JOB === 'video') {
  // a real take: a landscape video, its project (the keyboard marked, the notes found in its sound)
  const SRC = process.env.TAKE ?? `${SITE}website/source`;
  await page.setInputFiles('.row-actions input[type=file]', `${SRC}/take.pvproj.json`); await page.waitForTimeout(800);
  await page.setInputFiles('.file-card .actions input[type=file]', `${SRC}/take.mp4`); await page.waitForTimeout(4000);
  const T = 7;
  const at = async (t) => { await page.evaluate((t) => window.pianoverseSeek(t), t); await page.waitForTimeout(900); };
  const go = async (s, wait = 2000) => { await page.evaluate((s) => window.pianoverseGoStep(s), s); await page.waitForTimeout(wait); };
  await go('import', 1200); await screen('import');
  await go('notes', 2500); await at(T); await screen('sync');
  // the hero: the editor in three looks, where its preview and the look cards are, and the preview as loops
  const rects = {};
  for (const [id, name] of TAKE_LOOKS) {
    await pickLook(name); await at(T); await screen('looks-' + id);
    Object.assign(rects, await page.evaluate(() => {
      const r = (e) => { const b = e.getBoundingClientRect(); return [b.x, b.y, b.width, b.height].map((v) => Math.round(v)); };
      const o = { preview: r(document.querySelector('canvas.preview-canvas')) };
      document.querySelectorAll('.look-card').forEach((c) => { o['card:' + c.querySelector('.name').textContent.trim()] = r(c); });
      return o;
    }));
  }
  writeFileSync(`${WORK}/ui-rects.json`, JSON.stringify(rects, null, 1));
  // one screen per panel of the Picture tab, in Gold Leaf
  await pickLook('Gold Leaf');
  for (const [k, n] of [['2', 'notes'], ['3', 'saber'], ['5', 'particles'], ['6', 'lighting']]) {
    await page.keyboard.press(k); await page.waitForTimeout(700); await at(T); await screen('p-' + n);
  }
  await go('camera');
  await page.locator('button', { hasText: 'Auto camera' }).first().click().catch(() => {}); await page.waitForTimeout(2500);
  await at(T); await screen('camera');
  // the sound: the grand piano mixed in, in a hall, swelling in and ringing out
  await page.evaluate(() => { const p = window.pianoverseProject; window.pianoverseSetProject({ ...p, sound: { ...p.sound, source: 'both', blend: 0.6, even: true, room: 'hall', hall: 0.35, start: 'swell', end: 'ring', bass: 2, treble: 1.5 } }); });
  await go('sound', 3000);
  await page.waitForFunction(() => !/Drawing the piano|Getting the piano ready/.test(document.body.innerText), null, { timeout: 300000 }).catch(() => console.log('the waveform is still drawing'));
  await page.waitForTimeout(1500);
  await screen('sound');
  await go('export', 2500); await screen('export');
  // the finished frame, and the effects alone (the transparent export)
  await go('style', 1500);
  await still('take-final', T, [1920, 1080]);
  if (want('take-fx')) { write(`${WORK}/take-fx.png`, await frame(T, [1920, 1080], null, true)); console.log('still take-fx'); }
  // the hero's loops, one per look
  for (const [id, name] of TAKE_LOOKS) { await pickLook(name); await loop('take-' + id, [960, 540], null, TAKE_SECS, TAKE_FROM); }
}
await b.close();
