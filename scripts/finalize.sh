#!/bin/bash
# Finalize: mux audio into rendered video, publish to GitHub release.
set -e
cd "$(dirname "$0")/.."
TOKEN="${GITHUB_TOKEN:?Set GITHUB_TOKEN env var before running}"
REPO="${GITHUB_REPO:-khizar3125/tech-toon}"

echo "=== 1. Mux audio ==="
ffmpeg -y -loglevel error -i output/tech_cartoon.mp4 -i output/voice.wav \
  -c:v copy -c:a aac -b:a 192k -shortest output/tech_cartoon_final.mp4
ffprobe -v error -show_entries format=duration -show_entries stream=codec_type,codec_name,width,height \
  -of default=noprint_wrappers=1 output/tech_cartoon_final.mp4

echo "=== 2. Git commit & push ==="
rm -rf .work/frames
if [ ! -d .git ]; then git init -q; fi
git add -A
git -c user.email="khizar3125@users.noreply.github.com" -c user.name="khizar3125" \
  commit -q -m "Tech cartoon: fully rigged animation engine + script + sprites" || true
git branch -M main
git remote remove origin 2>/dev/null || true
git remote add origin "https://${TOKEN}@github.com/${REPO}.git"
git push -q -u origin main 2>&1 | tail -3
echo "push done"

echo "=== 3. Create release ==="
RELEASE=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  https://api.github.com/repos/${REPO}/releases \
  --data-binary @release_payload.json)
echo "$RELEASE" | python3 -c "import json,sys; d=json.load(sys.stdin); print('tag:',d.get('tag_name'),'id:',d.get('id'),'msg:',d.get('message',''))"
RID=$(curl -s -H "Authorization: Bearer $TOKEN" https://api.github.com/repos/${REPO}/releases | python3 -c "import json,sys; print(json.load(sys.stdin)[0]['id'])")

echo "=== 4. Upload MP4 ==="
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: video/mp4" \
  --data-binary @output/tech_cartoon_final.mp4 \
  "https://uploads.github.com/repos/${REPO}/releases/${RID}/assets?name=tech_cartoon_final.mp4" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('asset:',d.get('name'),'size:',d.get('size'),'url:',d.get('browser_download_url'),'msg:',d.get('message',''))"

echo "=== DONE ==="
