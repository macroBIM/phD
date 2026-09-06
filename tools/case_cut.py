#!/usr/bin/env python3
"""
case_cut.py — "장이 철근을 잘라 준다"는 기능이 수학적으로 성립하는지 실측.

주장: 철근 절단·길이조정은 새로운 장이 아니라, 이미 있는 허용장
      psi(x) = dist(x, boundary) - c - phi/2
      의 레벨셋으로 철근 곡선을 제한한 결과(1D 부울 교집합)이다.

      realized(bar) = { s in [0,L] : psi(gamma(s)) >= 0 }

이 스크립트는 그 집합을 이분법으로 기계정밀도까지 구해
  (1) 조각 개수(개구부에서 2분할되는가)
  (2) 각 조각 길이(경사 복부에서 자동 조정되는가)
  (3) 정착길이 미달 조각(잘린 결과가 유효한 철근인가)
  (4) 경사면에서 수평피복을 쓸 때의 오차 1/cos(theta)
를 보고한다.
"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from admissible import Section

# ── 격벽 형상 (박스거더 내부를 채운 사다리꼴 + 중앙 맨홀 개구부) ─────────
H         = 6600.0     # 격벽 높이
BOT_HALF  = 3000.0     # 하부 반폭
TOP_HALF  = 6000.0     # 상부 반폭
OPEN_W    = 1400.0     # 맨홀 폭
OPEN_H    = 2000.0     # 맨홀 높이
OPEN_CY   = 3300.0     # 맨홀 중심 높이

COVER = {'outer': 50.0, 'void': 50.0, 'duct': 50.0}
PHI   = 16.0           # 격벽 횡방향 철근 D16
LD    = 40 * PHI       # 정착길이 (40phi, KDS 개략치) = 640 mm

outer = [(-BOT_HALF, 0.0), (BOT_HALF, 0.0), (TOP_HALF, H), (-TOP_HALF, H)]
manhole = [(-OPEN_W/2, OPEN_CY-OPEN_H/2), (OPEN_W/2, OPEN_CY-OPEN_H/2),
           (OPEN_W/2, OPEN_CY+OPEN_H/2), (-OPEN_W/2, OPEN_CY+OPEN_H/2)]
sec = Section(outer, [manhole], [], COVER)

# 복부 경사각 (연직에서)
theta = math.atan((TOP_HALF - BOT_HALF) / H)

# ── 수평선 y=y0 위에서 psi>=0 인 구간들을 이분법으로 정확히 구한다 ──────
def psi(x, y, phi):
    """부호 있는 허용장. 콘크리트 안이면 +, 밖이면 -."""
    d = sec.clearance(x, y, phi)
    return d if sec.inside_concrete(x, y) else -abs(d) - 1.0


def intervals(y0, phi, n=4000, tol=1e-9):
    x0, x1 = -TOP_HALF - 10.0, TOP_HALF + 10.0
    xs = [x0 + (x1-x0)*i/n for i in range(n+1)]
    vs = [psi(x, y0, phi) for x in xs]

    def root(a, b):                       # psi 부호가 바뀌는 구간에서 이분법
        fa = psi(a, y0, phi)
        while b - a > tol:
            m = 0.5*(a+b)
            if (psi(m, y0, phi) >= 0) == (fa >= 0):
                a, fa = m, psi(m, y0, phi)
            else:
                b = m
        return 0.5*(a+b)

    out, s = [], None
    for i in range(n+1):
        inside = vs[i] >= 0
        if inside and s is None:
            s = xs[i] if i == 0 else root(xs[i-1], xs[i])
        elif not inside and s is not None:
            out.append((s, root(xs[i-1], xs[i]))); s = None
    if s is not None:
        out.append((s, xs[-1]))
    return out

# ── 보고 ────────────────────────────────────────────────────────────────
print(f"격벽 사다리꼴  H={H:.0f}  하부반폭={BOT_HALF:.0f}  상부반폭={TOP_HALF:.0f}")
print(f"맨홀 {OPEN_W:.0f} x {OPEN_H:.0f}, 중심 y={OPEN_CY:.0f}")
print(f"피복 {COVER['outer']:.0f}, phi={PHI:.0f}, 정착길이 ld={LD:.0f}")
print(f"복부 경사 theta = {math.degrees(theta):.2f}deg (연직 기준), cos = {math.cos(theta):.4f}")
print()
print(f"{'y (mm)':>8} {'조각':>4} {'각 조각 길이 (mm)':>34} {'ld 미달':>7}")
print("-"*62)

rows, n_split, n_short = [], 0, 0
for k in range(1, 33):
    y0 = k * 200.0
    iv = intervals(y0, PHI)
    lens = [b-a for a, b in iv]
    if not lens:
        continue
    short = sum(1 for L in lens if L < LD)
    n_short += short
    if len(lens) >= 2:
        n_split += 1
    rows.append((y0, len(lens), lens, short))
    txt = " + ".join(f"{L:8.1f}" for L in lens)
    print(f"{y0:8.0f} {len(lens):4d} {txt:>34} {short:7d}")

print("-"*62)
print(f"2분할된 철근 단수: {n_split} / {len(rows)}")
print(f"정착길이 미달 조각 수: {n_short}")
print()

# ── 경사 복부에서 수평피복을 쓰면 얼마나 틀리는가 ────────────────────────
print("경사 복부: 수평 오프셋으로 피복을 주면 실제 피복이 얼마나 부족한가")
print(f"{'y (mm)':>8} {'수평오프셋 c':>12} {'실제 피복':>10} {'부족량':>8} {'정오프셋 c/cos':>14}")
print("-"*58)
c = COVER['outer']
for y0 in (600.0, 2000.0, 4000.0, 6000.0):
    half = BOT_HALF + (TOP_HALF-BOT_HALF)*y0/H     # 그 높이에서의 외곽면 x
    # 수평으로 c 만큼 들어간 점의 실제(법선) 피복
    x_naive = half - c
    real = min(math.hypot(0,0) or 0, 0) or min(
        __import__('admissible').seg_dist(x_naive, y0, *e) for e in sec.e_out)
    print(f"{y0:8.0f} {c:12.1f} {real:10.2f} {c-real:8.2f} {c/math.cos(theta):14.2f}")
