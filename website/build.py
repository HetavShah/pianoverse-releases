"""Build pianoverse.in. GitHub Pages serves this repository's main branch as it is, from its root: index.html,
404.html, the icons and assets/ there are the site (assets/piano and assets/sample are the app's downloads: never
touch them; the app checks their checksums).

The page is index.src.html with the galleries and links filled in. After editing the words or the layout, run the
last step and commit the new index.html:

  python3 website/build.py page      # index.html at the root (needs nothing but Python)

Every picture and clip on it is made by the app itself: the effects from a MIDI file on the app's drawn keyboard
(no video); the app's screens, the hero's loops and the before and after from a real take in assets/sample (a
landscape video and its project: the keyboard marked, the notes found in its sound; the same files the app downloads as
its sample take, so they live in assets/sample, kept like assets/piano). The app's source is checked out
next to this repository (../pianoverse) or wherever PIANOVERSE_APP says. Run these from that checkout (the frames go
to website/.work/, which is not committed):

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
# the hero: the editor in these looks (must match tools/render.mjs), the cursor picking them in turn
TAKE_LOOKS = [('gold', 'Gold Leaf'), ('ocean', 'Ocean Gem'), ('synth', 'Synthwave')]
TAKE_T = 7  # the moment of the take the screens and stills show
NOTES = [('glass', 'Glass'), ('gem', 'Gem'), ('hollow', 'Hollow'), ('soft', 'Soft glow')]
PARTICLES = [('fountain', 'Fountain'), ('vortex', 'Vortex'), ('explode', 'Explode'), ('streaks', 'Streaks')]
# the app's screens (1440x900): the whole window for wide screens, and on phones the part that matters
SCREENS = {
    'import': ('Pianoverse importing a video, its MIDI file and its sound', (0, 50, 700, 650)),
    'sync': ('Pianoverse lining the notes up with the keys in the video', (120, 96, 1100, 831)),
    'looks-gold': ('Pianoverse adding falling notes and light to a piano video, in the Gold Leaf look', (520, 96, 1440, 786)),
    'looks-ocean': ('The same take in the Ocean Gem look', (520, 96, 1440, 786)),
    'looks-synth': ('The same take in the Synthwave look', (520, 96, 1440, 786)),
    'p-notes': ('The Notes panel: shapes and textures', None),
    'p-saber': ('The Saber panel: colour, size and glow', None),
    'p-particles': ('The Particles panel: sparks on every note', None),
    'p-lighting': ('The Note light panel: the notes light the keys', None),
    'camera': ('Pianoverse moving the camera with the hands', None),
    'sound': ('Pianoverse mixing a grand piano under the recording', None),
    'export': ('Pianoverse exporting the video', (0, 50, 760, 810)),
}
# customize: the editor stays and the panel changes as you scroll (on phones: the right of the preview and the panel)
PIN = [('looks-gold', 'Looks', 'One click, a whole style.'), ('p-notes', 'Notes', 'Shapes and textures.'),
       ('p-saber', 'Saber', 'Light where the notes land.'), ('p-particles', 'Particles', 'A burst on every note.'),
       ('p-lighting', 'Light', 'The notes light your keys.'), ('camera', 'Camera', 'Follows your hands.')]
PIN_BOX = {'camera': (440, 96, 1440, 640)}
PIN_BOX_DEFAULT = (520, 96, 1440, 640)


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
    # the old page's files go; the piano and the sample take the app downloads stay
    for p in glob.glob(f'{A}/*'):
        if os.path.basename(p) not in ('piano', 'sample'):
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(f'{A}/fonts', exist_ok=True)
    nm = f'{ROOT}/node_modules'
    shutil.copy(f'{nm}/@fontsource-variable/archivo/files/archivo-latin-wght-normal.woff2', f'{A}/fonts/archivo.woff2')
    shutil.copy(f'{nm}/@fontsource/syncopate/files/syncopate-latin-700-normal.woff2', f'{A}/fonts/syncopate-700.woff2')
    shutil.copy(f'{nm}/@fontsource/cormorant-garamond/files/cormorant-garamond-latin-600-normal.woff2', f'{A}/fonts/cormorant-600.woff2')
    shutil.copy(f'{nm}/@fontsource/cormorant-garamond/files/cormorant-garamond-latin-600-italic.woff2', f'{A}/fonts/cormorant-600-italic.woff2')
    for id, _ in TAKE_LOOKS:
        loop(f'take-{id}', f'{A}/hero/{id}')
    loop('saber', f'{A}/saber/gold')
    for id, _ in PARTICLES:
        loop(f'part-{id}', f'{A}/particles/{id}')
    for id, _ in LOOKS:
        save(Image.open(f'{WORK}/look-{id}.jpg'), f'{A}/looks/{id}.jpg', (960, 540))
    for id, _ in NOTES:
        save(Image.open(f'{WORK}/notes-{id}.jpg'), f'{A}/notes/{id}.jpg')
    for id in ('flame', 'electric'):
        save(Image.open(f'{WORK}/saber-{id}.jpg'), f'{A}/saber/{id}.jpg', (640, 360))
    save(Image.open(f'{WORK}/title-open.jpg'), f'{A}/titles/open.jpg')
    save(Image.open(f'{WORK}/title-end.jpg'), f'{A}/titles/end.jpg')
    for id, (_, box) in SCREENS.items():
        im = Image.open(f'{WORK}/ui-{id}.png')
        save(im, f'{A}/screens/{id}.jpg', q=86)
        if box:
            save(im.crop(box), f'{A}/screens/{id}-m.jpg', q=86)
    for id, _, _ in PIN:
        save(Image.open(f'{WORK}/ui-{id}.png').crop(PIN_BOX.get(id, PIN_BOX_DEFAULT)), f'{A}/screens/{id}-p.jpg', q=86)
    # the sound tab down to its waveforms
    save(Image.open(f'{WORK}/ui-sound.png').crop((0, 96, 1440, 640)), f'{A}/screens/sound-top.jpg', q=86)
    # the take: finished, as filmed, and the effects alone (the transparent export)
    fin = Image.open(f'{WORK}/take-final.jpg')
    save(fin, f'{A}/take/final.jpg', q=84)
    save(fin, f'{A}/take/final-s.jpg', (960, 540))
    sh('ffmpeg', '-v', 'error', '-y', '-ss', str(TAKE_T), '-i', f'{A}/sample/take.mp4', '-frames:v', '1', '-q:v', '2', f'{WORK}/take-raw.jpg')
    save(Image.open(f'{WORK}/take-raw.jpg'), f'{A}/take/raw.jpg', q=84)
    Image.open(f'{WORK}/take-fx.png').resize((960, 540), Image.LANCZOS).save(f'{A}/take/fx.png', optimize=True)
    shutil.copy(f'{WORK}/ui-rects.json', f'{A}/take/rects.json')
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
    import json
    html = open(f'{W}/index.src.html').read()
    # the hero: the editor in each look, the preview playing the take, a cursor that clicks the next look's card
    rects = json.load(open(f'{A}/take/rects.json'))
    pct = lambda v, n: f'{v / n * 100:.3f}%'
    x, y, w, h = rects['preview']
    tour = []
    for i, (id, name) in enumerate(TAKE_LOOKS):
        cx, cy, cw, ch = rects['card:' + name]
        tour.append(f'        <img class="scr{" on" if i == 0 else ""}" src="assets/screens/looks-{id}.jpg" alt="{"Pianoverse, the video editor, adding falling notes and light to a piano video" if i == 0 else ""}" '
                    f'width="1440" height="900" data-src="assets/hero/{id}.mp4" data-poster="assets/hero/{id}.jpg" data-cx="{pct(cx + cw * .55, 1440)}" data-cy="{pct(cy + ch * .45, 900)}"'
                    f'{" fetchpriority=\"high\"" if i == 0 else " loading=\"lazy\""}>')
    tour.append(f'        <video src="assets/hero/gold.mp4" poster="assets/hero/gold.jpg" autoplay muted loop playsinline '
                f'style="left:{pct(x, 1440)};top:{pct(y, 900)};width:{pct(w, 1440)};height:{pct(h, 900)}" aria-label="The preview: the take with notes falling onto the keys"></video>')
    tour.append('        <span class="cursor" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M3 2l7 19 2.5-8L21 10z" fill="#fff" stroke="#000" stroke-width="1.4" stroke-linejoin="round"/></svg></span>')
    pin_list = '\n'.join(f'          <li data-cap="{cap}"{" class=\"on\"" if i == 0 else ""}><b>{i + 1:02d}</b>{name}<i></i></li>' for i, (id, name, cap) in enumerate(PIN))
    pin_shots = '\n'.join(f'          <picture><source media="(max-width: 700px)" srcset="assets/screens/{id}-p.jpg">'
                          f'<img{" class=\"on\"" if i == 0 else ""} src="assets/screens/{id}.jpg" alt="{SCREENS[id][0]}" loading="lazy" width="1440" height="900"></picture>'
                          for i, (id, name, cap) in enumerate(PIN))
    html = (html.replace('%%RELEASES_ALL%%', RELEASES).replace('%%RELEASES%%', f'{RELEASES}/latest').replace('%%TOUR%%', '\n'.join(tour))
            .replace('%%PIN_LIST%%', pin_list).replace('%%PIN_SCREENS%%', pin_shots)
            .replace('%%LOOKS%%', figures(LOOKS, 'looks')).replace('%%NOTES%%', figures(NOTES, 'notes'))
            .replace('%%PARTICLES%%', figures(PARTICLES, 'particles', video=True)))
    for id, (alt, box) in SCREENS.items():
        src = f'<source media="(max-width: 700px)" srcset="assets/screens/{id}-m.jpg">' if box else ''
        html = html.replace(f'%%SCREEN:{id}%%', f'<picture>{src}<img src="assets/screens/{id}.jpg" alt="{alt}" loading="lazy" width="1440" height="900"></picture>')
    assert '%%' not in html, html[html.index('%%') - 40:html.index('%%') + 40]
    open(f'{S}/index.html', 'w').write(html)


steps = sys.argv[1:] or ['page']
for s in steps:
    {'render': render, 'media': media, 'page': page}[s]()
