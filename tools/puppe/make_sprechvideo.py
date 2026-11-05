"""Sprechtest-Vergleich mit Ton -> reference/abnahme/sprechtest_3s.mp4 (6 s, jede Seite spricht 3 s).
0-3 s: links RED-EYE-Clip mit seinem Ton, rechts wir als Standbild.
3-6 s: links RED-EYE als Standbild, rechts wir mit unserem Ton."""
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

ROOT = "C:/ProjectTikTok/studio/"
RN = ROOT + "renders/_puppe/"
CLIP = ROOT + "reference/redeye/frames/p3_54_sprechen_clip.mp4"
OUT = ROOT + "reference/abnahme/sprechtest_3s.mp4"
FONT = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 44)


def label(path, text, col, right):
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((28, 1830, 28 + right, 1896), 16, fill=(0, 0, 0, 255))
    d.text((48, 1836), text, font=FONT, fill=col)
    im.save(path)


lab_l, lab_r = RN + "sprechtest_label_l.png", RN + "sprechtest_label_r.png"
label(lab_l, "RED-EYE  P3 55 s, spricht zuerst", (255, 110, 90) + (255,), 750)
label(lab_r, "WIR  85 mm f/1,8, spricht danach", (120, 230, 140) + (255,), 770)

AUDIO = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,loudnorm=I=-14:LRA=7:TP=-1.5,aresample=48000,apad=whole_dur=3,atrim=0:3,asetpts=N/SR/TB"
flt = (
    "[0:v]scale=1080:1920:flags=lanczos,fps=30,setsar=1,tpad=stop_mode=clone:stop_duration=3,trim=duration=6,setpts=PTS-STARTPTS[l0];"
    "[1:v]fps=30,setsar=1,tpad=start_mode=clone:start_duration=3,trim=duration=6,setpts=PTS-STARTPTS[r0];"
    "[l0][3:v]overlay=0:0:eof_action=repeat[l];[r0][4:v]overlay=0:0:eof_action=repeat[r];"
    "[l][r]hstack=inputs=2,format=yuv420p[v];"
    f"[0:a]{AUDIO}[a0];[2:a]{AUDIO}[a1];[a0][a1]concat=n=2:v=0:a=1[a]"
)
cmd = ["ffmpeg", "-y", "-loglevel", "error",
       "-i", CLIP,
       "-framerate", "30", "-start_number", "1", "-i", RN + "sprechtest/f_%04d.png",
       "-i", RN + "sprechtest_stimme.wav",
       "-i", lab_l, "-i", lab_r,
       "-filter_complex", flt, "-map", "[v]", "-map", "[a]",
       "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "160k", "-r", "30", OUT]
subprocess.run(cmd, check=True)
print(OUT, round(os.path.getsize(OUT) / 1e6, 2), "MB")
