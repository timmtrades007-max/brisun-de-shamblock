"""Cut the Shamblock reels from the vertical brand frames."""
import math
import random
import struct
import subprocess
import wave
from pathlib import Path

ROOT = Path(r"c:\Users\timme\Downloads\_Sorted\08_Project_Folders\brisun-de-shunblock")
ASSETS = Path(r"C:\Users\timme\.cursor\projects\c-Users-timme-Downloads\assets")
IMG = ROOT / "images"
VID = ROOT / "videos"
TMP = VID / "_tmp"
FONT = "c\\\\:/Users/timme/Downloads/_Sorted/08_Project_Folders/brisun-de-shunblock/fonts/bahnschrift.ttf"
FPS = 30
W, H = 1080, 1920

for folder in (IMG, VID, TMP):
    folder.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "carry": ASSETS / "brisun-reel-carry.jpg",
    "impact": ASSETS / "brisun-reel-impact.jpg",
    "bomb": ASSETS / "brisun-reel-bomb.jpg",
    "logo": IMG / "brisun-logo.jpg",
    "product": IMG / "brisun-post-product-tee.jpg",
    "lab": IMG / "brisun-post-lab-range.jpg",
}


def run(args):
    print(">", " ".join(str(a) for a in args[:6]), "...")
    subprocess.run(args, check=True)


def shot(src, dest, frames, zoom, x_bias, y_bias, texts):
    """texts: list of (text, size, y_frac, start, end)."""
    z0, z1 = zoom
    span = max(frames - 1, 1)
    draws = []
    for text, size, y_frac, start, end in texts:
        draws.append(
            "drawtext=fontfile=%s:text='%s':fontsize=%d:fontcolor=white:"
            "borderw=0:shadowcolor=black@0.55:shadowx=0:shadowy=3:"
            "x=(w-text_w)/2:y=h*%.3f:"
            "alpha='if(lt(t,%.2f),0,if(lt(t,%.2f),(t-%.2f)/%.2f,"
            "if(lt(t,%.2f),1,if(lt(t,%.2f),(%.2f-t)/%.2f,0))))'"
            % (
                FONT, text, size, y_frac,
                start, start + 0.25, start, 0.25,
                end - 0.3, end, end, 0.3,
            )
        )
    chain = ",".join(
        [
            "scale=1620:2880:force_original_aspect_ratio=increase:flags=lanczos",
            "crop=1620:2880",
            "zoompan=z='%0.3f+(%0.3f-%0.3f)*on/%d':x='(iw-iw/zoom)*%0.3f':y='(ih-ih/zoom)*%0.3f':d=%d:s=%dx%d:fps=%d"
            % (z0, z1, z0, span, x_bias, y_bias, frames, W, H, FPS),
            "eq=contrast=1.06:saturation=1.08:brightness=0.01",
            "vignette=PI/4.5",
            "noise=alls=3:allf=t",
            *draws,
            "format=yuv420p",
        ]
    )
    run(
        [
            "ffmpeg", "-y", "-loop", "1", "-i", str(src),
            "-vf", chain,
            "-frames:v", str(frames),
            "-an",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p",
            str(dest),
        ]
    )


def end_card(dest, frames, kicker, title):
    fade = 0.35
    end = frames / FPS
    chain = (
        "[1:v]scale=620:620:flags=lanczos[lg];"
        "[0:v][lg]overlay=(W-w)/2:(H-h)/2-120,"
        "drawtext=fontfile=%s:text='%s':fontsize=28:fontcolor=0xc6a36a:"
        "x=(w-text_w)/2:y=h*0.72:alpha='if(lt(t,%.2f),0,if(lt(t,%.2f),(t-%.2f)/%.2f,1))',"
        "drawtext=fontfile=%s:text='%s':fontsize=54:fontcolor=white:"
        "x=(w-text_w)/2:y=h*0.76:alpha='if(lt(t,%.2f),0,if(lt(t,%.2f),(t-%.2f)/%.2f,1))',"
        "format=yuv420p"
        % (FONT, kicker, 0.25, 0.25 + fade, 0.25, fade,
           FONT, title, 0.45, 0.45 + fade, 0.45, fade)
    )
    run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=0x051C3C:s=%dx%d:r=%d:d=%0.3f" % (W, H, FPS, end),
            "-i", str(SOURCES["logo"]),
            "-filter_complex", chain,
            "-frames:v", str(frames),
            "-an",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p",
            str(dest),
        ]
    )


def flash(dest, frames=3):
    run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=white:s=%dx%d:r=%d:d=%0.3f" % (W, H, FPS, frames / FPS),
            "-frames:v", str(frames),
            "-an",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p",
            str(dest),
        ]
    )


def concat(parts, dest):
    listing = TMP / "list.txt"
    listing.write_text("".join("file '%s'\n" % p.as_posix() for p in parts), encoding="utf-8")
    run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
            "-c", "copy", str(dest),
        ]
    )


def duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        text=True,
    )
    return float(out.strip())


def write_score(path, dur, hits):
    sr = 48000
    n = int(sr * dur)
    buf = [0.0] * n
    rng = random.Random(11)

    def add(i, v):
        if 0 <= i < n:
            buf[i] += v

    air = 0.0
    for i in range(n):
        t = i / sr
        env = min(1.0, t / 0.8) * min(1.0, max(0.0, (dur - t) / 0.8))
        buf[i] += env * 0.04 * math.sin(2 * math.pi * 46 * t)
        buf[i] += env * 0.018 * math.sin(2 * math.pi * 92 * t + 0.4)
        white = rng.uniform(-1, 1)
        air = 0.985 * air + 0.015 * white
        buf[i] += env * 0.03 * air

    for t0, amp in hits:
        length = int(sr * 0.5)
        for k in range(length):
            t = k / sr
            v = amp * math.exp(-6.5 * t) * math.sin(2 * math.pi * 52 * t)
            v += amp * 0.45 * math.exp(-18 * t) * math.sin(2 * math.pi * 160 * t)
            if k < int(sr * 0.01):
                v += amp * 0.28 * rng.uniform(-1, 1)
            add(int(t0 * sr) + k, v)
        # short rise into the hit
        rise = int(sr * 0.55)
        start = int(t0 * sr) - rise
        for k in range(rise):
            p = k / rise
            add(start + k, amp * 0.05 * (p ** 2) * rng.uniform(-1, 1))

    peak = max(abs(s) for s in buf) or 1
    scale = 0.82 / peak
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sr)
        frames = b"".join(struct.pack("<h", max(-32767, min(32767, int(s * scale * 32767)))) for s in buf)
        handle.writeframes(frames)


def mux(video, score, dest):
    run(
        [
            "ffmpeg", "-y", "-i", str(video), "-i", str(score),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", "-shortest",
            str(dest),
        ]
    )


def build_bomb():
    carry = TMP / "carry.mp4"
    impact = TMP / "impact.mp4"
    bomb = TMP / "bomb.mp4"
    end = TMP / "end.mp4"
    white = TMP / "flash.mp4"
    silent = TMP / "bomb-silent.mp4"
    shot(
        SOURCES["carry"], carry, 120, (1.02, 1.14), 0.50, 0.16,
        [("320", 140, 0.74, 0.45, 3.5), ("CARRY", 36, 0.84, 0.9, 3.6)],
    )
    shot(
        SOURCES["impact"], impact, 78, (1.05, 1.20), 0.38, 0.46,
        [("CENTER FACE", 52, 0.80, 0.2, 2.4)],
    )
    shot(
        SOURCES["bomb"], bomb, 138, (1.03, 1.12), 0.50, 0.42,
        [("FINISH HIGH", 58, 0.78, 0.45, 4.2)],
    )
    end_card(end, 90, "SHAMBLOCK", "BIG DRIVES. FULL SUN.")
    flash(white, 2)
    concat([carry, white, impact, bomb, end], silent)
    dur = duration(silent)
    score = TMP / "bomb.wav"
    write_score(score, dur, [(120 / FPS, 1.0), ((120 + 2 + 78) / FPS, 0.35)])
    mux(silent, score, VID / "the-bomb.mp4")


def build_coat():
    product = TMP / "product.mp4"
    lab = TMP / "lab.mp4"
    end = TMP / "coat-end.mp4"
    silent = TMP / "coat-silent.mp4"
    shot(
        SOURCES["product"], product, 120, (1.04, 1.14), 0.34, 0.48,
        [("BOMB SPF 50", 52, 0.90, 0.4, 3.6)],
    )
    shot(
        SOURCES["lab"], lab, 105, (1.03, 1.12), 0.55, 0.48,
        [("UV 6.2", 72, 0.86, 0.35, 3.1)],
    )
    end_card(end, 75, "ON BEFORE THE SWING", "THEN HIT IT.")
    concat([product, lab, end], silent)
    dur = duration(silent)
    score = TMP / "coat.wav"
    write_score(score, dur, [(0.15, 0.25)])
    mux(silent, score, VID / "the-coat.mp4")


if __name__ == "__main__":
    for name in ("carry", "impact", "bomb"):
        target = IMG / ("brisun-reel-%s.jpg" % name)
        if not target.exists():
            target.write_bytes(SOURCES[name].read_bytes())
    build_bomb()
    build_coat()
    print("done", VID / "the-bomb.mp4", VID / "the-coat.mp4")
