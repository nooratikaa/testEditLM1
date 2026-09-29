import subprocess, sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
SRC = 'clean.mp4'
FPS = 30
W, H = 1080, 1920

GRADE = (
    "format=gbrp,"
    "huesaturation=saturation=-0.5:colors=c+g,"
    "huesaturation=saturation=-0.12:colors=r+y+m,huesaturation=saturation=-0.3:colors=b,"
    "colorbalance=rs=0.025:bs=-0.035:rm=0.045:gm=0.01:bm=-0.05:rh=0.015:bh=-0.02,"
    "curves=all='0/0.035 0.25/0.22 0.5/0.5 0.78/0.8 1/0.955',"
    "eq=contrast=1.03:gamma=0.98,"
    "vignette=angle=0.35,"
    "unsharp=5:5:0.45,"
    "noise=alls=3:allf=t,"
    "format=yuv420p"
)

# name, src_in, src_out, out_duration, crop_x (0..78), ramp
CLIPS = [
    ('01_hook',     44.30, 46.20, 3.4, -20, None),
    ('02_cover',     9.30, 10.95, 2.4, 50, None),
    ('03_runner',   15.00, 16.40, 1.6, 40, None),
    ('04_chairs',   24.60, 26.20, 2.0, 40, None),
    ('05_vase',     31.06, 32.00, 1.6, 30, None),
    ('06_sash',     32.08, 33.25, 1.7, 30, None),
    ('07_reveal',   36.10, 38.45, 2.95, 39, 'ramp'),
    ('07b_punch',   39.30, 40.50, 1.6, -150, None),
    ('08_sashdet',  46.60, 48.05, 2.0, -100, None),
    ('10_closing',  51.80, 55.10, 4.2, 39, None),
]

def clip(name, a, b, dur, cx, ramp):
    src_len = b - a
    speed = src_len / dur
    tight = cx < 0
    crop = f"crop=376:668:{-cx}:0" if tight else f"crop=498:880:{cx}:0"
    f = [f"trim=start={a}:end={b}", "setpts=PTS-STARTPTS", crop]
    if ramp:
        # speed ramp: 0.55x easing linearly up to 1.0x+ ; out(u) solved in setpts
        s0, a0, b0 = 0.55, 0.45, 1.25
        k = (1.0 - s0) / (b0 - a0)
        t1 = a0 / s0
        t2 = t1 + (1 / k) * __import__('math').log(1.0 / s0)
        f.append("minterpolate=fps=90:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1")
        # piecewise: u<a0 -> u/s0 ; a0<=u<b0 -> t1 + ln((s0+k(u-a0))/s0)/k ; u>=b0 -> t2 + (u-b0)
        e = (f"if(lt(T,{a0}),T/{s0},if(lt(T,{b0}),{t1}+log(({s0}+{k}*(T-{a0}))/{s0})/{k},{t2}+(T-{b0})))")
        f.append(f"setpts='({e})/TB'")
    elif speed < 0.97:
        f.append(f"minterpolate=fps={int(round(FPS/speed/10.0)*10)+10}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1")
        f.append(f"setpts=PTS/{speed}")
    else:
        f.append(f"setpts=PTS/{speed}")
    g = GRADE.replace("unsharp=5:5:0.45", "unsharp=7:7:0.75:3:3:0.25") if tight else GRADE
    f += [f"fps={FPS}", f"scale={W}:{H}:flags=lanczos", g, f"trim=duration={dur}", "setpts=PTS-STARTPTS"]
    vf = ",".join(f)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', SRC if (a >= 35.9 and not tight) else 'src.mp4', '-an', '-vf', vf,
                    '-c:v', 'libx264', '-crf', '10', '-preset', 'medium', '-r', str(FPS), f'clips/{name}.mp4'], check=True)

if __name__ == '__main__':
    os.makedirs('clips', exist_ok=True)
    only = sys.argv[1:]
    for c in CLIPS:
        if not only or c[0] in only:
            clip(*c); print('done', c[0], flush=True)
