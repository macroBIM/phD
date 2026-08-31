#!/usr/bin/env python3
"""
case_boxgirder.py — 1-셀 박스거더에서 허용영역 A 를 계산한다 (부록 A.6 1단계).

제원 주의: 아래 치수는 macroBIM 단면 엔진의 1-셀 박스 기본값 계열을 따른
**도해용 제원**이다. 특정 실교량 도면이 아니며, 덕트 위치·간격은 진단을
보이기 위해 저자가 정한 값이다(7.4의 KSR2015A032 제원과 다름).
"""
import sys, math
sys.path.insert(0, ".")
from admissible import Section, report, svg

COVER = {'outer': 50.0, 'void': 40.0, 'duct': 40.0}   # 가정: 외기면 50, 중공면 40, 덕트면 40

# ── 도해용 1-셀 박스 (y 위쪽, 원점 하단 중앙) ──
H, T_TOP, T_BOT = 6600.0, 400.0, 600.0
BOT_HALF, TOP_HALF = 3000.0, 6000.0
WEB_T = 500.0
Y_WEB0, Y_WEB1 = T_BOT, H - T_TOP
X_O0, X_O1 = 3000.0, 4000.0        # 복부 외면: 하단 x, 상단 x (경사)

OUTER = [(-BOT_HALF, 0), (BOT_HALF, 0), (X_O0, Y_WEB0), (X_O1, Y_WEB1),
         (TOP_HALF, Y_WEB1), (TOP_HALF, H), (-TOP_HALF, H), (-TOP_HALF, Y_WEB1),
         (-X_O1, Y_WEB1), (-X_O0, Y_WEB0)]
VOID = [(-(X_O0-WEB_T), Y_WEB0), (X_O0-WEB_T, Y_WEB0),
        (X_O1-WEB_T, Y_WEB1), (-(X_O1-WEB_T), Y_WEB1)]

def web_center_x(y):
    """높이 y 에서 복부(우측) 중심선의 x."""
    t = (y - Y_WEB0) / (Y_WEB1 - Y_WEB0)
    return (X_O0 + t*(X_O1 - X_O0)) - WEB_T/2.0

def ducts(cluster_gap, r=50.0):
    """복부에 2단 클러스터 1조씩(좌우 대칭) + 하부 슬래브에 4공."""
    out = []
    y1 = 3000.0
    y2 = y1 + cluster_gap                       # 중심 간 수직 거리
    for s in (+1, -1):
        out.append((s*web_center_x(y1), y1, r))
        out.append((s*web_center_x(y2), y2, r))
    for x in (-1500.0, -500.0, 500.0, 1500.0):  # 하부 슬래브 텐던
        out.append((x, 300.0, r))
    return out

def gap_between(sec, i, j):
    (x1, y1, r1), (x2, y2, r2) = sec.ducts[i], sec.ducts[j]
    return math.hypot(x2-x1, y2-y1) - r1 - r2

if __name__ == "__main__":
    STEP = 25.0
    for label, gap in (("여유 클러스터", 300.0), ("빠듯한 클러스터", 190.0)):
        sec = Section(OUTER, [VOID], ducts(gap), COVER)
        g = gap_between(sec, 0, 1)
        print(f"\n=== {label}: 덕트 표면 간격 {g:.1f} mm "
              f"(철근이 지나려면 {2*COVER['duct']:.0f} + 지름 이 필요) ===")
        for phi, name in ((15.9, "D16"), (31.8, "D32")):
            grid, clear, xywh, comps = report(f"{label}/{name}", sec, phi, STEP)
            need = 2*COVER['duct'] + phi
            print(f"        → 클러스터 통로 판정: 필요 {need:.1f} mm vs 실제 {g:.1f} mm "
                  f"→ {'통과 가능' if g >= need else '통과 불가'}")
            if label == "빠듯한 클러스터":
                svg(f"/tmp/A_{name}.svg", sec, grid, xywh, STEP,
                    f"admissible set  phi={name}  duct gap={g:.0f}mm")

def diagnose(label, gap, step=25.0):
    from admissible import corridor, components_in
    sec = Section(OUTER, [VOID], ducts(gap), COVER)
    g = gap_between(sec, 0, 1)
    print(f"\n=== {label} — 덕트 표면 간격 {g:.1f} mm ===")
    for phi, name in ((15.9, "D16"), (31.8, "D32")):
        grid, clear, xywh, comps = report(f"{label}/{name}", sec, phi, step)
        best, at = corridor(sec, 0, 1, phi)
        # 우측 복부 띠 안에서만 연결성분을 센다
        band = lambda x, y: (x > 2000) and (Y_WEB0 < y < Y_WEB1)
        wc = components_in(sec, grid, xywh, step, band)
        wa = [len(c)*step*step/1e6 for c in wc[:3]]
        print(f"        국소통로 최대여유 = {best:+7.1f} mm  → {'통과 가능' if best >= 0 else '통과 불가'}")
        print(f"        복부 띠 연결성분 = {len(wc)}개, 면적(m²) = {[round(a,3) for a in wa]}")
        svg(f"/tmp/A_{label}_{name}.svg", sec, grid, xywh, step,
            f"{label} / {name}  duct surface gap={g:.0f}mm  corridor={best:+.0f}mm")

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "diag":
    diagnose("wide", 300.0)
    diagnose("tight", 190.0)
