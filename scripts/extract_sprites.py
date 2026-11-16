"""Extract clean transparent PNG sprites from the source asset sheets.
Clips are defined in ORIGINAL source pixel coordinates.
"""
from pathlib import Path
from PIL import Image
import io, sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "source"
OUT = ROOT / "assets" / "sprites"
OUT.mkdir(parents=True, exist_ok=True)

def sheet(n):
    return Image.open(SRC / f"asset_{n}.jpg").convert("RGB")

def save_crop(img, box, name, target_h=900):
    c = img.crop(box)
    # upscale for cleaner rembg matting
    scale = max(1, target_h / max(c.height, 1))
    c = c.resize((int(c.width*scale), int(c.height*scale)), Image.Resampling.LANCZOS)
    buf = io.BytesIO(); c.save(buf, format="PNG"); buf.seek(0)
    try:
        from rembg import remove, new_session
        session = getattr(save_crop, "_s", None)
        if session is None:
            session = new_session("u2netp")
            save_crop._s = session
        rgba = remove(buf.getvalue(), session=session, alpha_matting=True,
                      alpha_matting_foreground_threshold=240,
                      alpha_matting_background_threshold=15,
                      alpha_matting_erode_size=6)
        out = Image.open(io.BytesIO(rgba)).convert("RGBA")
    except Exception as e:
        print("  rembg fail", name, e)
        out = c.convert("RGBA")
    # trim transparent border
    bbox = out.getbbox()
    if bbox:
        out = out.crop(bbox)
    out.save(OUT / f"{name}.png")
    print(f"  {name}: {out.size}")

a3 = sheet(3)
# black hoodie full-body poses (from c_poses3c analysis, orig y ~375-605)
poses = {
 "body_1": (5, 375, 100, 605),
 "body_2": (110, 375, 208, 605),
 "body_3": (212, 375, 302, 605),
 "body_4": (308, 375, 400, 605),
 "body_5": (400, 375, 497, 605),
 "body_6": (497, 375, 594, 605),
}
# expression heads from asset_3 (top-right), single character, blue collar
expr3 = {
 "face_happy":  (980, 38, 1078, 140),
 "face_laugh":  (1078, 38, 1176, 140),
 "face_shock":  (1176, 38, 1278, 140),
 "face_angry":  (1278, 38, 1378, 140),
 "face_sad":    (1378, 38, 1478, 140),
}
# expression heads from asset_6
a6 = sheet(6)
expr6 = {
 "face2_happy": (790, 35, 872, 140),
 "face2_sad":   (875, 35, 957, 140),
 "face2_angry": (960, 35, 1042, 140),
 "face2_shock": (1045, 35, 1127, 140),
 "face2_think": (1130, 35, 1212, 140),
}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all","bodies"):
        print("BODIES"); [save_crop(a3,b,n) for n,b in poses.items()]
    if which in ("all","faces"):
        print("FACES a3"); [save_crop(a3,b,n) for n,b in expr3.items()]
        print("FACES a6"); [save_crop(a6,b,n) for n,b in expr6.items()]

# ---- backgrounds (plain rectangular crops, no rembg) ----
def save_bg(img, box, name):
    c = img.crop(box)
    c = c.resize((1080, 1920), Image.Resampling.LANCZOS)
    c.save(OUT / f"{name}.png")
    print(f"  {name}: {c.size}")

BACKGROUNDS = {
 "bg_living": (10, 370, 207, 477),
 "bg_street": (413, 482, 593, 597),
 "bg_garden": (7, 482, 207, 597),
 "bg_school": (213, 482, 407, 597),
}

# ---- meme stickers (rembg) ----
a5 = sheet(5)
MEMES = {
 "wow":  (1195, 62, 1330, 175),
 "lol":  (1330, 62, 1445, 175),
 "boom": (1445, 62, 1536, 175),
 "haha": (1195, 170, 1330, 260),
}
