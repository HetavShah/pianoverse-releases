"""Build pianoverse.in. GitHub Pages serves this repository's main branch as it is, from its root: index.html,
404.html, the icons and assets/ there are the site (assets/piano is the app's download: never touch it).

The page is index.src.html with the galleries and links filled in. After editing the words or the layout, run the
last step and commit the new index.html:

  python3 website/build.py page      # index.html at the root (needs nothing but Python)

Every picture and clip on it is made by the app itself: the effects from a MIDI file on the app's drawn keyboard
(no video), the app's screens from the sample take in the app's source, checked out next to this repository
(../pianoverse) or wherever PIANOVERSE_APP says. Run these from that checkout (the frames go to website/.work/,
which is not committed):

  npx vite build && npx vite preview --port 4173      # the app, for rendering frames
  python3 website/build.py render    # frames and screens from the app (slow without a graphics card)
  python3 website/build.py media     # loops, stills, screens, fonts
  python3 website/build.py page      # index.html
  python3 -m http.server 8090       # from the repository's root, to look at it
  node website/tools/og.mjs .                  # share card and touch icon
  node website/tools/shoot.mjs <dir>                      # full-page screenshots at 1440 and 390
"""
import glob, os, shutil, subprocess, sys

W = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get('PIANOVERSE_APP') or os.path.join(os.path.dirname(os.path.dirname(W)), 'pianoverse')
WORK = f'{W}/.work'
S = os.path.dirname(W)  # the site is the repository's root
A = f'{S}/assets'
RELEASES = 'https://github.com/HetavShah/pianoverse-releases/releases'
# must match tools/render.mjs
FPS, FADE = 24, 1

LOOKS = [('gold', 'Gold Leaf'), ('lagoon', 'Lagoon'), ('ember', 'Ember'), ('neon', 'Neon Night'), ('aurora', 'Aurora'), ('swan', 'Swan')]
PICKER = ['gold', 'lagoon', 'ember', 'neon']  # the hero's loops
NOTES = [('glass', 'Glass'), ('gem', 'Gem'), ('hollow', 'Hollow'), ('soft', 'Soft glow')]
PARTICLES = [('fountain', 'Fountain'), ('vortex', 'Vortex'), ('explode', 'Explode'), ('streaks', 'Streaks')]
# the app's screens (1440x900): the whole window for wide screens, and on phones the part that matters
SCREENS = {
    'import': ('Pianoverse importing a video, its MIDI file and its sound', (0, 50, 700, 650)),
    'sync': ('Pianoverse lining the notes up with the keys in the video', (150, 90, 950, 890)),
    'picture': ('Pianoverse adding falling notes and light to a piano video', (230, 90, 1030, 890)),
    'camera': ('Pianoverse moving the camera with the hands', (250, 90, 1050, 890)),
    'sound': ('Pianoverse mixing a grand piano under the recording', (0, 90, 820, 910)),
    'export': ('Pianoverse exporting the video', (0, 50, 760, 810)),
}


def sh(*a, **k):
    subprocess.run(a, check=True, **k)


def render():
    """frames and screens from the app's renderer (needs the vite preview on :4173). Two runs: the software GPU of a
    headless browser doesn't last through everything at once"""
    tool = f'{W}/tools/render.mjs'
    sh('node', tool, WORK, 'drawn')
    sh('node', tool, WORK, 'video')


def save(im, path, size=None, q=84):
    from PIL import Image
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im = im.convert('RGB')
    if size:
        im = im.resize(size, Image.LANCZOS)
    im.save(path, quality=q, optimize=True, progressive=True)


def loop(name, out):
    """a clip that loops without a jump: its last second fades into its first"""
    from PIL import Image
    fr = sorted(glob.glob(f'{WORK}/{name}/*.jpg'))
    n = len(fr) - FADE * FPS
    tmp = f'{WORK}/_loop'
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    for i in range(n):
        im = Image.open(fr[i])
        if i < FADE * FPS:
            im = Image.blend(Image.open(fr[n + i]), im, i / (FADE * FPS))
        im.save(f'{tmp}/{i:05d}.jpg', quality=95)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sh('ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', f'{tmp}/%05d.jpg', '-vf', 'format=yuv420p',
       '-c:v', 'libx264', '-preset', 'slow', '-crf', '24', '-movflags', '+faststart', '-an', f'{out}.mp4')
    save(Image.open(f'{tmp}/{FADE * FPS:05d}.jpg'), f'{out}.jpg')
    shutil.rmtree(tmp)


def media():
    from PIL import Image
    # the old page's files go; the piano the app downloads stays
    for p in glob.glob(f'{A}/*'):
        if os.path.basename(p) != 'piano':
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(f'{A}/fonts', exist_ok=True)
    nm = f'{ROOT}/node_modules'
    shutil.copy(f'{nm}/@fontsource-variable/archivo/files/archivo-latin-wght-normal.woff2', f'{A}/fonts/archivo.woff2')
    shutil.copy(f'{nm}/@fontsource/syncopate/files/syncopate-latin-700-normal.woff2', f'{A}/fonts/syncopate-700.woff2')
    shutil.copy(f'{nm}/@fontsource/cormorant-garamond/files/cormorant-garamond-latin-600-normal.woff2', f'{A}/fonts/cormorant-600.woff2')
    shutil.copy(f'{nm}/@fontsource/cormorant-garamond/files/cormorant-garamond-latin-600-italic.woff2', f'{A}/fonts/cormorant-600-italic.woff2')
    for id in PICKER:
        loop(f'hero-{id}', f'{A}/hero/{id}')
    loop('hero-short', f'{A}/hero/short')
    loop('saber', f'{A}/saber/gold')
    for id, _ in PARTICLES:
        loop(f'part-{id}', f'{A}/particles/{id}')
    for id, _ in LOOKS:
        save(Image.open(f'{WORK}/look-{id}.jpg'), f'{A}/looks/{id}.jpg', (960, 540))
    for id, _ in NOTES:
        save(Image.open(f'{WORK}/notes-{id}.jpg'), f'{A}/notes/{id}.jpg')
    for id in ('flame', 'electric'):
        save(Image.open(f'{WORK}/saber-{id}.jpg'), f'{A}/saber/{id}.jpg', (640, 360))
    for id in ('landscape', 'square', 'vertical'):
        save(Image.open(f'{WORK}/shape-{id}.jpg'), f'{A}/shapes/{id}.jpg')
    save(Image.open(f'{WORK}/title-open.jpg'), f'{A}/titles/open.jpg')
    save(Image.open(f'{WORK}/title-end.jpg'), f'{A}/titles/end.jpg')
    for id, (_, box) in SCREENS.items():
        im = Image.open(f'{WORK}/ui-{id}.png')
        save(im, f'{A}/screens/{id}.jpg', q=86)
        save(im.crop(box), f'{A}/screens/{id}-m.jpg', q=86)
    # the README's picture
    save(Image.open(f'{WORK}/look-gold.jpg'), f'{S}/docs/hero.jpg', (1280, 720))
    for f in ('favicon.svg', '404.html'):
        shutil.copy(f'{W}/static/{f}', f'{S}/{f}')
    open(f'{S}/.nojekyll', 'w').close()


def figures(items, folder, video=False):
    out = []
    for id, name in items:
        if video:
            pic = (f'<video src="assets/{folder}/{id}.mp4" poster="assets/{folder}/{id}.jpg" muted loop playsinline preload="none" '
                   f'aria-label="{name}"></video>')
        else:
            pic = f'<img src="assets/{folder}/{id}.jpg" alt="{name}" loading="lazy" width="960" height="540">'
        out.append(f'      <figure><div class="shot">{pic}</div><figcaption>{name}</figcaption></figure>')
    return '\n'.join(out)


def page():
    html = open(f'{W}/index.src.html').read()
    names = dict(LOOKS)
    picker = '\n'.join(
        f'        <button type="button" aria-pressed="{str(i == 0).lower()}" data-name="{names[id]}" data-src="assets/hero/{id}.mp4" '
        f'data-poster="assets/hero/{id}.jpg"><img src="assets/looks/{id}.jpg" alt="{names[id]}"><span>{names[id]}</span></button>'
        for i, id in enumerate(PICKER))
    html = (html.replace('%%RELEASES_ALL%%', RELEASES).replace('%%RELEASES%%', f'{RELEASES}/latest').replace('%%PICKER%%', picker)
            .replace('%%LOOKS%%', figures(LOOKS, 'looks')).replace('%%NOTES%%', figures(NOTES, 'notes'))
            .replace('%%PARTICLES%%', figures(PARTICLES, 'particles', video=True)))
    for id, (alt, _) in SCREENS.items():
        html = html.replace(f'%%SCREEN:{id}%%', f'<picture><source media="(max-width: 700px)" srcset="assets/screens/{id}-m.jpg">'
                                                f'<img src="assets/screens/{id}.jpg" alt="{alt}" loading="lazy" width="1440" height="900"></picture>')
    assert '%%' not in html, html[html.index('%%') - 40:html.index('%%') + 40]
    open(f'{S}/index.html', 'w').write(html)


steps = sys.argv[1:] or ['page']
for s in steps:
    {'render': render, 'media': media, 'page': page}[s]()
