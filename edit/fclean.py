import cv2, numpy as np, subprocess
m=cv2.imread('mask_C.png',0); m[830:]=0
M=m>0
Mbig=cv2.dilate(m,np.ones((13,13),np.uint8))>0
MbigU=Mbig.astype(np.uint8)*255
cap=cv2.VideoCapture('src.mp4'); fps=cap.get(5); F=[]
while True:
    ok,f=cap.read()
    if not ok: break
    F.append(f)
N=len(F); G=[cv2.cvtColor(f,cv2.COLOR_BGR2GRAY) for f in F]
cuts=[0,int(36.0*fps)+1,int(44.2*fps)+1,int(51.433*fps)+1,N]
def shot(i):
    for a,b in zip(cuts,cuts[1:]):
        if a<=i<b: return a,b
dis=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
yy,xx=np.mgrid[0:1024,0:576].astype(np.float32)
ring=cv2.dilate(m,np.ones((31,31),np.uint8))>0; ring&=~Mbig
start=int(35.95*fps)
out=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s','576x1024','-r','29.98230088495575','-i','-','-c:v','libx264','-crf','8','-preset','fast','-pix_fmt','yuv420p','clean.mp4'],stdin=subprocess.PIPE)
feather=cv2.GaussianBlur(cv2.dilate(m,np.ones((5,5),np.uint8)).astype(np.float32)/255,(11,11),0)[...,None]
st=[]
for i in range(N):
    f=F[i]
    if i>=start and ((G[i]>200)&M).mean()>0:
        a,b=shot(i); cands=[]
        for d in [5,-5,10,-10,16,-16,24,-24,34,-34,48,-48]:
            j=i+d
            if not(a<=j<b): continue
            fl=dis.calc(G[i],G[j],None)
            fx=cv2.inpaint(fl[...,0].copy(),MbigU,7,cv2.INPAINT_TELEA)
            fy=cv2.inpaint(fl[...,1].copy(),MbigU,7,cv2.INPAINT_TELEA)
            mx=xx+fx; my=yy+fy
            w=cv2.remap(F[j],mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
            src_ok=cv2.remap(MbigU,mx,my,cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT,borderValue=255)==0
            inb=(mx>=0)&(mx<575)&(my>=0)&(my<1023)
            err=np.abs(w.astype(np.float32)-f.astype(np.float32)).mean(2)[ring]
            if np.median(err)>12: continue
            v=src_ok&inb
            cands.append((w,v))
            if len(cands)>=5 and all(c[1][M].mean()>0.98 for c in cands[-3:]): break
        acc=f.copy(); rest=M.copy()
        if cands:
            W=np.stack([c[0] for c in cands]).astype(np.float32)
            V=np.stack([c[1] for c in cands])
            W[~V]=np.nan
            med=np.nanmedian(W,axis=0)
            have=V.any(0)&M
            acc[have]=np.clip(med[have],0,255).astype(np.uint8)
            rest=M&~have
        if rest.any(): acc=cv2.inpaint(acc,rest.astype(np.uint8)*255,5,cv2.INPAINT_TELEA)
        f=(acc*feather+f*(1-feather)).astype(np.uint8)
        st.append(rest.sum()/M.sum())
    out.stdin.write(f.tobytes())
out.stdin.close(); out.wait()
print(len(st),np.mean(st))
