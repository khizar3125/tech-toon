"""Frame-by-frame rigged animation engine for the tech cartoon.

Rig features:
  - jaw-morph lip-sync (audio amplitude drives mouth open/close)
  - periodic blinking (eye-band squash)
  - head bob + tilt synced to speech energy
  - full-body pose swaps + idle sway for gestures
  - parallax background (slow zoom/pan)
  - meme sticker pop-in with overshoot + shake
  - camera FX: zoom punch, shake, flash
  - speech bubble + Hinglish text, "Wait for End" pill
"""
from pathlib import Path
import json, math, random
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SPR = ROOT / "assets" / "sprites"
WORK = ROOT / ".work"
STORY = json.load(open(ROOT / "story.json"))
ENV = json.load(open(WORK / "amplitude.json"))
W, H = STORY["width"], STORY["height"]
FPS = STORY.get("fps", 24)

FONTS = {
    "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "sans": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
}
def font(size, key="bold"):
    return ImageFont.truetype(FONTS[key], size)

# y fraction above which face stays rigid; below = jaw region
JAW = {"face2_happy":0.845,"face2_sad":0.85,"face2_angry":0.85,
       "face2_shock":0.85,"face2_think":0.85,"face_happy":0.78,
       "face_laugh":0.80,"face_angry":0.85,"face_sad":0.85,"face_shock":0.85}
# eye band (top,bottom) fraction for blink
EYES = {"face2_happy":(0.60,0.74),"face2_sad":(0.60,0.75),"face2_angry":(0.60,0.75),
        "face2_shock":(0.61,0.75),"face2_think":(0.60,0.75),"face_happy":(0.56,0.72),
        "face_laugh":(0.58,0.74),"face_angry":(0.60,0.75),"face_sad":(0.60,0.75),
        "face_shock":(0.60,0.75)}

_CACHE = {}
def sprite(name):
    if name not in _CACHE:
        _CACHE[name] = Image.open(SPR / f"{name}.png").convert("RGBA")
    return _CACHE[name]

# ---------------- rig primitives ----------------

def jaw_morph(base, openness):
    """Stretch lower face vertically: 0=closed mouth, 1=wide open."""
    w, h = base.size
    top = int(h * JAW.get(base.name, 0.845))
    upper = base.crop((0, 0, w, top))
    lower = base.crop((0, top, w, h))
    factor = 0.42 + 0.95 * max(0.0, min(1.0, openness))
    nh = max(4, int(lower.height * factor))
    lower = lower.resize((w, nh), Image.Resampling.BILINEAR)
    canvas = Image.new("RGBA", (w, top + nh), (0, 0, 0, 0))
    canvas.paste(upper, (0, 0))
    canvas.paste(lower, (0, top))
    return canvas

def blink(base, amount, face_name=None):
    """Squash eye band to simulate blinking (amount 0=open,1=closed)."""
    if amount <= 0.02:
        return base
    w, h = base.size
    band = EYES.get(face_name or getattr(base, "name", ""), (0.60, 0.75))
    y0, y1 = int(h * band[0]), int(h * band[1])
    upper = base.crop((0, 0, w, y0))
    eyes = base.crop((0, y0, w, y1))
    lower = base.crop((0, y1, w, h))
    nh = max(2, int(eyes.height * (1 - 0.9 * amount)))
    eyes = eyes.resize((w, nh), Image.Resampling.BILINEAR)
    canvas = Image.new("RGBA", (w, upper.height + nh + lower.height), (0, 0, 0, 0))
    canvas.paste(upper, (0, 0))
    canvas.paste(eyes, (0, upper.height))
    canvas.paste(lower, (0, upper.height + nh))
    return canvas

def rotate_scale(img, angle, scale):
    if abs(angle) < 0.1 and abs(scale - 1) < 0.01:
        return img
    out = img.rotate(angle, Image.Resampling.BICUBIC, expand=True)
    if scale != 1:
        nw, nh = max(1, int(out.width*scale)), max(1, int(out.height*scale))
        out = out.resize((nw, nh), Image.Resampling.LANCZOS)
    return out

def round_rect(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def draw_bubble(canvas, text, max_w=880):
    """Speech bubble at top with wrapped Hinglish text."""
    d = ImageDraw.Draw(canvas)
    f = font(58, "bold")
    # wrap
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= max_w:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    lh = 72
    pad = 34
    tw = max([d.textlength(l, font=f) for l in lines] or [0])
    bw = int(tw) + pad*2
    bh = lh*len(lines) + pad*2 - 10
    bx = (W - bw)//2
    by = 150
    # shadow + bubble
    round_rect(d, [bx+6, by+8, bx+bw+6, by+bh+8], 38, (0,0,0,90))
    round_rect(d, [bx, by, bx+bw, by+bh], 38, (255,255,255,248), (60,50,55,255), 5)
    # tail
    tx = bx + bw//2
    d.polygon([(tx-34,by+bh-4),(tx+34,by+bh-4),(tx,by+bh+52)], fill=(255,255,255,248))
    d.line([(tx-34,by+bh-4),(tx,by+bh+52),(tx+34,by+bh-4)], fill=(60,50,55,255), width=5)
    for i, l in enumerate(lines):
        x = (W - d.textlength(l, font=f))/2
        y = by + pad - 6 + i*lh
        # stroke
        d.text((x+2,y+2), l, font=f, fill=(0,0,0,90))
        d.text((x,y), l, font=f, fill=(28,22,26,255))
    return by+bh

def draw_pill(canvas):
    d = ImageDraw.Draw(canvas)
    f = font(44, "bold")
    txt = "Wait for End  ***"
    tw = d.textlength(txt, font=f)
    bw, bh = int(tw)+72, 92
    bx, by = (W-bw)//2, H-150
    round_rect(d, [bx+5,by+7,bx+bw+5,by+bh+7], 46, (0,0,0,120))
    round_rect(d, [bx,by,bx+bw,by+bh], 46, (18,16,20,238), (255,255,255,220), 3)
    d.text(((W-tw)/2, by+18), txt, font=f, fill=(255,255,255,255))

def overlay_gradient(canvas, strength=0.35):
    d = ImageDraw.Draw(canvas)
    for i in range(260):
        a = int(strength*255*(i/260)**1.6)
        d.line([(0,H-260+i),(W,H-260+i)], fill=(0,0,0,a))

# ---------------- scene composition ----------------

def compose_line(idx, line):
    """Yield (frame_image, duration_frames) for one dialogue line."""
    dur = line["duration"]
    nframes = max(1, int(dur*FPS))
    env = ENV.get(str(line["id"]), [0.02]*nframes)
    face_name = line["face"]
    body_name = line.get("body", "body_1")
    bg_name = "bg_" + line.get("bg", "living")
    meme = line.get("meme")
    fx = line.get("fx", "pop")

    bg = sprite(bg_name)
    face = sprite(face_name)
    body = sprite(body_name)
    face.name = face_name   # tag for JAW/EYES lookup

    rng = random.Random(line["id"]*7919)
    blink_times = set(rng.sample(range(10, nframes-5), k=max(2, nframes//55)))
    for bt in list(blink_times):
        blink_times.update([bt-1, bt, bt+1])

    meme_img = sprite(meme) if meme else None

    prev_open = 0.0
    for fi in range(nframes):
        t = fi/FPS
        amp = env[fi] if fi < len(env) else 0.02
        # normalize amplitude to mouth openness
        target = max(0.0, min(1.0, amp*4.6))
        openness = prev_open*0.45 + target*0.55   # smooth
        prev_open = openness

        # ---- camera FX ----
        canvas = Image.new("RGBA", (W, H), (255,255,255,255))
        zoom = 1.0; shakex = shakey = 0
        if fx == "zoom":
            zoom = 1.0 + 0.06*(fi/max(1,nframes))
        elif fx == "punch":
            zoom = 1.08 if fi < nframes*0.18 else 1.0
        elif fx == "shake":
            if fi % 3 == 0:
                shakex, shakey = rng.randint(-6,6), rng.randint(-5,5)
        elif fx == "flash" and fi < 4:
            zoom = 1.05
        # parallax background slow pan
        pan = int(10*math.sin(t*0.5))
        bgs = bg.resize((int(W*1.10*zoom), int(H*1.10*zoom)), Image.Resampling.LANCZOS)
        bx = (W-bgs.width)//2 + pan + shakex
        by = (H-bgs.height)//2 + shakey
        canvas.paste(bgs, (bx,by))
        overlay_gradient(canvas, 0.30)

        # ---- body (full pose) lower-left, gentle bob/sway ----
        body_h = int(H*0.52)
        bs = body.resize((int(body.width*body_h/body.height), body_h), Image.Resampling.LANCZOS)
        bob = int(9*math.sin(t*2*math.pi*1.6))
        lean = 2.2*math.sin(t*2*math.pi*0.7)
        bs = rotate_scale(bs, lean, 1.0)
        bxx = int(W*0.06) + shakex
        byy = int(H*0.44) + bob + shakey
        canvas.paste(bs, (bxx,byy), bs)

        # ---- big face (rigged talking head) right side ----
        fh = int(H*0.46)
        fr = jaw_morph(face, openness)
        bl = 1.0 if fi in blink_times else 0.0
        fr = blink(fr, bl, face_name)
        fscale = fh/fr.height
        fr = fr.resize((int(fr.width*fscale), int(fr.height*fscale)), Image.Resampling.LANCZOS)
        headbob = int(7*math.sin(t*2*math.pi*2.0 + 0.5))
        tilt = 3.0*math.sin(t*2*math.pi*0.55)
        fr = rotate_scale(fr, tilt*0.5, 1.0+0.01*openness)
        # keep face fully on canvas (clamp to right edge with small margin)
        fxx = min(W - fr.width - 18, int(W*0.46)) + shakex
        fxx = max(4, fxx)
        fyy = int(H*0.10) + headbob + shakey
        canvas.paste(fr, (fxx,fyy), fr)

        # ---- meme sticker pop ----
        if meme_img:
            entry = 0.5  # seconds
            if t < entry:
                p = t/entry
                s = 0.3 + 1.05*(1-math.cos(p*math.pi/2))  # overshoot
                ms = meme_img.resize((int(meme_img.width*s), int(meme_img.height*s)), Image.Resampling.LANCZOS)
                rot = 12*(1-p)
                ms = rotate_scale(ms, rot, 1.0)
                mx = int(W*0.44) + rng.randint(-3,3)
                my = int(H*0.30)
            else:
                ms = meme_img
                mx, my = int(W*0.44), int(H*0.30)
            canvas.paste(ms, (mx,my), ms)

        # ---- text + pills ----
        draw_bubble(canvas, line["text"])
        draw_pill(canvas)

        # ---- flash overlay (proper alpha blend) ----
        if fx == "flash" and fi < 6:
            a = int(210*(1-fi/6))
            overlay = Image.new("RGBA", (W,H), (255,255,255,a))
            canvas = Image.alpha_composite(canvas, overlay)

        yield canvas.convert("RGB")

# ---------------- timeline ----------------

def build_timeline():
    """Return ordered list of line dicts with absolute start frames."""
    tl = []
    cur = 0
    for line in STORY["lines"]:
        nframes = max(1, int(line["duration"]*FPS))
        tl.append({"line":line, "start":cur, "nframes":nframes})
        cur += nframes
    return tl, cur

if __name__ == "__main__":
    import sys
    tl, total = build_timeline()
    print(f"timeline: {len(tl)} lines, {total} frames, {total/FPS:.1f}s")
    # render a single test frame from line 2
    f = next(compose_line(2, STORY["lines"][1]))
    f.save(WORK/"test_frame.jpg", quality=92)
    print("test frame saved")
