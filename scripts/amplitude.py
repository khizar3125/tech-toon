"""Extract per-frame loudness envelope from each voice line for lip-sync."""
from pathlib import Path
import subprocess, json, struct, math

ROOT = Path(__file__).resolve().parents[1]
AUD = ROOT / "assets" / "audio"
FPS = 24

def pcm_rms(path, fps=FPS):
    """Decode to 16-bit mono PCM at given rate and return RMS per 1/fps window."""
    rate = 24000
    raw = subprocess.run(
        ["ffmpeg","-v","error","-i",str(path),"-f","s16le","-ac","1",
         "-ar",str(rate),"-acodec","pcm_s16le","-"],
        capture_output=True).stdout
    n = len(raw)//2
    samples = struct.unpack(f"<{n}h", raw[:n*2])
    hop = rate//fps
    env = []
    for i in range(0, n, hop):
        chunk = samples[i:i+hop]
        if not chunk: break
        rms = math.sqrt(sum(s*s for s in chunk)/len(chunk))/32768.0
        env.append(rms)
    return env

def smooth(env, k=2):
    out=[]
    for i in range(len(env)):
        a=env[max(0,i-k):i+k+1]
        out.append(sum(a)/len(a))
    return out

if __name__ == "__main__":
    meta = json.load(open(ROOT/".work"/"audio_meta.json"))
    allenv={}
    for m in meta:
        e = smooth(pcm_rms(AUD/f"line_{m['id']:02d}.mp3"))
        allenv[m['id']] = [round(x,4) for x in e]
    json.dump(allenv, open(ROOT/".work"/"amplitude.json","w"))
    for k,v in allenv.items():
        mx=max(v) if v else 0
        print(f"  line {k}: {len(v)} frames, peak {mx:.3f}, mean {sum(v)/len(v):.3f}")
