"""Concatenate voice lines with per-line durations rounded to exact video frames.
This keeps audio frame-aligned with the rendered animation timeline.
"""
from pathlib import Path
import json, subprocess

ROOT = Path(__file__).resolve().parents[1]
AUD = ROOT/"assets"/"audio"
WORK = ROOT/".work"
STORY = json.load(open(ROOT/"story.json"))
FPS = STORY.get("fps",24)

def main():
    # Each line occupies round(duration*FPS) frames in the video.
    # Pad/trim each mp3 to exactly that many frames, then concatenate.
    segs=[]
    for ln in STORY["lines"]:
        lid=ln["id"]; nfr=max(1,int(ln["duration"]*FPS)); sec=nfr/FPS
        src=AUD/f"line_{lid:02d}.mp3"; tmp=WORK/f"seg_{lid:02d}.wav"
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(src),
                        "-af",f"apad=pad_dur={sec}","-t",f"{sec:.6f}",
                        "-ar","48000","-ac","2","-c:a","pcm_s16le",str(tmp)],check=True)
        segs.append(tmp)
    listf=WORK/"concat_seg.txt"
    listf.write_text("\n".join(f"file '{s}'" for s in segs)+"\n")
    out=ROOT/"output"/"voice.wav"
    out.parent.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0",
                    "-i",str(listf),"-c:a","pcm_s16le",str(out)],check=True)
    nframes=sum(int(l["duration"]*FPS) for l in STORY["lines"])
    total=nframes/FPS
    print("audio:",out,out.stat().st_size,"bytes",f"duration {total:.3f}s ({nframes} frames)")
    json.dump({"audio_duration":total,"frames":nframes},open(WORK/"audio_total.json","w"))

if __name__=="__main__":
    main()
