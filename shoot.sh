#!/bin/bash
# Dev loop: shoot.sh <overrides-json|real> <frames> <interval-s> <output-prefix>
# Builds, installs over adb, activates the face and takes screenshots (prefix0.png ...).
set -e; P=$(cd "$(dirname "$0")" && pwd); [ -f "$P/.buildenv" ] && . "$P/.buildenv"; A=${ADB:-adb}
D=${ANDROID_SERIAL:-$($A devices | awk 'NR>1 && $2=="device"{print $1; exit}')}; [ -n "$D" ] || { echo "no adb device"; exit 1; }
if [ "$1" = real ]; then python3 $P/patch_xml.py; else python3 $P/patch_xml.py "$1"; fi
$P/build.sh | tail -1
timeout 60 $A -s "$D" install -r $P/dist/aurora-sweep.apk | tail -1
PKG=$(grep -o 'package="[^"]*"' $P/source/AndroidManifest.xml | cut -d'"' -f2)
$A -s "$D" shell am broadcast -a com.google.android.wearable.app.DEBUG_SURFACE --es operation set-watchface --es watchFaceId $PKG | tail -1
$A -s "$D" shell input keyevent KEYCODE_WAKEUP; $A -s "$D" shell input keyevent KEYCODE_HOME; sleep 2; : > $4.ts
for i in $(seq 0 $(($2 - 1))); do $A -s "$D" shell input keyevent KEYCODE_WAKEUP; $A -s "$D" shell cmd statusbar collapse >/dev/null 2>&1 || true; sleep 0.6; date +%s.%N >> $4.ts; timeout 10 $A -s "$D" exec-out screencap -p > $4$i.png; sleep $3; done
echo frames ok
