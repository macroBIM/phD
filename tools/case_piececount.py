#!/usr/bin/env python3
"""
case_piececount.py — "조각 수를 미리 알 수 있는가"를 실측.

주장: 조각 수는 간섭체 개수의 함수가 아니라 철근 위치의 함수다.
      따라서 사전 분할·사전 할당은 불가능하며, 조각 수는 출력값이다.

같은 단면에서 y 만 바꿔가며
  m(y) = 그 높이에서 철근선이 만나는 간섭체 수
  n(y) = 실제로 나오는 조각 수
를 함께 세어 m 과 n 의 관계를 본다.
"""
import math

H, BOT_HALF, TOP_HALF = 6600.0, 3000.0, 6000.0
COVER, PHI = 50.0, 16.0
THETA = math.atan((TOP_HALF-BOT_HALF)/H)
M = COVER + PHI/2                                    # 배제 여유

# 간섭체 3종
OPEN1 = (-700.0,  700.0, 2300.0, 4300.0)             # 중앙 맨홀
OPEN2 = (2400.0, 3200.0, 1000.0, 2000.0)             # 편심 점검구
DUCTS = [(x, 5000.0, 60.0) for x in
         (-1600.0, -1200.0, -800.0, -400.0, 0.0, 400.0, 800.0, 1200.0, 1600.0)]

def hw(y):
    return BOT_HALF + (TOP_HALF-BOT_HALF)*y/H - COVER/math.cos(THETA) - PHI/2

def bands(y):
    """그 높이에서 막히는 x 구간들과, 실제로 만난 간섭체 수"""
    out, met = [], 0
    for (x0, x1, y0, y1) in (OPEN1, OPEN2):
        if y0-M <= y <= y1+M:
            out.append((x0-M, x1+M)); met += 1
    for (cx, cy, r) in DUCTS:
        e = r + M
        dy = abs(y-cy)
        if dy < e:
            w = math.sqrt(e*e - dy*dy)
            out.append((cx-w, cx+w)); met += 1
    return out, met

def pieces(y):
    W = hw(y)
    if W <= 0: return [], 0
    bs, met = bands(y)
    # 단면 안으로 자르고 병합
    bs = [(max(a,-W), min(b,W)) for a,b in bs]
    bs = [(a,b) for a,b in bs if b > a]
    bs.sort(); mg = []
    for a,b in bs:
        if mg and a <= mg[-1][1]: mg[-1][1] = max(mg[-1][1], b)
        else: mg.append([a,b])
    out, x = [], -W
    for a,b in mg:
        if a > x: out.append((x, a))
        x = max(x, b)
    if x < W: out.append((x, W))
    return out, met

print("간섭체: 중앙맨홀 1, 편심점검구 1, 덕트 9  →  총 11 개")
print()
print(f"{'y':>6} {'만난 간섭체 m':>13} {'조각 수 n':>10} {'n = m+1 ?':>10}   조각 길이")
print("-"*88)
hist = {}
for k in range(1, 66):
    y = k*100.0
    ps, m = pieces(y)
    n = len(ps)
    if n == 0: continue
    hist[n] = hist.get(n, 0) + 1
    if k % 3 == 0 or m > 0:
        mark = "OK" if n == m+1 else f"아님({n} vs {m+1})"
        txt = " + ".join(f"{b-a:.0f}" for a,b in ps)
        print(f"{y:6.0f} {m:13d} {n:10d} {mark:>10}   {txt}")

print("-"*88)
print("조각 수 분포:", ", ".join(f"{n}조각 {c}단" for n,c in sorted(hist.items())))
print(f"최소 {min(hist)} / 최대 {max(hist)} — 같은 단면, 같은 간섭체, y 만 다름")
