#!/usr/bin/env python3
"""
case_stage2.py — 2단계 척력(인력으로 자리 잡은 뒤 덕트가 밀어내기)의 성립성 검토.

A.13 은 인력과 척력이 *동시에* 작용할 때의 평형을 다뤘다. 여기서는 다르다:
  1단계: CAF 인력으로 피복선에 안착 (완료, 척력 없음)
  2단계: 인력을 끄고, 덕트 척력만으로 피복선 *접선방향* 이동

접선 구속이 핵심이다. 구속 없이 밀면 1단계의 피복 결과가 깨진다:
      v2 = -(I - n (x) n) grad U_rep      (n = 피복면 법선)
즉 철근은 피복선 위를 미끄러져 덕트를 벗어난다.

측정: 필요 이동량, 간격 왜곡, 연쇄(cascade) 범위, 배치 실패 개수.
그리고 대안 (I) 정의역 제외(=절단) 와 ρ / 조각 개수로 비교한다.
"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from admissible import Section, seg_dist

H, BOT_HALF, TOP_HALF = 6600.0, 3000.0, 6000.0
COVER, PHI = 50.0, 16.0
LD = 40 * PHI                       # 정착길이 640
SPACING = 200.0                     # 설계 배근 간격
MIN_CLEAR = max(PHI, 25.0)          # 철근 순간격 하한 (KDS 개략)
DUCT_Y, DUCT_R = 3300.0, 60.0
DUCT_XS = [-1200.0, -800.0, -400.0, 0.0, 400.0, 800.0, 1200.0]

outer = [(-BOT_HALF, 0.0), (BOT_HALF, 0.0), (TOP_HALF, H), (-TOP_HALF, H)]

def half_width(y):
    return BOT_HALF + (TOP_HALF - BOT_HALF) * y / H

def excl(r_duct):
    """덕트 배제반경 = 덕트반경 + 피복 + phi/2"""
    return r_duct + COVER + PHI/2

def hits(y, r_duct):
    """수평 철근 y 가 덕트열과 간섭하는가 (수직 거리 기준)"""
    return abs(y - DUCT_Y) < excl(r_duct)

def stage2(r_duct, spacing):
    """2단계: 접선(=수직) 이동으로 덕트를 벗어남. 연쇄 밀림 포함."""
    ys = [k*spacing for k in range(1, int(H/spacing))]
    ys = [y for y in ys if 0 < y < H]
    e = excl(r_duct)
    moved = {y: y for y in ys}

    # 덕트 아래 철근은 아래로, 위 철근은 위로 밀린다
    below = sorted([y for y in ys if y <= DUCT_Y], reverse=True)
    above = sorted([y for y in ys if y >  DUCT_Y])

    prev = None
    for y in below:                              # 위에서 아래로 연쇄
        t = moved[y]
        if hits(t, r_duct):
            t = DUCT_Y - e
        if prev is not None and prev - t < spacing - (spacing - MIN_CLEAR - PHI):
            t = min(t, prev - (MIN_CLEAR + PHI))
        moved[y] = t; prev = t
    prev = None
    for y in above:
        t = moved[y]
        if hits(t, r_duct):
            t = DUCT_Y + e
        if prev is not None and t - prev < MIN_CLEAR + PHI:
            t = max(t, prev + (MIN_CLEAR + PHI))
        moved[y] = t; prev = t

    dys = [moved[y]-y for y in ys]
    order = sorted(moved.values())
    gaps = [order[i+1]-order[i] for i in range(len(order)-1)]
    fail = sum(1 for g in gaps if g < MIN_CLEAR + PHI - 1e-6)
    out = sum(1 for y in ys if not (0 < moved[y] < H))
    return ys, moved, dys, gaps, fail, out

def stage_exclude(r_duct, spacing):
    """(I) 정착역 제외: 간섭하는 철근은 덕트마다 잘린다. 조각/슬리버 계수."""
    ys = [k*spacing for k in range(1, int(H/spacing))]
    e = excl(r_duct); pieces_all, slivers, total_len = 0, 0, 0.0
    for y in ys:
        hw = half_width(y) - COVER/math.cos(math.atan((TOP_HALF-BOT_HALF)/H)) - PHI/2
        if not hits(y, r_duct):
            pieces_all += 1; total_len += 2*hw; continue
        # 이 높이에서 각 덕트가 만드는 배제구간 [cx-w, cx+w]
        bans = []
        for cx in DUCT_XS:
            dy = abs(y-DUCT_Y)
            if dy >= e: continue
            w = math.sqrt(e*e - dy*dy)
            bans.append((cx-w, cx+w))
        bans.sort(); merged=[]
        for b in bans:
            if merged and b[0] <= merged[-1][1]: merged[-1]=(merged[-1][0], max(merged[-1][1],b[1]))
            else: merged.append(list(b))
        cuts, x = [], -hw
        for a,b in merged:
            if b < -hw or a > hw: continue
            if a > x: cuts.append((x, min(a,hw)))
            x = max(x, min(b, hw))
        if x < hw: cuts.append((x, hw))
        for a,b in cuts:
            L = b-a
            if L <= 0: continue
            pieces_all += 1; total_len += L
            if L < LD: slivers += 1
    return pieces_all, slivers, total_len

print(f"격벽 사다리꼴 H={H:.0f}, 하부반폭={BOT_HALF:.0f}, 상부반폭={TOP_HALF:.0f}")
print(f"덕트열 y={DUCT_Y:.0f}, {len(DUCT_XS)}공, 피복 {COVER:.0f}, phi={PHI:.0f}, ld={LD:.0f}")
print(f"철근 순간격 하한 {MIN_CLEAR:.0f} (중심간 {MIN_CLEAR+PHI:.0f})")
print()
print("=== (II) 2단계 척력: 피복선 접선방향 이동 ===")
print(f"{'덕트r':>6} {'배제반경':>8} {'밀린 철근':>9} {'최대이동':>9} {'최소간격':>9} {'간격위반':>8} {'이탈':>5}")
print("-"*62)
for rd in (40, 60, 80, 100, 120, 150, 200):
    ys, moved, dys, gaps, fail, out = stage2(float(rd), SPACING)
    nz = sum(1 for d in dys if abs(d) > 1e-6)
    print(f"{rd:6.0f} {excl(float(rd)):8.1f} {nz:9d} {max(abs(d) for d in dys):9.1f}"
          f" {min(gaps):9.1f} {fail:8d} {out:5d}")

print()
print("=== (I) 정의역 제외(절단) 와 비교 — 같은 케이스 ===")
print(f"{'덕트r':>6} {'(I)조각수':>9} {'(I)슬리버':>9} {'(I)총연장m':>11} {'(II)총연장m':>12} {'(II)슬리버':>10}")
print("-"*62)
for rd in (40, 60, 80, 100, 120, 150, 200):
    p, s, tl = stage_exclude(float(rd), SPACING)
    ys, moved, dys, gaps, fail, out = stage2(float(rd), SPACING)
    th = math.atan((TOP_HALF-BOT_HALF)/H)
    tl2 = sum(2*(half_width(moved[y]) - COVER/math.cos(th) - PHI/2) for y in ys)
    print(f"{rd:6.0f} {p:9d} {s:9d} {tl/1000:11.1f} {tl2/1000:12.1f} {0:10d}")
