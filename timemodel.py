# Real time + daily routine + weather + seasons on top of the original Aurora Farm watchface.xml (MIT).
# Sunrise/sunset are approximated at build time from LAT/LON/UTC_OFFSET (edit below or set env vars):
#   half-day length = mean + amplitude * cos(2*pi*(doy - solstice)/365), solar noon from longitude.
# ov (tests): m (minute of day), doy (day of year), cond (WEATHER.CONDITION), flip (0..1).
import re, os, math
LAT = float(os.environ.get('WF_LAT', '-30.03'))        # default: Porto Alegre, BR
LON = float(os.environ.get('WF_LON', '-51.23'))
UTC_OFFSET = float(os.environ.get('WF_UTC_OFFSET', '-3'))
def _half_day(dec_deg):
    x = -math.tan(math.radians(LAT)) * math.tan(math.radians(dec_deg))
    return math.degrees(math.acos(max(-1, min(1, x)))) / 15 * 60 + 5   # +5 min refraction/disc
_hs, _hw = _half_day(-23.44), _half_day(23.44)             # December / June solstice
HD_MEAN, HD_AMP = (_hs + _hw) / 2, (_hs - _hw) / 2         # AMP > 0 south, < 0 north
NOON = 720 + (UTC_OFFSET * 15 - LON) * 4
SEASON_SHIFT = 0 if LAT < 0 else 182                        # northern hemisphere: seasons flipped
T = '(fract(([SECONDS_IN_DAY] + [MILLISECOND] / 1000) / 45) * 45)'
NF = ('(clamp(((fract(([SECONDS_IN_DAY] + [MILLISECOND] / 1000) / 45) * 45) - 18) / 4, 0, 1) - '
      'clamp(((fract(([SECONDS_IN_DAY] + [MILLISECOND] / 1000) / 45) * 45) - 41) / 4, 0, 1))')
U = '([SECONDS_IN_DAY] + [MILLISECOND] / 1000)'
REAL = dict(m='[HOUR_0_23] * 60 + [MINUTE] + [SECOND] / 60', doy='[DAY_OF_YEAR]',
            cond='([WEATHER.IS_AVAILABLE] ? [WEATHER.CONDITION] : 0)',
            flip='(([MINUTE] == 59) ? clamp(([SECOND] + [MILLISECOND] / 1000 - 57) / 3, 0, 1) : 0)')

def build(ov):
    """Each value is computed ONCE per frame in an invisible node (WFF v4 <Reference>) and consumed
    as [REFERENCE.name]. Inlined, the same math repeated in ~150 transforms (1.5x the original's CPU)."""
    o = dict(REAL, **(ov or {}))
    refs = []
    def ref(name, expr):
        refs.append((name, expr)); return f'[REFERENCE.{name}]'
    M = ref('M', o['m']); DOY = ref('DOY', o['doy']); C = ref('C', o['cond'])
    HD = ref('HD', f'{HD_MEAN:.1f} + {HD_AMP:.1f} * cos(6.2832 * ({DOY} - 355) / 365)')
    RISE = ref('RISE', f'{NOON:.1f} - {HD}'); SET = ref('SET', f'{NOON:.1f} + {HD}')
    D = ref('D', f'clamp(({M} - {RISE} + 25) / 50, 0, 1) * (1 - clamp(({M} - {SET} + 25) / 50, 0, 1))')
    E = dict(M=M, D=D, N=f'(1 - {D})', U=U, C=C)
    E['FLIP'] = ref('FLIP', o['flip'])
    E['P'] = ref('P', f'clamp(({M} - {RISE}) / ({SET} - {RISE}), 0, 1)')
    E['PN'] = ref('PN', f'clamp(fract(({M} - {SET}) / 1440) * 1440 / (1440 - ({SET} - {RISE})), 0, 1)')
    E['DUSK'] = ref('DUSK', f'clamp(1 - abs({M} - {RISE}) / 55, 0, 1) + clamp(1 - abs({M} - {SET}) / 55, 0, 1)')
    # routine: the boy works from sunrise+30 to sunset-60; otherwise he stays inside (t=16.5)
    WORK = f'({M} &gt;= {RISE} + 30 &amp;&amp; {M} &lt; {SET} - 60)'
    E['TP'] = ref('TP', f'({D} &gt;= 0.5) ? ({WORK} ? (fract({U} / 18) * 18) : 16.5) : (22 + fract({U} / 20) * 20)')
    # cabin lights: on from dusk until 23:00, and again when waking up (sunrise-40 .. sunrise+30)
    E['LON'] = ref('LON', f'((({M} &gt;= {SET} - 30) &amp;&amp; ({M} &lt; 1380)) || (({M} &gt;= {RISE} - 40) &amp;&amp; ({M} &lt; {RISE} + 30))) ? 1 : 0')
    # weather (WFF codes: 1 clear 2 cloudy 3 fog 4 heavy_rain 5 heavy_snow 6 rain 7 snow 8 sunny
    #        9 thunder 10 sleet 11 light_snow 12 light_rain 13 mist 14 partly 15 windy)
    # Samsung reports 14 while naming it "Clear", so partly cloudy barely greys the sky.
    E['CL'] = ref('CL', f'({C} == 2 || {C} == 4 || {C} == 5 || {C} == 6 || {C} == 7 || {C} == 9 || {C} == 10) ? 1 : '
                  f'(({C} == 11 || {C} == 12) ? 0.75 : (({C} == 3 || {C} == 13) ? 0.6 : ({C} == 14 ? 0.15 : ({C} == 15 ? 0.3 : 0))))')
    E['RAIN'] = ref('RAIN', f'({C} == 4 || {C} == 9) ? 1 : ({C} == 6 ? 0.7 : (({C} == 12 || {C} == 10) ? 0.4 : 0))')
    E['SNOW'] = ref('SNOW', f'{C} == 5 ? 1 : ({C} == 7 ? 0.7 : (({C} == 11 || {C} == 10) ? 0.45 : 0))')
    E['FOG'] = ref('FOG', f'{C} == 3 ? 1 : ({C} == 13 ? 0.6 : 0)')
    E['WINDY'] = ref('WINDY', f'({C} == 15 || {C} == 9 || {C} == 4) ? 1 : 0')
    # seasons (southern dates, shifted 182 days up north): autumn ~Apr 20, winter ~Jul 19, spring ~Oct 17, summer ~Jan 20 (no snow)
    sw = lambda c: f'clamp(1.7 * cos(6.2832 * ({DOY} - {c}) / 365) - 0.7, 0, 1)'
    for k, c in (('AUT', 110), ('WIN', 200), ('SPR', 290), ('SUM', 20)): E[k] = ref(k, sw((c + SEASON_SHIFT) % 365))
    E['REFS'] = '    <Group x="0" y="0" width="1" height="1" name="refs">\n' + ''.join(
        f'      <PartDraw x="0" y="0" width="1" height="1"><Transform target="x" value="{e}"/>'
        f'<Reference name="{n}" source="x" defaultValue="0"/><Rectangle x="0" y="0" width="1" height="1"><Fill color="#00000000"/></Rectangle></PartDraw>\n'
        for n, e in refs) + '    </Group>\n'
    return E

STORY = re.compile(r'\bt &(gt|lt);|\bt (&gt;|&lt;)|\(t - |\(t \+ ')

def element_of(s, res):
    i = s.index(f'<Image resource="{res}"/>'); a = s.rindex('<PartImage', 0, i); b = s.index('</PartImage>', i) + len('</PartImage>')
    return a, b

def apply(s, ov=None):
    E = build(ov)
    # --- seasons: copy of the element with recolored art on top, alpha = season weight
    for res, variants in (('back', ('summer',)), ('front', ('autumn', 'winter', 'spring')), ('tree', ('autumn', 'winter')), ('bush', ('autumn', 'winter', 'spring'))):
        a, b = element_of(s, res); el = s[a:b]; extra = ''
        for v in variants:
            w = E[{'autumn': 'AUT', 'winter': 'WIN', 'spring': 'SPR', 'summer': 'SUM'}[v]]
            cp = el.replace(f'resource="{res}"', f'resource="{res}_{v}"')
            cp = cp.replace('>', f'>\n        <Transform target="alpha" value="255 * {w}"/>', 1)
            extra += '\n      ' + cp
        s = s[:b] + extra + s[b:]
    # --- cabin lights follow the routine
    a, b = element_of(s, 'lights'); el = s[a:b]
    el = el.replace(f'value="255 * {NF}', f'value="255 * {E["LON"]} * {NF}'); s = s[:a] + el + s[b:]
    # --- sun and moon by real time, on an arc outside the numeral
    a = s.index('<PartImage x="0" y="0" width="100" height="100">'); b = s.index('</PartImage>', a) + len('</PartImage>')
    s = s[:a] + f'''<PartImage x="0" y="0" width="100" height="100" name="sun">
        <Transform target="x" value="175 - 182 * cos(3.1416 * {E['P']})"/>
        <Transform target="y" value="182 - 182 * sin(3.1416 * {E['P']})"/>
        <Transform target="alpha" value="255 * {E['D']}"/>
        <Image resource="sun"/>
      </PartImage>
      <PartImage x="0" y="0" width="56" height="56" name="moon">
        <Transform target="x" value="197 - 182 * cos(3.1416 * {E['PN']})"/>
        <Transform target="y" value="204 - 182 * sin(3.1416 * {E['PN']})"/>
        <Transform target="alpha" value="240 * {E['N']}"/>
        <Image resource="moon"/>
      </PartImage>''' + s[b:]
    # --- dawn/dusk glow right after the night sky
    a, b = element_of(s, 'sky_night')
    s = s[:b] + f'''
      <PartImage x="0" y="0" width="450" height="450" name="dusk">
        <Transform target="alpha" value="210 * clamp({E['DUSK']}, 0, 1) * (1 - 0.7 * {E['CL']})"/>
        <Image resource="sky_dusk"/>
      </PartImage>''' + s[b:]
    # --- overcast + storm band, before the mountains (covers sun, moon, stars, aurora)
    a, _ = element_of(s, 'back')
    s = s[:a] + f'''<PartImage x="0" y="0" width="900" height="190" name="storm">
        <Transform target="x" value="-450 * fract({U} / ({E['WINDY']} ? 10 : 34))"/>
        <Transform target="alpha" value="255 * clamp(({E['CL']} - 0.3) / 0.7, 0, 1) * (1 - 0.55 * {E['N']})"/>
        <Image resource="storm"/>
      </PartImage>
      <PartImage x="0" y="0" width="450" height="450" name="overcastDay">
        <Transform target="alpha" value="215 * {E['CL']} * {E['D']}"/>
        <Image resource="overcast_day"/>
      </PartImage>
      <PartImage x="0" y="0" width="450" height="450" name="overcastNight">
        <Transform target="alpha" value="235 * {E['CL']} * {E['N']}"/>
        <Image resource="overcast_night"/>
      </PartImage>
      ''' + s[a:]
    # --- rain, snow, fog and lightning in front of the scene
    end = s.index('    </Group>\n    <PartAnimatedImage x="262"')
    s = s[:end] + f'''      <PartImage x="0" y="0" width="450" height="450" name="fog">
        <Transform target="x" value="-450 * fract({U} / 40)"/>
        <Transform target="alpha" value="235 * {E['FOG']}"/>
        <Image resource="fog"/>
      </PartImage>
      <PartImage x="0" y="-450" width="450" height="900" name="rainFar">
        <Transform target="y" value="-450 + 450 * fract({U} / 1.1)"/>
        <Transform target="alpha" value="255 * {E['RAIN']}"/>
        <Image resource="rain"/>
      </PartImage>
      <PartImage x="0" y="-450" width="450" height="900" name="rainNear">
        <Transform target="y" value="-450 + 450 * fract({U} / 0.7)"/>
        <Transform target="alpha" value="255 * clamp(({E['RAIN']} - 0.45) / 0.55, 0, 1)"/>
        <Image resource="rain_near"/>
      </PartImage>
      <PartImage x="0" y="-450" width="450" height="900" name="snow">
        <Transform target="y" value="-450 + 450 * fract({U} / 9)"/>
        <Transform target="x" value="6 * sin({U} * 0.8)"/>
        <Transform target="alpha" value="255 * {E['SNOW']}"/>
        <Image resource="snow"/>
      </PartImage>
      <PartDraw x="0" y="0" width="450" height="450" name="lightning">
        <Transform target="alpha" value="({E['C']} == 9 &amp;&amp; (fract({U} / 6.3) &lt; 0.025 || (fract({U} / 6.3) &gt; 0.05 &amp;&amp; fract({U} / 6.3) &lt; 0.065))) ? 175 : 0"/>
        <Rectangle x="0" y="0" width="450" height="450"><Fill color="#ffeef2ff"/></Rectangle>
      </PartDraw>
''' + s[end:]
    s = s.replace(NF, E['N'])
    i = s.index('>', s.index('<Scene')) + 1; s = s[:i] + '\n' + E['REFS'] + s[i:]
    s = s.replace(T, '\0')
    def fix(mt):
        v = mt.group(2)
        if '\0' in v:
            v = v.replace('\0', E['TP'] if STORY.search(v.replace('\0', 't')) else E['U'])
        return f'target="{mt.group(1)}" value="{v}"'
    s = re.sub(r'target="(\w+)" value="([^"]*)"', fix, s)
    assert '\0' not in s
    return s, E
