#!/bin/bash
# usage: assemble.sh LEDE_Y MARK_Y KICK_Y CLOSE_Y out.mp4 [music]
cd "$(dirname "$0")"
sed "s/{LEDE_Y}/$1/g; s/{MARK_Y}/$2/g; s/{KICK_Y}/$3/g; s/{CLOSE_Y}/$4/g" titles.ass > titles_r.ass
C=clips
ffmpeg -v error -y \
 -i $C/01_hook.mp4 -i $C/02_cover.mp4 -i $C/03_runner.mp4 -i $C/04_chairs.mp4 -i $C/05_vase.mp4 -i $C/06_sash.mp4 \
 -i $C/07_reveal.mp4 -i $C/07b_punch.mp4 -i $C/08_sashdet.mp4 -i $C/10_closing.mp4 \
 -f lavfi -i "color=c=0xEFE9E0:s=1080x1920:r=30:d=4.25" \
 -i music.wav \
 -filter_complex "
 [1:v][2:v][3:v][4:v][5:v]concat=n=5:v=1:a=0,settb=1/30[B];
 [6:v][7:v][8:v][9:v]concat=n=4:v=1:a=0,settb=1/30[C];
 [10:v]format=yuv420p,noise=alls=2:allf=t,vignette=angle=0.25,settb=1/30[D];
 [0:v]settb=1/30[A];
 [A][B]xfade=transition=fade:duration=0.4:offset=3.0[AB];
 [AB][C]xfade=transition=fade:duration=0.5:offset=11.8[ABC];
 [ABC][D]xfade=transition=fade:duration=0.8:offset=21.75,subtitles=titles_r.ass:fontsdir=fonts/ttf,format=yuv420p[v];
 [11:a]highpass=f=40,equalizer=f=120:t=q:w=1:g=-3,loudnorm=I=-14:TP=-1.5:LRA=7,aresample=48000[a]" \
 -map "[v]" -map "[a]" -t 26.0 -c:v libx264 -preset slow -crf 16 -profile:v high -level 4.2 -pix_fmt yuv420p -r 30 \
 -x264-params "keyint=60:min-keyint=30" -movflags +faststart -c:a aac -b:a 256k "$5"
