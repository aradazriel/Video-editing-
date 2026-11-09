"""Beat-synced vertical (9:16) motorcycle edit to AC/DC - Thunderstruck.

Usage: python3 edit.py <src_dir> <out_dir>
src_dir must hold the GoPro clips and song.mp3 (see README).
Output: edit.mp4 (song only).
"""
import os
import subprocess
import sys

SRC, OUT = sys.argv[1], sys.argv[2]
TMP = os.path.join(OUT, "shots")
os.makedirs(TMP, exist_ok=True)

FPS = 30
W, H = 1080, 1920
BEAT = 60 / 133.15          # song tempo
SONG_START = 19.98          # riff build-up; drums hit at beat 21, full band at beat 36

# Each shot covers beats [b0, b1) of the song. The source moment `peak` lands
# exactly on song beat `pb`, so the interesting moment hits on the beat.
# speed < 1 = slow motion. fx: f = white flash, p = zoom punch on the cut.
# (clip, peak sec, peak beat, b0, b1, speed, fx)
SHOTS = [
    # intro riff
    ("GX011602",    0.5,  0,  0,  8, 1.0, ""),    # open trail
    ("GX011601",    3.3, 13,  8, 15, 1.0, "p"),   # forest single, gas on beat
    ("GX011593",    3.4, 19, 15, 21, 1.0, "p"),   # rocky climb
    # drums hit
    ("GX011605",    2.25, 22, 21, 24, 1.0, "f"),  # big gas
    ("GX011602",   13.0, 24, 24, 36, 1.0, "p"),   # transition: speed + curves
    # full band
    ("GX011609",    5.3, 38, 36, 43, 0.6, "f"),   # friend over the log, slow
    ("GX011593",    5.1, 45, 43, 51, 1.0, "p"),   # gas on the rocks + cow
    ("GX011602",   38.2, 53, 51, 59, 1.0, "p"),   # transition: winding descent
    ("GX011605_1",  3.0, 63, 59, 67, 1.0, "p"),   # chasing the rider
    ("GX011601",    5.75, 70, 67, 71, 1.0, "p"),  # forest single, gas
    ("GX011602",   28.1, 72, 71, 83, 1.0, "p"),   # transition: speed
    ("GX011602",    4.2, 83, 83, 93, 1.0, "p"),   # outro
]

# Zoom in a little and keep the top of the frame: more trail, less handlebar.
ZOOM = 1.12
TOP = 0.25  # 0 = keep the very top, 0.5 = centered


def run(cmd):
    subprocess.run(cmd, check=True)


def render_shot(i, clip, start, frames, speed, fx):
    dur = frames / FPS
    zoom = f"{ZOOM}"
    if "p" in fx or "f" in fx:
        zoom += "+0.12*max(0\\,1-t/0.25)"
    vf = [
        f"setpts=(PTS-STARTPTS)/{speed}",
        f"crop=ih*9/16:ih:(iw-ih*9/16)/2:0",
        f"scale=w='{W}*({zoom})':h=-2:eval=frame",
        f"crop={W}:{H}:(iw-{W})/2:(ih-{H})*{TOP}",
        f"fps={FPS}",
        "eq=contrast=1.1:saturation=1.2:gamma=0.97",
        "colorbalance=rm=0.04:bm=-0.04",
        "format=yuv420p",
    ]
    if "f" in fx:
        vf.append("fade=t=in:st=0:d=0.3:color=white")
    out = os.path.join(TMP, f"{i:02d}.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{dur * speed + 0.1:.3f}",
         "-i", os.path.join(SRC, clip + ".MP4"), "-an", "-map", "0:v",
         "-vf", ",".join(vf), "-frames:v", str(frames),
         "-c:v", "libx264", "-preset", "fast", "-crf", "16", out])
    return out


def main():
    parts = []
    for i, (clip, peak, pb, b0, b1, speed, fx) in enumerate(SHOTS):
        start = peak - (pb - b0) * BEAT * speed
        f0, f1 = round(b0 * BEAT * FPS), round(b1 * BEAT * FPS)
        end = start + (f1 - f0) / FPS * speed
        print(f"shot {i:02d} {clip:11s} src {start:5.2f}-{end:5.2f}  out {f0 / FPS:5.2f}-{f1 / FPS:5.2f}")
        assert start >= 0, f"shot {i} starts before the clip"
        parts.append(render_shot(i, clip, start, f1 - f0, speed, fx))
    total = round(SHOTS[-1][4] * BEAT * FPS) / FPS

    lst = os.path.join(TMP, "list.txt")
    with open(lst, "w") as fh:
        fh.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
         "-i", os.path.join(SRC, "song.mp3"),
         "-map", "0:v", "-map", "1:a",
         "-vf", f"fade=t=in:st=0:d=0.4,fade=t=out:st={total - 1.2:.3f}:d=1.2",
         "-af", f"atrim={SONG_START}:{SONG_START + total:.3f},asetpts=PTS-STARTPTS,"
                f"afade=t=in:d=0.3,afade=t=out:st={total - 2:.3f}:d=2",
         "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-maxrate", "12M", "-bufsize", "24M",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest",
         os.path.join(OUT, "edit.mp4")])
    print(f"done: {total:.2f}s")


if __name__ == "__main__":
    main()
