# Weather, hour-change and season assets. Run after gen_assets.py.
import os, random, colorsys, math
from PIL import Image, ImageDraw, ImageFilter
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'source/res/drawable-nodpi')
R = random.Random(42)
def tile_streaks(n, color, lmin, lmax, w, a):
    im = Image.new('RGBA', (450, 450)); g = ImageDraw.Draw(im)
    for _ in range(n):
        x, y, L = R.uniform(0, 450), R.uniform(0, 450), R.uniform(lmin, lmax)
        for dy in (0, -450, 450):
            g.line((x, y + dy, x - L * 0.18, y + dy + L), fill=color + (int(a * R.uniform(.5, 1)),), width=w)
    return im
def stack(im):
    o = Image.new('RGBA', (450, 900)); o.paste(im, (0, 0)); o.paste(im, (0, 450)); return o
stack(tile_streaks(70, (215, 230, 255), 18, 34, 2, 170)).save(f'{D}/rain.png')
stack(tile_streaks(40, (235, 240, 255), 26, 44, 3, 200)).save(f'{D}/rain_near.png')
sn = Image.new('RGBA', (450, 450)); g = ImageDraw.Draw(sn)
for _ in range(90):
    x, y, r = R.uniform(0, 450), R.uniform(0, 450), R.uniform(1.5, 3.8)
    for dy in (0, -450, 450): g.ellipse((x - r, y + dy - r, x + r, y + dy + r), fill=(255, 255, 255, R.randint(170, 250)))
stack(sn).save(f'{D}/snow.png')
fog = Image.new('RGBA', (900, 450)); g = ImageDraw.Draw(fog)
for _ in range(60):
    x, y, rx, ry = R.uniform(0, 900), R.uniform(230, 430), R.uniform(60, 140), R.uniform(18, 40)
    for dx in (0, -900, 900): g.ellipse((x + dx - rx, y - ry, x + dx + rx, y + ry), fill=(225, 230, 238, 60))
fog.filter(ImageFilter.GaussianBlur(14)).save(f'{D}/fog.png')
st = Image.new('RGBA', (900, 190)); g = ImageDraw.Draw(st)
for _ in range(55):
    x, y, r = R.uniform(0, 900), R.uniform(40, 130), R.uniform(28, 60)
    sh = R.randint(105, 140)
    for dx in (0, -900, 900): g.ellipse((x + dx - r * 1.4, y - r, x + dx + r * 1.4, y + r), fill=(sh, sh + 6, sh + 16, 235))
st.filter(ImageFilter.GaussianBlur(4)).save(f'{D}/storm.png')
for name, col in (('overcast_day', (150, 160, 175)), ('overcast_night', (25, 28, 38))):
    o = Image.new('RGBA', (450, 450)); g = ImageDraw.Draw(o)
    for y in range(450): g.line((0, y, 450, y), fill=col + (int(255 * max(0.0, 1 - y / 330) ** 0.7),))
    o.save(f'{D}/{name}.png')
S = 4; ring = Image.new('RGBA', (450 * S, 450 * S)); g = ImageDraw.Draw(ring)
g.ellipse((8 * S, 8 * S, 442 * S, 442 * S), outline=(255, 255, 255, 255), width=5 * S)
ring.resize((450, 450), Image.LANCZOS).save(f'{D}/ring.png')
# seasons: recolor the greens
def recolor(src, fn):
    im = Image.open(f'{D}/{src}.png').convert('RGBA'); px = im.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            r, gg, b, a = px[x, y]
            if a == 0: continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, gg / 255, b / 255)
            if 0.20 < h < 0.50 and s > 0.18:
                h, s, v = fn(h, s, v, x, y)
                r, gg, b = (int(c * 255) for c in colorsys.hsv_to_rgb(h, s, v)); px[x, y] = (r, gg, b, a)
    return im
autumn = lambda h, s, v, x, y: ((0.07 if v < 0.62 else 0.12) + 0.02 * math.sin(x * .3 + y * .2), min(1, s * 1.25), min(1, v * 1.05))
winter_g = lambda h, s, v, x, y: (0.58, 0.10, min(1, 0.80 + v * 0.18)) if v >= 0.55 else (0.45, s * 0.45, v * 0.9)
winter_t = lambda h, s, v, x, y: (0.45, s * 0.45, min(1, v * 0.95))
recolor('front', autumn).save(f'{D}/front_autumn.png'); recolor('tree', autumn).save(f'{D}/tree_autumn.png'); recolor('bush', autumn).save(f'{D}/bush_autumn.png')
recolor('front', winter_g).save(f'{D}/front_winter.png'); recolor('tree', winter_t).save(f'{D}/tree_winter.png')
recolor('bush', lambda h, s, v, x, y: (0.08, 0.35, v * 0.8)).save(f'{D}/bush_winter.png')
def flowers(src, n, area, cols):
    im = Image.open(f'{D}/{src}.png').convert('RGBA'); px = im.load(); g = ImageDraw.Draw(im); k = 0
    while k < n:
        x, y = R.randint(*area[0]), R.randint(*area[1]); r, gg, b, a = px[x, y]
        h, s, v = colorsys.rgb_to_hsv(r / 255, gg / 255, b / 255)
        if a > 200 and 0.2 < h < 0.5 and s > .18:
            c = R.choice(cols); rr = R.choice((1.6, 2.2, 2.8)); g.ellipse((x - rr, y - rr, x + rr, y + rr), fill=c); k += 1
    return im
flowers('front', 140, ((0, 449), (300, 449)), [(255, 170, 205, 255), (255, 235, 120, 255), (255, 255, 255, 255), (200, 160, 255, 255)]).save(f'{D}/front_spring.png')
flowers('bush', 25, ((55, 135), (367, 423)), [(255, 160, 200, 255), (255, 255, 255, 255)]).save(f'{D}/bush_spring.png')
print('ok')
# summer: mountains without snow (white/ice-blue replaced by rock tone)
im = Image.open(f'{D}/back.png').convert('RGBA'); px = im.load()
for y in range(im.size[1]):
    for x in range(im.size[0]):
        r, gg, b, a = px[x, y]
        if a == 0 or y > 340: continue
        h, s, v = colorsys.rgb_to_hsv(r / 255, gg / 255, b / 255)
        if s < 0.16 and v > 0.80:
            px[x, y] = (172, 168, 222, a) if v > 0.93 else (146, 142, 204, a)
im.save(f'{D}/back_summer.png')
print('summer ok')
