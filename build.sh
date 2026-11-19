#!/bin/bash
# Aurora Sweep (Watch Face Format 4, no code) -> dist/aurora-sweep.apk
# Assets: python3 gen_assets.py && python3 gen_assets2.py ; XML: python3 patch_xml.py
# Needs aapt2, zipalign, apksigner (Android build-tools), an android.jar (API 34+) and a JDK.
set -e
P=$(cd "$(dirname "$0")" && pwd)
[ -f "$P/.buildenv" ] && . "$P/.buildenv"   # optional local overrides (gitignored)
BT=${BUILD_TOOLS:-$ANDROID_HOME/build-tools/34.0.0}
JAR=${ANDROID_JAR:-$ANDROID_HOME/platforms/android-34/android.jar}
[ -n "$JAVA_HOME" ] && export PATH=$JAVA_HOME/bin:$PATH
KS=${KEYSTORE:-$P/keys/sign.jks}; KP=${KEYSTORE_PASS_FILE:-$P/keys/sign.pass}
if [ ! -f "$KS" ]; then   # first build: create a local signing key (keep it, updates need the same key)
  mkdir -p "$(dirname "$KS")"; head -c 24 /dev/urandom | base64 | tr -d '/+=' > "$KP"
  keytool -genkeypair -keystore "$KS" -storepass "$(cat "$KP")" -alias aurora -keyalg RSA -keysize 2048 -validity 20000 -dname "CN=Aurora Sweep" >/dev/null 2>&1
fi
W=$P/build; rm -rf $W; mkdir -p $W $P/dist
sed "s/VC/$(date +%s | cut -c3-)/g" $P/source/AndroidManifest.xml > $W/AndroidManifest.xml
cd $W
$BT/aapt2 compile --dir $P/source/res -o res.zip
$BT/aapt2 link -o un.apk -I $JAR --manifest AndroidManifest.xml res.zip
$BT/zipalign -f 4 un.apk al.apk
$BT/apksigner sign --ks "$KS" --ks-pass file:"$KP" --out $P/dist/aurora-sweep.apk al.apk
rm -rf $W $P/dist/*.idsig; echo "ok $P/dist/aurora-sweep.apk ($(du -h $P/dist/aurora-sweep.apk | cut -f1))"
