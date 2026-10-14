"""Check a set of colours for colour-vision-deficiency separation and contrast.

Usage: python scripts/check_palette.py "#33408F,#B5531E,#2E5F3E,#7C1A4B" [more sets...]
Prints the worst all-pairs CIEDE2000 under normal vision and Machado (2009)
protan, deutan and tritan simulation, and each colour's contrast on --sheet.
Aim for normal >= 20 and every CVD >= 10; text colours need >= 4.5:1.
"""
import itertools, math, sys
import numpy as np
def hex2rgb(h): h=h.lstrip('#'); return np.array([int(h[i:i+2],16)/255 for i in (0,2,4)])
def lin(c): return np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
def delin(c): c=np.clip(c,0,1); return np.where(c<=0.0031308,c*12.92,1.055*c**(1/2.4)-0.055)
M={'prot':np.array([[0.152286,1.052583,-0.204868],[0.114503,0.786281,0.099216],[-0.003882,-0.048116,1.051998]]),
   'deut':np.array([[0.367322,0.860646,-0.227968],[0.280085,0.672501,0.047413],[-0.011820,0.042940,0.968881]]),
   'trit':np.array([[1.255528,-0.076749,-0.178779],[-0.078411,0.930809,0.147602],[0.004733,0.691367,0.303900]])}
def sim(rgb,k): return delin(M[k]@lin(rgb)) if k!='norm' else rgb
def lab(rgb):
    l=lin(rgb); X=np.array([[0.4124,0.3576,0.1805],[0.2126,0.7152,0.0722],[0.0193,0.1192,0.9505]])@l
    X=X/np.array([0.95047,1,1.08883]); f=np.where(X>0.008856,np.cbrt(X),7.787*X+16/116)
    return np.array([116*f[1]-16,500*(f[0]-f[1]),200*(f[1]-f[2])])
def de2000(l1,l2):
    L1,a1,b1=l1;L2,a2,b2=l2;C1=math.hypot(a1,b1);C2=math.hypot(a2,b2);Cb=(C1+C2)/2
    G=0.5*(1-math.sqrt(Cb**7/(Cb**7+25**7)));a1p=(1+G)*a1;a2p=(1+G)*a2
    C1p=math.hypot(a1p,b1);C2p=math.hypot(a2p,b2);h1=math.degrees(math.atan2(b1,a1p))%360;h2=math.degrees(math.atan2(b2,a2p))%360
    dL=L2-L1;dC=C2p-C1p;dh=h2-h1
    if C1p*C2p==0: dh=0
    elif dh>180: dh-=360
    elif dh<-180: dh+=360
    dH=2*math.sqrt(C1p*C2p)*math.sin(math.radians(dh/2));Lb=(L1+L2)/2;Cbp=(C1p+C2p)/2
    hb=(h1+h2)/2 if abs(h1-h2)<=180 else (h1+h2+360)/2
    if C1p*C2p==0: hb=h1+h2
    T=1-0.17*math.cos(math.radians(hb-30))+0.24*math.cos(math.radians(2*hb))+0.32*math.cos(math.radians(3*hb+6))-0.20*math.cos(math.radians(4*hb-63))
    SL=1+0.015*(Lb-50)**2/math.sqrt(20+(Lb-50)**2);SC=1+0.045*Cbp;SH=1+0.015*Cbp*T
    RT=-2*math.sqrt(Cbp**7/(Cbp**7+25**7))*math.sin(math.radians(60*math.exp(-((hb-275)/25)**2)))
    return math.sqrt((dL/SL)**2+(dC/SC)**2+(dH/SH)**2+RT*(dC/SC)*(dH/SH))
def lum(rgb): l=lin(rgb); return 0.2126*l[0]+0.7152*l[1]+0.0722*l[2]
def cr(a,b): A,B=sorted([lum(hex2rgb(a)),lum(hex2rgb(b))],reverse=True); return (A+0.05)/(B+0.05)
sets=[s.split(',') for s in sys.argv[1:]]
for s in sets:
    names=s
    worst={}
    for k in ['norm','prot','deut','trit']:
        worst[k]=min(de2000(lab(sim(hex2rgb(a),k)),lab(sim(hex2rgb(b),k))) for a,b in itertools.combinations(names,2))
    print(s, {k:round(v,1) for k,v in worst.items()}, 'contrast vs #FBF8F1:', [float(round(cr(c,'#FBF8F1'),1)) for c in s])
