"""Render all animation frames to PNG sequence, then encode to MP4 with ffmpeg."""
from pathlib import Path
import subprocess, sys, time
sys.path.insert(0, str(Path(__file__).resolve().parent))
import animate

ROOT = animate.ROOT
FRAMES = ROOT / ".work" / "frames"
FRAMES.mkdir(parents=True, exist_ok=True)
FPS = animate.FPS

def main():
    import os
    tl, total = animate.build_timeline()
    # resume support: find first missing frame
    start = 0
    while (FRAMES / f"{start:05d}.png").exists() and start < total:
        start += 1
    print(f"Rendering {total} frames ({total/FPS:.1f}s) from frame {start} ...", flush=True)
    t0 = time.time()
    idx = start
    for item in tl:
        line = item["line"]
        item_end = item["start"] + item["nframes"]
        if item_end <= start:
            continue
        # compose_line yields frames for this line; skip ones before resume point
        for fno, frame in enumerate(animate.compose_line(item["start"], line)):
            abs_idx = item["start"] + fno
            if abs_idx < start:
                continue
            frame.save(FRAMES / f"{abs_idx:05d}.png", compress_level=1)
            idx = abs_idx + 1
            if idx % 120 == 0:
                el = time.time()-t0
                print(f"  {idx}/{total} frames  {el:.0f}s elapsed  eta {el/max(1,(idx-start))*(total-idx):.0f}s", flush=True)
    print(f"Frames done in {time.time()-t0:.0f}s", flush=True)

    # encode video
    out = ROOT / "output" / "tech_cartoon.mp4"
    out.parent.mkdir(exist_ok=True)
    cmd = ["ffmpeg","-y","-loglevel","error","-framerate",str(FPS),
           "-i",str(FRAMES/"%05d.png"),"-c:v","libopenh264","-b:v","6M",
           "-pix_fmt","yuv420p","-r",str(FPS),str(out)]
    subprocess.run(cmd, check=True)
    print("VIDEO:", out, out.stat().st_size, "bytes", flush=True)

if __name__ == "__main__":
    main()
