// The share card (1200x630) and the touch icon, drawn with the site's own fonts.
import { createRequire } from 'module';
const { chromium } = createRequire((process.env.PIANOVERSE_APP ?? new URL('../../../pianoverse', import.meta.url).pathname) + '/package.json')('playwright');
const S = process.argv[2];
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
await p.goto('http://localhost:8090/assets/');
await p.setContent(`<html><head><base href="http://localhost:8090/"><style>
@font-face{font-family:Syncopate;font-weight:700;src:url(assets/fonts/syncopate-700.woff2)}
@font-face{font-family:Cormorant;font-weight:600;src:url(assets/fonts/cormorant-600.woff2)}
@font-face{font-family:Cormorant;font-weight:600;font-style:italic;src:url(assets/fonts/cormorant-600-italic.woff2)}
@font-face{font-family:Archivo;font-weight:100 900;src:url(assets/fonts/archivo.woff2)}
body{margin:0;width:1200px;height:630px;background:#F4EDE1;color:#2A1A1C;font-family:Archivo;position:relative;overflow:hidden}
.t{position:absolute;left:64px;top:60px;width:560px}
.w{font:700 15px Syncopate;letter-spacing:.2em}
h1{margin:44px 0 0;font:600 84px/0.95 Cormorant;letter-spacing:-.02em}
h1 em{color:#722F37}
p{margin:22px 0 0;font-size:24px;color:#6B5A55}
.m{position:absolute;left:64px;bottom:56px;font-size:18px;color:#6B5A55}
img{position:absolute;right:-60px;top:110px;width:640px;height:360px;object-fit:cover;border-radius:22px;box-shadow:0 40px 80px rgba(42,26,28,.25)}
</style></head><body><div class="t"><div class="w">PIANOVERSE</div><h1>The video editor for <em>pianists.</em></h1><p>Editing tools shaped around the piano.</p></div><div class="m">Free for Windows · pianoverse.in</div><img src="assets/looks/gold.jpg"></body></html>`);
await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(300);
await p.screenshot({ path: S + '/og.jpg', type: 'jpeg', quality: 88 });
await p.setViewportSize({ width: 180, height: 180 });
await p.setContent(`<html><body style="margin:0"><img src="http://localhost:8090/favicon.svg" style="width:180px;height:180px;display:block"></body></html>`);
await p.waitForTimeout(200);
await p.screenshot({ path: S + '/apple-touch-icon.png' });
await b.close();
