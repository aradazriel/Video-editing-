"""Beat-synced vertical (9:16) motorcycle edit to AC/DC - Thunderstruck.

Usage: python3 edit.py <src_dir> <out_dir>
src_dir must hold the GoPro clips and song.mp3 (see README).
Outputs: edit_music.mp4 (song + engine) and edit_engine.mp4 (engine only).
"""
import os
import subprocess
import sys

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
TMP = os.path.join(OUT, "shots")
os.makedirs(TMP, exist_ok=True)

FPS = 30
W, H = 1080, 1920
BEAT = 60 / 133.15          # song tempo
SONG_START = 19.98          # riff build-up; drums hit at +9.46s, full band at +16.2s
ENGINE_VOL = 0.30           # engine level under the song

# (clip, source start sec, length in beats, speed, effects, crop center 0..1)
# effects: f = white flash, p = zoom punch-in, s = shake
SHOTS = [
    # intro riff - build tension
    ("GX011602",   0.0, 4, 1.0, "",    0.5),
    ("GX011593",   0.5, 4, 1.0, "p",   0.5),
    ("GX011605_1", 0.0, 4, 1.0, "p",   0.5),
    ("GX011593",   5.3, 4, 1.0, "p",   0.5),   # cows on the trail
    ("GX011609",   4.6, 2, 1.0, "p",   0.55),  # friend over the log
    ("GX011601_1", 0.0, 3, 1.0, "p",   0.5),
    # DRUMS IN - first wheelie, slow motion
    ("GX011605",   2.2, 6, 0.5, "fps", 0.5),
    ("GX011601_1", 4.9, 4, 1.0, "ps",  0.5),   # wheelie
    ("GX011601",   6.1, 3, 1.0, "ps",  0.5),   # wheelie
    ("GX011602",  28.0, 2, 1.0, "p",   0.5),
    # FULL BAND
    ("GX011602",  24.9, 6, 0.5, "fps", 0.5),   # wheelie slow-mo
    ("GX011609",   5.0, 2, 1.0, "p",   0.55),
    ("GX011593",   3.0, 2, 1.0, "p",   0.5),
    ("GX011605_1", 1.6, 2, 1.0, "p",   0.5),
    ("GX011602",  35.4, 4, 1.0, "fps", 0.5),   # wheelie
    ("GX011602",  38.2, 2, 1.0, "p",   0.5),
    ("GX011601",   3.2, 2, 1.0, "p",   0.5),
    ("GX011605_1", 3.4, 2, 1.0, "p",   0.5),
    ("GX011602",  40.0, 2, 1.0, "p",   0.5),
    ("GX011602",   8.0, 4, 1.0, "p",   0.5),
    ("GX011593",   4.0, 2, 1.0, "p",   0.5),
    ("GX011609",   2.4, 2, 1.0, "p",   0.45),
    ("GX011602",  12.0, 2, 1.0, "p",   0.5),
    ("GX011601",   8.0, 2, 1.0, "p",   0.5),
    ("GX011602",  42.9, 6, 0.5, "fps", 0.5),   # big final wheelie slow-mo
    ("GX011605",   2.2, 4, 1.0, "fs",  0.5),   # first wheelie again, full speed
    # outro
    ("GX011602",  18.0, 11, 1.0, "",   0.5),
]


def run(cmd):
    subprocess.run(cmd, check=True)


def render_shot(i, clip, start, frames, speed, fx, cx):
    dur = frames / FPS
    src_len = dur * speed + 0.1
    zoom = "1.08" if "s" in fx else "1.0"
    if "p" in fx or "f" in fx:
        zoom += "+0.18*max(0\\,1-t/0.22)"
    shake = "+14*sin(t*55)*max(0.3\\,1-t/1.5)" if "s" in fx else ""
    shake_y = "+10*cos(t*47)*max(0.3\\,1-t/1.5)" if "s" in fx else ""
    vf = [
        f"setpts=(PTS-STARTPTS)/{speed}",
        f"crop=ih*9/16:ih:(iw-ih*9/16)*{cx}:0",
        f"scale=w='{W}*({zoom})':h=-2:eval=frame",
        f"crop={W}:{H}:(iw-{W})/2{shake}:(ih-{H})/2{shake_y}",
        f"fps={FPS}",
        "eq=contrast=1.08:saturation=1.15",
        "format=yuv420p",
    ]
    if "f" in fx:
        vf.append("fade=t=in:st=0:d=0.25:color=white")
    af = f"asetpts=PTS-STARTPTS,atempo={speed},apad,atrim=0:{dur:.4f}"
    out = os.path.join(TMP, f"{i:02d}.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", f"{src_len:.3f}",
         "-i", os.path.join(SRC, clip + ".MP4"),
         "-vf", ",".join(vf), "-af", af, "-frames:v", str(frames),
         "-c:v", "libx264", "-preset", "fast", "-crf", "16",
         "-c:a", "aac", "-ar", "48000", "-ac", "2", out])
    return out


def main():
    parts, beat = [], 0
    for i, (clip, start, beats, speed, fx, cx) in enumerate(SHOTS):
        f0 = round(beat * BEAT * FPS)
        beat += beats
        f1 = round(beat * BEAT * FPS)
        print(f"shot {i:02d} {clip} @{start}s  {f0 / FPS:6.2f}-{f1 / FPS:6.2f}s")
        parts.append(render_shot(i, clip, start, f1 - f0, speed, fx, cx))
    total = round(beat * BEAT * FPS) / FPS

    lst = os.path.join(TMP, "list.txt")
    with open(lst, "w") as fh:
        fh.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
    joined = os.path.join(TMP, "joined.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
         "-c", "copy", joined])

    vfade = f"fade=t=in:st=0:d=0.4,fade=t=out:st={total - 1.2:.3f}:d=1.2"
    # engine-only version
    run(["ffmpeg", "-v", "error", "-y", "-i", joined, "-map", "0:v", "-map", "0:a", "-vf", vfade,
         "-af", f"afade=t=out:st={total - 1.2:.3f}:d=1.2",
         "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-maxrate", "12M", "-bufsize", "24M",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
         os.path.join(OUT, "edit_engine.mp4")])
    # song + engine version
    mix = (f"[1:a]atrim={SONG_START}:{SONG_START + total:.3f},asetpts=PTS-STARTPTS,"
           f"afade=t=in:d=0.3,afade=t=out:st={total - 2:.3f}:d=2[m];"
           f"[0:a]volume={ENGINE_VOL}[e];[m][e]amix=inputs=2:normalize=0,"
           f"alimiter=limit=0.95[a]")
    run(["ffmpeg", "-v", "error", "-y", "-i", joined, "-i", os.path.join(SRC, "song.mp3"),
         "-filter_complex", mix, "-map", "0:v", "-map", "[a]", "-vf", vfade,
         "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-maxrate", "12M", "-bufsize", "24M",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest",
         os.path.join(OUT, "edit_music.mp4")])
    print(f"done: {total:.2f}s")


if __name__ == "__main__":
    main()
