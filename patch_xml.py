# Turns the original Aurora Farm watchface.xml (MIT) into Aurora Sweep. Always rebuilt from watchface.orig.xml.
import os, re
B = os.path.dirname(os.path.abspath(__file__))
import sys, json, timemodel
# usage: patch_xml.py [overrides-json]  e.g. '{"m": "600", "cond": "6"}' (fixed 10:00, rain) for testing
OV = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
src = open(f'{B}/watchface.orig.xml').read()
src, E = timemodel.apply(src, OV)
FL = E['FLIP']
W = dict(x.split(':') for x in open(f'{B}/digit_widths.txt').read().split())
def font(name, kind):
    return f'<BitmapFont name="{name}">' + ''.join(f'<Character name="{d}" resource="hr_{kind}_{d}" width="{w}" height="230"/>' for d, w in W.items()) + '</BitmapFont>'
SWEPT = '[MINUTE] * 6 + [SECOND] * 0.1'
HOUR = '[CONFIGURATION.h24] ? [HOUR_0_23] : [HOUR_1_12]'
NEXT = '[CONFIGURATION.h24] ? (([HOUR_0_23] + 1) % 24) : (([HOUR_1_12] % 12) + 1)'
head = f'''  <BitmapFonts>{font("hrSolid","s")}{font("hrLine","l")}</BitmapFonts>
  <UserConfigurations>
    <ColorConfiguration id="accent" displayName="accent_color" defaultValue="0">
      <ColorOption id="0" displayName="c_white" colors="#ffffffff"/>
      <ColorOption id="1" displayName="c_gold" colors="#ffffd98a"/>
      <ColorOption id="2" displayName="c_aurora" colors="#ff8ff0c0"/>
      <ColorOption id="3" displayName="c_lilac" colors="#ffc9b6ff"/>
      <ColorOption id="4" displayName="c_sky" colors="#ff9fd3ff"/>
    </ColorConfiguration>
    <BooleanConfiguration id="mono" displayName="sweep_mono" defaultValue="TRUE"/>
    <ListConfiguration id="dim" displayName="sweep_dim" defaultValue="0">
      <ListOption id="0" displayName="dim_none"/>
      <ListOption id="1" displayName="dim_light"/>
      <ListOption id="2" displayName="dim_medium"/>
      <ListOption id="3" displayName="dim_strong"/>
    </ListConfiguration>
    <BooleanConfiguration id="h24" displayName="format_24h" defaultValue="TRUE"/>
  </UserConfigurations>
'''
overlay = f'''    <PartDraw x="0" y="0" width="450" height="450" name="sweepMono" blendMode="SATURATION">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <Transform target="alpha" value="([CONFIGURATION.mono] ? 255 : 0) * (1 - {FL})"/>
      <Arc direction="CLOCKWISE" startAngle="0" endAngle="0.01" centerX="225" centerY="225" width="225" height="225">
        <Transform target="endAngle" value="clamp(0.01 + {SWEPT}, 0, 360)"/>
        <Stroke color="#ff808080" cap="BUTT" thickness="225"/>
      </Arc>
    </PartDraw>
    <PartDraw x="0" y="0" width="450" height="450" name="sweepShade">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <Transform target="alpha" value="([CONFIGURATION.dim] == 0 ? 0 : ([CONFIGURATION.dim] == 1 ? 110 : ([CONFIGURATION.dim] == 2 ? 170 : 225))) * (1 - {FL})"/>
      <Arc direction="CLOCKWISE" startAngle="0" endAngle="0.01" centerX="225" centerY="225" width="225" height="225">
        <Transform target="endAngle" value="clamp(0.01 + {SWEPT}, 0, 360)"/>
        <Stroke color="#ff000008" cap="BUTT" thickness="225"/>
      </Arc>
    </PartDraw>
    <Group x="0" y="0" width="450" height="450" name="ticks">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <Transform target="alpha" value="255 * (1 - {FL})"/>
      <PartDraw x="0" y="0" width="450" height="450" renderMode="MASK">
        <Arc direction="CLOCKWISE" startAngle="0" endAngle="0.01" centerX="225" centerY="225" width="225" height="225">
          <Transform target="endAngle" value="clamp(0.01 + {SWEPT}, 0, 360)"/>
          <Stroke color="#ffffffff" cap="BUTT" thickness="225"/>
        </Arc>
      </PartDraw>
      <PartImage x="0" y="0" width="450" height="450" tintColor="[CONFIGURATION.accent.0]"><Image resource="ticks"/></PartImage>
    </Group>
'''
def hourtext(fam, expr=HOUR):
    return f'<Text align="CENTER" ellipsis="FALSE"><BitmapFont family="{fam}" size="230" color="#ffffffff"><Template>%s<Parameter expression="{expr}"/></Template></BitmapFont></Text>'
clock = f'''    <PartText x="25" y="36" width="400" height="34">
      <Variant mode="AMBIENT" target="alpha" value="150"/>
      <Text align="CENTER" ellipsis="FALSE"><Font family="SYNC_TO_DEVICE" size="25" weight="SEMI_BOLD" slant="NORMAL" color="#ffffffff">
        <Template>%s  %s  %s<Parameter expression="[DAY_OF_WEEK_S]"/><Parameter expression="[DAY]"/><Parameter expression="[MONTH_S]"/></Template></Font></Text>
    </PartText>
    <PartText x="25" y="68" width="400" height="24" name="weather">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <Transform target="alpha" value="[WEATHER.IS_AVAILABLE] ? 215 : 0"/>
      <Text align="CENTER" ellipsis="TRUE"><Font family="SYNC_TO_DEVICE" size="17" weight="MEDIUM" slant="NORMAL" color="#ffffffff">
        <Template>%s°  %s<Parameter expression="[WEATHER.TEMPERATURE]"/><Parameter expression="[WEATHER.CONDITION_NAME]"/></Template></Font></Text>
    </PartText>
    <PartText x="25" y="68" width="400" height="230" name="hourLine" tintColor="[CONFIGURATION.accent.0]">
      <Transform target="alpha" value="255 * (1 - {FL})"/>
      {hourtext("hrLine")}
    </PartText>
    <Group x="0" y="0" width="450" height="450" name="hourSolid">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <Transform target="alpha" value="255 * (1 - {FL})"/>
      <PartDraw x="0" y="0" width="450" height="450" renderMode="MASK">
        <Arc direction="COUNTER_CLOCKWISE" startAngle="0" endAngle="-0.01" centerX="225" centerY="225" width="225" height="225">
          <Transform target="endAngle" value="-1 * clamp(360.01 - ({SWEPT}), 0, 360)"/>
          <Stroke color="#ffffffff" cap="BUTT" thickness="225"/>
        </Arc>
      </PartDraw>
      <PartText x="25" y="68" width="400" height="230" tintColor="[CONFIGURATION.accent.0]">
        {hourtext("hrSolid")}
      </PartText>
    </Group>
'''
flip = f'''    <Group x="0" y="0" width="450" height="450" name="flipRing" pivotX="0.5" pivotY="0.5" tintColor="[CONFIGURATION.accent.0]">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <Transform target="scaleX" value="0.05 + 0.95 * {FL}"/>
      <Transform target="scaleY" value="0.05 + 0.95 * {FL}"/>
      <Transform target="alpha" value="({FL} &gt; 0) ? 255 * (1 - {FL}) : 0"/>
      <PartImage x="0" y="0" width="450" height="450"><Image resource="ring"/></PartImage>
    </Group>
    <Group x="0" y="0" width="450" height="450" name="hourNext" pivotX="0.5" pivotY="0.4">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <Transform target="scaleX" value="1.35 - 0.35 * {FL}"/>
      <Transform target="scaleY" value="1.35 - 0.35 * {FL}"/>
      <Transform target="alpha" value="255 * {FL}"/>
      <PartText x="25" y="68" width="400" height="230" tintColor="[CONFIGURATION.accent.0]">
        {hourtext("hrSolid", NEXT)}
      </PartText>
    </Group>
'''
hand = f'''    <Group x="205" y="0" width="40" height="450" name="minuteHand" pivotX="0.5" pivotY="0.5">
      <Transform target="angle" value="{SWEPT}"/>
      <PartImage x="0" y="0" width="40" height="450" tintColor="[CONFIGURATION.accent.0]"><Image resource="min_hand"/></PartImage>
    </Group>
'''
s = src.replace('<Metadata key="CLOCK_TYPE" value="DIGITAL"/>', '<Metadata key="CLOCK_TYPE" value="ANALOG"/>')
s = s.replace('  <Scene ', head + '  <Scene ', 1)
i = s.index('    <PartAnimatedImage x="262" y="330"'); s = s[:i] + overlay + s[i:]
a = s.index('    <PartText x="27" y="84"'); b = s.index('    <Group x="0" y="0" width="450" height="450" name="stats">')
s = s[:a] + clock + s[b:]
s = s.replace('  </Scene>', flip + hand + '  </Scene>')
if 'cond' in OV:   # forced weather in tests: hide the real temperature/condition line
    s = s.replace('value="[WEATHER.IS_AVAILABLE] ? 215 : 0"', 'value="0"')
open(f'{B}/source/res/raw/watchface.xml', 'w').write(s)
print('ok', len(s))
