#!/usr/bin/env python3
"""
case_diaphragm.py — 격벽 배근 예제 2건: 장(psi)으로 배근 → 정착판정 → 물량 + 배근도.

Case A : 중앙 맨홀만
Case B : 중앙 맨홀 + 덕트열 (간섭체가 배근 경로에 걸침)

절차 (앞서 검증한 S1~S5)
  S2 제한 : 배근선을 {psi>=0} 으로 잘라 조각 분해
  S3 판정 : 조각별 ell >= ld
  S4 재시도: 미달이면 배근선을 접선방향으로 미끄러뜨려 재분해 (Gamma_obst 처리)
  S5 확정 : 그래도 미달이면 폐기 → 물량에서 빠짐
출력: BOM(부호별 집계) + SVG 배근도 + 굽힘보정 유무 물량 비교
"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rebarlib import Bar, bom, bom_text, svg

# ── 격벽 제원 ────────────────────────────────────────────────────────────
H, BOT_HALF, TOP_HALF = 6600.0, 3000.0, 6000.0
COVER, DIA, SPACING = 50.0, 16.0, 200.0
LD = 40 * DIA                       # 정착길이 640
BEND_R = 3 * DIA                    # 굽힘 중심선 반지름 48
THETA = math.atan((TOP_HALF-BOT_HALF)/H)
M = COVER + DIA/2

OUTLINE = [(-BOT_HALF, 0.0), (BOT_HALF, 0.0), (TOP_HALF, H), (-TOP_HALF, H)]
MANHOLE = (-700.0, 700.0, 2300.0, 4300.0)          # x0,x1,y0,y1
DUCTS_B = [(x, 5000.0, 60.0) for x in
           (-1600.0,-1200.0,-800.0,-400.0,0.0,400.0,800.0,1200.0,1600.0)]

def hw(y):                                          # 그 높이의 사용가능 반폭
    return BOT_HALF + (TOP_HALF-BOT_HALF)*y/H - COVER/math.cos(THETA) - DIA/2

def y_range_at(x):
    """연직 배근선 x 에서 콘크리트가 존재하는 y 구간 (사다리꼴이므로 하한이 x 에 의존)"""
    ylo = COVER + DIA/2
    yhi = H - COVER - DIA/2
    # |x| = BOT_HALF + (TOP_HALF-BOT_HALF)*y/H  를 만족하는 y 아래로는 콘크리트 없음
    need = (abs(x) + COVER/math.cos(THETA) + DIA/2 - BOT_HALF) * H / (TOP_HALF-BOT_HALF)
    return max(ylo, need), yhi

def h_bands(y, ducts):
    b = []
    x0, x1, y0, y1 = MANHOLE
    if y0-M <= y <= y1+M: b.append((x0-M, x1+M))
    for cx, cy, r in ducts:
        e, dy = r+M, abs(y-cy)
        if dy < e:
            w = math.sqrt(e*e-dy*dy); b.append((cx-w, cx+w))
    return b

def v_bands(x, ducts):
    b = []
    x0, x1, y0, y1 = MANHOLE
    if x0-M <= x <= x1+M: b.append((y0-M, y1+M))
    for cx, cy, r in ducts:
        e, dx = r+M, abs(x-cx)
        if dx < e:
            w = math.sqrt(e*e-dx*dx); b.append((cy-w, cy+w))
    return b

def cut(lo, hi, bands):
    bs = sorted([(max(a,lo), min(b,hi)) for a,b in bands if min(b,hi) > max(a,lo)])
    mg = []
    for a,b in bs:
        if mg and a <= mg[-1][1]: mg[-1][1] = max(mg[-1][1], b)
        else: mg.append([a,b])
    out, x = [], lo
    for a,b in mg:
        if a > x: out.append((x,a))
        x = max(x,b)
    if x < hi: out.append((x,hi))
    return out

def place_h(ducts, log):
    bars, slid, dropped = [], 0, 0
    for k in range(1, int(H/SPACING)):
        y = k*SPACING
        W = hw(y)
        if W <= 0: continue
        segs = cut(-W, W, h_bands(y, ducts))
        if any(b-a < LD for a,b in segs):                       # S4 재시도
            best = None
            for d in [i*4.0 for i in range(1, 76)]:
                for t in (y-d, y+d):
                    if t <= 0 or t >= H: continue
                    W2 = hw(t)
                    if W2 <= 0: continue
                    s2 = cut(-W2, W2, h_bands(t, ducts))
                    if s2 and all(b-a >= LD for a,b in s2):
                        best = (t, s2); break
                if best: break
            if best:
                y, segs = best[0], best[1]; slid += 1
        keep = [(a,b) for a,b in segs if b-a >= LD]
        dropped += len(segs) - len(keep)
        for a,b in keep:
            bars.append(Bar('H1', int(DIA), [(a,y),(b,y)], count=2, bend_r=BEND_R))
    log.append(f"  수평 H1: {len(bars)}본(x2면)  S4 이동 {slid}단  S5 폐기 {dropped}조각")
    return bars

def place_v(ducts, log):
    bars, slid, dropped = [], 0, 0
    n = int(TOP_HALF/SPACING)
    for k in range(-n, n+1):
        x = k*SPACING
        lo, hi = y_range_at(x)
        if hi - lo < LD: continue
        segs = cut(lo, hi, v_bands(x, ducts))
        if any(b-a < LD for a,b in segs):
            best = None
            for d in [i*4.0 for i in range(1, 76)]:
                for t in (x-d, x+d):
                    lo2, hi2 = y_range_at(t)
                    if hi2-lo2 < LD: continue
                    s2 = cut(lo2, hi2, v_bands(t, ducts))
                    if s2 and all(b-a >= LD for a,b in s2):
                        best = (t, s2); break
                if best: break
            if best:
                x, segs = best[0], best[1]; slid += 1
        keep = [(a,b) for a,b in segs if b-a >= LD]
        dropped += len(segs) - len(keep)
        for a,b in keep:
            bars.append(Bar('V1', int(DIA), [(x,a),(x,b)], count=2, bend_r=BEND_R))
    log.append(f"  연직 V1: {len(bars)}본(x2면)  S4 이동 {slid}열  S5 폐기 {dropped}조각")
    return bars

def place_opening(log):
    """개구부 보강근 — 4변 각각, 양쪽으로 정착길이 연장 + 90도 절곡"""
    x0, x1, y0, y1 = MANHOLE
    e = M; bars = []
    ho = 150.0                                       # 절곡 후크 길이
    for (yy, sgn) in ((y0-e, -1), (y1+e, +1)):       # 하 · 상 수평 보강
        bars.append(Bar('O1', int(DIA),
            [(x0-e-LD, yy+sgn*ho), (x0-e-LD, yy), (x1+e+LD, yy), (x1+e+LD, yy+sgn*ho)],
            count=4, bend_r=BEND_R, note='개구부 수평보강'))
    for (xx, sgn) in ((x0-e, -1), (x1+e, +1)):       # 좌 · 우 연직 보강
        bars.append(Bar('O1', int(DIA),
            [(xx+sgn*ho, y0-e-LD), (xx, y0-e-LD), (xx, y1+e+LD), (xx+sgn*ho, y1+e+LD)],
            count=4, bend_r=BEND_R, note='개구부 연직보강'))
    log.append(f"  개구부 O1: {len(bars)}종 x 4본")
    return bars

def run(name, ducts, out_svg):
    log = [f"\n{'='*82}", f"{name}", f"{'='*82}"]
    bars = place_h(ducts, log) + place_v(ducts, log) + place_opening(log)
    print("\n".join(log))
    rows, tot = bom(bars, use_true=True)
    print()
    print(bom_text(rows, tot, "── 철근 물량표 (굽힘 원호 반영) ──"))
    rowsS, totS = bom(bars, use_true=False)
    d = totS['Lsum'] - tot['Lsum']
    print(f"\n  굽힘 미반영(직각 교차점) 총연장 {totS['Lsum']/1000:.1f} m, "
          f"중량 {totS['W']:.1f} kg")
    print(f"  차이: 연장 +{d/1000:.2f} m ({100*d/tot['Lsum']:.2f}%), "
          f"중량 +{totS['W']-tot['W']:.1f} kg  ← 굽힘반지름 r={BEND_R:.0f} 미반영 시 과대계상")
    hol = [[(MANHOLE[0],MANHOLE[2]),(MANHOLE[1],MANHOLE[2]),
            (MANHOLE[1],MANHOLE[3]),(MANHOLE[0],MANHOLE[3])]]
    svg(out_svg, OUTLINE, hol, ducts, bars, name)
    print(f"  배근도: {out_svg}")
    return bars, tot

if __name__ == '__main__':
    d = os.path.dirname(os.path.abspath(__file__))
    print(f"격벽 H={H:.0f} 하부반폭={BOT_HALF:.0f} 상부반폭={TOP_HALF:.0f} "
          f"경사 {math.degrees(THETA):.2f}deg")
    print(f"피복 {COVER:.0f}  D{int(DIA)}@{SPACING:.0f}  ld={LD:.0f}  굽힘반지름 {BEND_R:.0f}")
    _, tA = run("Case A — 중앙 맨홀만", [], os.path.join(d, 'out_diaphragm_A.svg'))
    _, tB = run("Case B — 중앙 맨홀 + 덕트열 9공", DUCTS_B, os.path.join(d, 'out_diaphragm_B.svg'))
    print(f"\n{'='*82}\nA vs B  총연장 {tA['Lsum']/1000:.1f} → {tB['Lsum']/1000:.1f} m"
          f"   중량 {tA['W']:.1f} → {tB['W']:.1f} kg"
          f"   ({100*(tB['W']-tA['W'])/tA['W']:+.2f}%)")
