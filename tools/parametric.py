#!/usr/bin/env python3
"""
parametric.py — 공정한 파라메트릭(규칙기반) 배근 baseline

실무자/Dynamo 스크립트가 실제로 하는 절차를 그대로 구현한다.
  ① 지정된 면의 피복선을 offset 한다 — **miter join 으로 robust 하게**
     (단순 offset 의 self-intersection 은 여기서 이미 해결된다. 허수아비를 만들지 않는다.)
  ② 사람이 "이 면에 간격 얼마" 를 지정한다
  ③ 그 선을 따라 등간격으로 놓는다
  ④ 적층은 사람이 층 위치를 계산해 넣는다

덕트는 규칙에 없다 — 사람이 도면을 보고 손으로 뺀다. 그 횟수를 센다.
"""
import math

def offset_ring(ring, d, sign=+1):
    """링을 안쪽(sign=+1: 좌법선)으로 d 만큼 밀고, 이웃 이동선의 교점으로 코너를 잡는다.
    = miter join. 단순 offset 의 자기교차가 여기서 해소된다."""
    n = len(ring)
    lines = []
    for i in range(n):
        (x1, y1), (x2, y2) = ring[i], ring[(i+1) % n]
        dx, dy = x2-x1, y2-y1
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy/L*sign, dx/L*sign          # 좌법선
        lines.append(((x1+nx*d, y1+ny*d), (x2+nx*d, y2+ny*d)))
    out = []
    for i in range(n):
        p = _isect(lines[(i-1) % n], lines[i])
        out.append(p if p else lines[i][0])
    return out

def _isect(a, b):
    (x1,y1),(x2,y2) = a; (x3,y3),(x4,y4) = b
    den = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
    if abs(den) < 1e-9: return None
    t = ((x1-x3)*(y3-y4) - (y1-y3)*(x3-x4)) / den
    return (x1 + t*(x2-x1), y1 + t*(y2-y1))

def place_equal_spacing(poly, spacing, closed=True):
    """폴리라인을 따라 등간격으로 점을 놓는다 (실무의 '@200' 배근)."""
    pts, seglens = [], []
    n = len(poly)
    m = n if closed else n-1
    for i in range(m):
        (x1,y1),(x2,y2) = poly[i], poly[(i+1) % n]
        seglens.append(math.hypot(x2-x1, y2-y1))
    total = sum(seglens)
    count = max(1, int(round(total / spacing)))
    step = total / count
    s = 0.0
    for k in range(count):
        t = k*step
        acc = 0.0
        for i in range(m):
            if acc + seglens[i] >= t or i == m-1:
                r = (t - acc) / (seglens[i] or 1.0)
                (x1,y1),(x2,y2) = poly[i], poly[(i+1) % n]
                pts.append((x1 + (x2-x1)*r, y1 + (y2-y1)*r))
                break
            acc += seglens[i]
    return pts
