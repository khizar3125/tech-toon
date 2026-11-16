"""Synthesize per-line TTS with distinct voices and return durations."""
from pathlib import Path
import subprocess, json, re

ROOT = Path(__file__).resolve().parents[1]
AUD = ROOT / "assets" / "audio"
AUD.mkdir(parents=True, exist_ok=True)

def synth(text, voice, rate="+0%", pitch="+0Hz", out=None):
    out = out or AUD / "tmp.mp3"
    cmd = ["edge-tts", "--voice", voice, f"--rate={rate}", f"--pitch={pitch}",
           "--text", text, "--write-media", str(out)]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0 or not out.exists() or out.stat().st_size < 500:
        raise RuntimeError(f"TTS failed: {r.stderr.decode()[-200:]}")
    return out

def duration(path):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                        "-of","csv=p=0",str(path)],capture_output=True,text=True)
    return float(r.stdout.strip())

if __name__ == "__main__":
    story = json.load(open(ROOT/"story.json"))
    meta = []
    for ln in story["lines"]:
        p = AUD / f"line_{ln['id']:02d}.mp3"
        synth(ln["text"], ln["voice"], ln.get("rate","+0%"), ln.get("pitch","+0Hz"), p)
        d = duration(p)
        ln["duration"] = round(d,3)
        meta.append({"id":ln["id"],"duration":d})
        print(f"  line {ln['id']:02d}: {d:.2f}s  [{ln['speaker']}]")
    json.dump(meta, open(ROOT/".work"/"audio_meta.json","w"), indent=2)
    print("TOTAL:", round(sum(m['duration'] for m in meta),2),"s")
