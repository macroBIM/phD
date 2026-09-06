#!/usr/bin/env python3
"""
case_opening.py — 개구부를 가로지르는 긴 철근의 절단 시나리오 전체를 실행.

핵심 주장: 개구부에 '별도의 장'을 두지 않는다. 경계 목록에 한 줄 추가할 뿐이며,
          외곽면과 코드상 구분되지 않는다(법선을 콘크리트 안쪽으로 통일).

시나리오
  S1 인력 : CAF 가 면에 안착 (면외). 단면 내 y 는 배근간격이 결정
  S2 제한 : 축방향으로 {psi>=0} 을 구해 조각으로 분해
  S3 판정 : 조각별 정착 ℓ_k >= ld 검사
  S4 재시도: 미달 조각이 있으면 그 단을 y 로 미끄러뜨려(2단계 척력과 같은 기구) 재분해
  S5 확정 : 그래도 미달이면 후크 or 폐기 → rho 감소로 기록
"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

H, BOT_HALF, TOP_HALF = 6600.0, 3000.0, 6000.0
COVER_OUT, COVER_OPEN, PHI = 50.0, 50.0, 16.0
LD = 40 * PHI                      # 640
SPACING = 200.0
THETA = math.atan((TOP_HALF - BOT_HALF) / H)

# 개구부: 편심 배치 (실무에서 점검구는 한쪽으로 치우친다)
OPEN_CX, OPEN_W = 2800.0, 1400.0
OPEN_Y0, OPEN_Y1 = 2300.0, 4300.0

def half_usable(y):
    """그 높이에서 외곽 피복선까지의 반폭 (경사면이므로 c/cos)"""
    return BOT_HALF + (TOP_HALF-BOT_HALF)*y/H - COVER_OUT/math.cos(THETA) - PHI/2

def open_band(y):
    """그 높이에서 개구부가 막는 x 구간 (피복 포함). 없으면 None"""
    m = COVER_OPEN + PHI/2
    if not (OPEN_Y0 - m <= y <= OPEN_Y1 + m):
        return None
    return (OPEN_CX - OPEN_W/2 - m, OPEN_CX + OPEN_W/2 + m)

def pieces(y):
    hw = half_usable(y)
    if hw <= 0: return []
    b = open_band(y)
    if b is None: return [(-hw, hw)]
    a0, a1 = max(b[0], -hw), min(b[1], hw)
    if a1 <= a0: return [(-hw, hw)]          # 개구부가 단면 밖
    out = []
    if a0 > -hw: out.append((-hw, a0))
    if a1 <  hw: out.append((a1, hw))
    return out

def slide_clear(y, limit=400.0):
    """S4: 미달 조각이 사라지도록 y 를 미끄러뜨린다. 최소 |dy| 를 찾는다."""
    for d in [i*2.0 for i in range(1, int(limit/2)+1)]:
        for t in (y - d, y + d):
            ps = pieces(t)
            if ps and all(b-a >= LD for a, b in ps):
                return t - y, t
    return None, None

print(f"격벽 H={H:.0f} 하부반폭={BOT_HALF:.0f} 상부반폭={TOP_HALF:.0f} 경사 {math.degrees(THETA):.2f}deg")
print(f"개구부 중심 x={OPEN_CX:.0f}, 폭 {OPEN_W:.0f}, y {OPEN_Y0:.0f}~{OPEN_Y1:.0f} (편심)")
print(f"피복 외곽 {COVER_OUT:.0f} / 개구부 {COVER_OPEN:.0f}, phi={PHI:.0f}, ld={LD:.0f}")
print()
hdr = f"{'y':>6} {'조각':>4} {'각 조각 길이':>26} {'미달':>4} {'S4 이동':>8} {'S4 후':>18} {'판정':>10}"
print(hdr); print("-"*len(hdr))

A_req = 0.0; A_place = 0.0; n_slide = 0; n_hook = 0; n_drop = 0; max_dy = 0.0
for k in range(1, int(H/SPACING)):
    y = k*SPACING
    ps = pieces(y)
    if not ps: continue
    L = [b-a for a, b in ps]
    A_req += 2*half_usable(y)                       # 소요 = 개구부 없을 때 연장
    bad = [v for v in L if v < LD]
    txt = " + ".join(f"{v:7.1f}" for v in L)
    if not bad:
        A_place += sum(L)
        print(f"{y:6.0f} {len(L):4d} {txt:>26} {0:4d} {'-':>8} {'-':>18} {'OK':>10}")
        continue
    dy, ynew = slide_clear(y)
    if dy is not None:
        L2 = [b-a for a, b in pieces(ynew)]
        A_place += sum(L2); n_slide += 1; max_dy = max(max_dy, abs(dy))
        print(f"{y:6.0f} {len(L):4d} {txt:>26} {len(bad):4d} {dy:+8.0f} "
              f"{' + '.join(f'{v:.0f}' for v in L2):>18} {'S4 해소':>10}")
    else:
        keep = [v for v in L if v >= LD]
        A_place += sum(keep); n_drop += len(bad)
        print(f"{y:6.0f} {len(L):4d} {txt:>26} {len(bad):4d} {'실패':>8} {'-':>18} {'S5 폐기':>10}")

print("-"*len(hdr))
print(f"S4 로 해소된 단 수: {n_slide} (최대 이동 {max_dy:.0f} mm)")
print(f"S5 폐기 조각 수   : {n_drop}")
print(f"rho = A_place / A_req = {A_place:.0f} / {A_req:.0f} = {100*A_place/A_req:.2f} %")
