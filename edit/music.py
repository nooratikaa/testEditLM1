import numpy as np, wave
from scipy.signal import butter, sosfilt, fftconvolve
SR=48000; BEAT=0.8; BAR=4*BEAT; DUR=26.0
L=int(SR*(DUR+3)); out=np.zeros((L,2))
rng=np.random.default_rng(7)
def hz(n): return 440*2**((n-69)/12)
def lp(x,fc,o=2): return sosfilt(butter(o,fc,fs=SR,output='sos'),x)
def piano(n,vel,dur=4.0):
    f=hz(n); t=np.arange(int(SR*dur))/SR; y=np.zeros_like(t)
    B=0.0004
    for k in range(1,9):
        fk=f*k*np.sqrt(1+B*k*k)
        if fk>9000: break
        amp=(1/k**1.4)*(1 if k==1 else 0.8)
        dec=1.2+ (0.6*k) + (f/600)
        y+=amp*np.sin(2*np.pi*fk*t+rng.random()*6)*np.exp(-t*dec*0.9)
    y+=0.3*np.sin(2*np.pi*f*t)*np.exp(-t*0.5)  # sustain body
    att=np.minimum(1,t/0.006)
    ham=lp(rng.standard_normal(len(t))*np.exp(-t*60),1200)*0.15
    y=(y*att+ham)
    y=lp(y,1800+vel*1500)       # felt: dark
    rel=np.ones_like(t); r0=int(SR*(dur-0.6)); rel[r0:]=np.linspace(1,0,len(t)-r0)
    return y*rel*vel
def pad(notes,start,dur,amp):
    t=np.arange(int(SR*dur))/SR; y=np.zeros((len(t),2))
    for n in notes:
        for det,ch in [(-0.07,0),(0.07,1),(0.0,0),(0.0,1)]:
            f=hz(n)*2**(det/12)
            s=np.sin(2*np.pi*f*t+rng.random()*6)+0.25*np.sin(2*np.pi*2*f*t)+0.1*np.sin(2*np.pi*3*f*t)
            y[:,ch]+=s
    env=np.minimum(1,t/1.2)*np.minimum(1,(dur-t)/1.2).clip(0,1)
    y*=env[:,None]*amp/len(notes)
    add(y,start)
def add(y,start,pan=0.0):
    i=int(start*SR)
    if y.ndim==1:
        l=np.cos((pan+1)*np.pi/4); r=np.sin((pan+1)*np.pi/4)
        y=np.stack([y*l,y*r],1)
    if i<0: y=y[-i:]; i=0
    e=min(L,i+len(y)); out[i:e]+=y[:e-i]
# chords (midi): bars
G7=[43,55,59,62,66]; D=[42,54,57,62,66]; Em9=[40,55,59,62,66]; Asus=[45,57,62,64,69]
Gm9=[43,55,59,62,69]; Dd=[38,54,57,62,64]; Bm7=[47,54,57,62,66]; A9=[45,57,61,64,71]; Dmaj9=[38,50,57,61,64,66]
prog=[G7,D,Em9,Asus,Gm9,Bm7,A9]
for b,ch in enumerate(prog):
    t0=b*BAR
    # arpeggio pattern (8th notes, sparse at start)
    ns=ch[1:]
    pat=[0,2,1,3,2,1,3,2] if b>=4 else [0,None,2,1,None,3,None,2]
    for s,idx in enumerate(pat):
        if idx is None: continue
        n=ns[idx%len(ns)]+12
        v=0.33 if b<4 else 0.4
        v*=0.85+0.15*rng.random()
        add(piano(n,v,3.0), t0+s*BEAT/2+rng.normal(0,0.008), pan=((idx%3)-1)*0.35)
    # left hand root
    add(piano(ch[0]+12 if b<4 else ch[0],0.35 if b<4 else 0.45,4.0),t0,pan=-0.1)
    # pad
    pad(ch[1:4],t0-0.3,BAR+0.9,0.10 if b<4 else 0.16)
    # melody from reveal (bar4 = 12.8s)
mel=[(4,0,74),(4,2.5,73),(4,3,71),(5,0,69),(5,1.5,66),(5,3,71),(6,0,69),(6,2,71),(6,3,64)]
for b,beat,n in mel:
    add(piano(n+12,0.32,3.5),b*BAR+beat*BEAT,pan=0.15)
# sub swell into reveal
t=np.arange(int(SR*3.2))/SR; sw=np.sin(2*np.pi*hz(31)*t)*(t/3.2)**2*0.06; add(sw,9.6)
# final chord
T=7*BAR
for k,n in enumerate(Dmaj9[1:]):
    add(piano(n+12,0.36,5.0),T+k*0.06)
add(piano(38,0.45,5.0),T); pad(Dmaj9[1:5],T-0.3,4.5,0.14)
# reverb
ir_t=np.arange(int(SR*3.0))/SR
ir=np.stack([lp(rng.standard_normal(len(ir_t)),5000)*np.exp(-ir_t*2.2) for _ in range(2)],1); ir/=np.abs(ir).sum(0)**0.5*6
wet=np.stack([fftconvolve(out[:,c],ir[:,c])[:L] for c in range(2)],1)
mix=out*0.75+wet*0.9
mix=mix[:int(SR*DUR)]
# fade out last 1.8s, fade in 0.05
n=len(mix); fo=int(SR*1.8); mix[-fo:]*=np.linspace(1,0,fo)[:,None]**1.5
mix[:int(SR*0.05)]*=np.linspace(0,1,int(SR*0.05))[:,None]
mix=np.tanh(mix/np.abs(mix).max()*1.1)*0.85
mix*= 10**(-1/20)/np.abs(mix).max()
w=wave.open('music.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((mix*32767).astype(np.int16).tobytes()); w.close()
print('ok',n/SR)
