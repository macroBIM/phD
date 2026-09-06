#!/usr/bin/env python3
"""
case_dxf.py — 격벽 배근을 (1) 2D 배근도 DXF, (2) 3D 원통 메시 DXF 로 출력.

2D: 철근 = 중심선 1개 (LINE + ARC). 실무 배근도 관례. 종방향 철근은 CIRCLE.
3D: 철근 = 8각 원통 메시 (3DFACE). 콘크리트 = 압출 면. R12(AC1009) 호환.
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dxflib as D
from case_diaphragm import (OUTLINE, MANHOLE, DUCTS_B, BEND_R, DIA, COVER,
                            place_h, place_v, place_opening)

T = 800.0                                  # 격벽 두께
ZF = COVER + DIA/2                         # 전면 철근 z
ZB = T - COVER - DIA/2                     # 배면 철근 z
LAY = {'H1': ('REBAR-H', 4), 'V1': ('REBAR-V', 3), 'O1': ('REBAR-O', 6)}
MH = [(MANHOLE[0],MANHOLE[2]), (MANHOLE[1],MANHOLE[2]),
      (MANHOLE[1],MANHOLE[3]), (MANHOLE[0],MANHOLE[3])]

def bars_for(ducts):
    log = []
    return place_h(ducts, log) + place_v(ducts, log) + place_opening(log)

def dxf2d(bars, ducts, path):
    d = D.Dxf()
    d.layer('CONC', 251).layer('OPENING', 251).layer('DUCT', 2)
    for nm, c in LAY.values(): d.layer(nm, c)
    d.polyline(OUTLINE, 'CONC', closed=True)
    d.polyline(MH, 'OPENING', closed=True)
    for cx, cy, r in ducts:
        d.circle(cx, cy, r, 'DUCT')
        d.circle(cx, cy, r + COVER + DIA/2, 'DUCT')     # 배제선
    for b in bars:
        d.bar(b.pts, b.bend_r, LAY[b.mark][0])
    # 부호 텍스트 (대표 1개씩)
    seen = set()
    for b in bars:
        if b.mark in seen: continue
        seen.add(b.mark)
        p = b.pts[len(b.pts)//2]
        d.text(p[0], p[1] + 60, 90, f"{b.mark}  D{b.dia}@200", LAY[b.mark][0])
    return d.save(path)

def dxf3d(bars, ducts, path):
    d = D.Dxf3D()
    d.layer('CONC', 251).layer('DUCT', 2)
    for nm, c in LAY.values(): d.layer(nm, c)
    d.prism(OUTLINE, 0.0, T, 'CONC')
    d.prism(MH,      0.0, T, 'CONC')
    for cx, cy, r in ducts:                              # 덕트 = z 방향 원통
        ring = [(cx + r*math.cos(2*math.pi*i/12), cy + r*math.sin(2*math.pi*i/12))
                for i in range(12)]
        d.prism(ring, 0.0, T, 'DUCT')
    for b in bars:
        lay = LAY[b.mark][0]
        for z in ((ZF, ZB) if b.count >= 2 else (ZF,)):
            d.tube(b.pts, b.bend_r, b.dia, z=z, lay=lay, sides=8)
    return d.save(path)

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    for name, ducts in (('A', []), ('B', DUCTS_B)):
        bars = bars_for(ducts)
        p2 = dxf2d(bars, ducts, os.path.join(here, f'out_diaphragm_{name}_2d.dxf'))
        p3 = dxf3d(bars, ducts, os.path.join(here, f'out_diaphragm_{name}_3d.dxf'))
        n2 = sum(1 for _ in open(p2)); n3 = sum(1 for _ in open(p3))
        print(f"Case {name}: 철근 {len(bars)}종")
        print(f"   2D {os.path.basename(p2):28} {os.path.getsize(p2)/1024:8.1f} KB")
        print(f"   3D {os.path.basename(p3):28} {os.path.getsize(p3)/1024:8.1f} KB")
