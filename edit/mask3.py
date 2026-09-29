import cv2, numpy as np
cap=cv2.VideoCapture('src.mp4'); fps=cap.get(5)
segs={'B':(7.6,35.5),'C':(36.2,56.4)}
buf={k:[] for k in segs}; i=0
while True:
    ok,f=cap.read()
    if not ok: break
    t=i/fps
    for k,(a,b) in segs.items():
        if a<=t<=b and i%2==0: buf[k].append(f.mean(2).astype(np.uint8))
    i+=1
for k,L in buf.items():
    g=np.stack(L)
    bright=(g>185).mean(0); dark=(g<70).mean(0)
    zone=np.zeros(g.shape[1:],np.uint8); zone[885:1020,100:480]=1
    if k=='C': zone[670:800,130:450]=1
    core=((bright>0.55)&(zone>0)).astype(np.uint8)
    near=cv2.dilate(core,np.ones((9,9),np.uint8))
    sh=((dark>0.55)&(near>0)).astype(np.uint8)
    m=cv2.dilate(core|sh,np.ones((3,3),np.uint8),iterations=2)*255
    cv2.imwrite(f'mask_{k}.png',m); print(k,(m>0).sum())
