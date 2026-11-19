# Generates hour numerals (solid/outline), minute hand and ticks. Font: Barlow (OFL).
import math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'source/res/drawable-nodpi')
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
H = 230
def shadow(mask, r=6, a=150):
    s = Image.new('RGBA', mask.size, (0,0,0,0)); s.putalpha(mask.filter(ImageFilter.GaussianBlur(r)).point(lambda v: v*a//255)); return s
solid = ImageFont.truetype(f'{F}/Barlow-SemiBold.ttf', 250)
light = ImageFont.truetype(f'{F}/Barlow-Light.ttf', 250)
widths = {}
for d in '0123456789':
    w = int(solid.getlength(d)) + 8; widths[d] = w
    for kind in ('s', 'l'):
        m = Image.new('L', (w, H), 0); g = ImageDraw.Draw(m)
        if kind == 's':
            g.text((w/2, H/2), d, font=solid, fill=255, anchor='mm')
        else:
            g.text((w/2, H/2), d, font=solid, fill=255, anchor='mm', stroke_width=3, stroke_fill=255)
            inner = Image.new('L', (w, H), 0); ImageDraw.Draw(inner).text((w/2, H/2), d, font=solid, fill=255, anchor='mm')
            inner = inner.filter(ImageFilter.MinFilter(3))
            m = Image.composite(Image.new('L', (w, H), 0), m, inner)
        img = shadow(m, 5 if kind == 's' else 3, 160 if kind == 's' else 120)
        fg = Image.new('RGBA', (w, H), (255,255,255,0)); fg.putalpha(m)
        Image.alpha_composite(img, fg).save(f'{D}/hr_{kind}_{d}.png')
open(os.path.join(os.path.dirname(D), '..', '..', 'digit_widths.txt'), 'w').write(' '.join(f'{k}:{v}' for k,v in widths.items()))
# minute hand: 40x450, pivot at center (20,225)
S = 4; hw = Image.new('RGBA', (40*S, 450*S), (0,0,0,0)); g = ImageDraw.Draw(hw)
g.rounded_rectangle((17*S, 6*S, 23*S, 226*S), radius=3*S, fill=(0,0,0,110))
g.rounded_rectangle((18*S, 6*S, 22*S, 225*S), radius=2*S, fill=(255,255,255,255))
g.ellipse((11*S, 216*S, 29*S, 234*S), fill=(0,0,0,120)); g.ellipse((12*S, 217*S, 28*S, 233*S), fill=(255,255,255,255))
g.ellipse((17*S, 222*S, 23*S, 228*S), fill=(30,30,40,255))
hw.resize((40, 450), Image.LANCZOS).save(f'{D}/min_hand.png')
# 60 ticks, outside the step/sleep arcs (r 217-224)
T = Image.new('RGBA', (450*S, 450*S), (0,0,0,0)); g = ImageDraw.Draw(T); c = 225*S
for i in range(60):
    a = math.radians(i*6); maj = i % 5 == 0
    r0, r1, w, al = (214 if maj else 218)*S, 224*S, (4 if maj else 2)*S, 255 if maj else 170
    g.line((c+r0*math.sin(a), c-r0*math.cos(a), c+r1*math.sin(a), c-r1*math.cos(a)), fill=(255,255,255,al), width=w)
T.resize((450, 450), Image.LANCZOS).save(f'{D}/ticks.png')
print('ok', widths)
# crescent moon 56x56 and dawn/dusk glow
mo = Image.new('RGBA', (56*S, 56*S), (0,0,0,0)); g = ImageDraw.Draw(mo)
glow = Image.new('L', (56*S, 56*S), 0); ImageDraw.Draw(glow).ellipse((6*S, 6*S, 50*S, 50*S), fill=90)
mo.putalpha(glow.filter(ImageFilter.GaussianBlur(5*S)))
disc = Image.new('L', (56*S, 56*S), 0); ImageDraw.Draw(disc).ellipse((14*S, 14*S, 42*S, 42*S), fill=255)
bite = Image.new('L', (56*S, 56*S), 0); ImageDraw.Draw(bite).ellipse((22*S, 9*S, 48*S, 37*S), fill=255)
cres = Image.composite(Image.new('L', disc.size, 0), disc, bite)
col = Image.new('RGBA', mo.size, (255, 246, 210, 0)); col.putalpha(cres)
base = Image.new('RGBA', mo.size, (220, 230, 255, 0)); base.putalpha(mo.getchannel('A'))
Image.alpha_composite(base, col).resize((56, 56), Image.LANCZOS).save(f'{D}/moon.png')
du = Image.new('RGBA', (450, 450))
for y in range(450):
    k = max(0.0, min(1.0, (y - 40) / 300)); a = int(255 * k ** 1.6)
    ImageDraw.Draw(du).line((0, y, 450, y), fill=(255, int(150 - 50 * k), int(120 - 60 * k), a))
du.save(f'{D}/sky_dusk.png')
