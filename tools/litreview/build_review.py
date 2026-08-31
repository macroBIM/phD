#!/usr/bin/env python3
"""
build_review.py — papers.csv 를 2장 원고와 gap 판정으로 바꾼다.

  python3 build_review.py            # 요약 + 빈 셀 진단
  python3 build_review.py --md       # 2장에 붙일 마크다운 표
  python3 build_review.py --prisma   # 검색 → 선별 → 확정 편수 (2장 조사절차용)
  python3 build_review.py --bib      # BibTeX 초안 (확인된 것만)

축의 뜻은 protocol(부록 B) 참조.
"""
import csv, sys, collections

AX = {
 'output':        {'Q':'소요량만','P':'위치·좌표','R':'경로·형상','C':'간섭판정만'},
 'mechanism':     {'RULE':'규칙·파라메트릭','OPT':'최적화','FIELD':'장·포텐셜','LEARN':'학습','TOOL':'도구'},
 'justification': {'GEO':'기하만','CODE':'기준충족','MECH':'역학 목적함수','NONE':'없음'},
 'clash':         {'POST':'detect-and-fix','CONSTR':'생성시 회피','NONE':'다루지 않음'},
}
# 이 논문이 비어 있다고 주장하려는 칸 — 여기에 선행연구가 들어오면 gap 문장을 고쳐야 한다.
CLAIM_CELLS = [
    ('output=P', 'mechanism=FIELD', '장으로 위치를 생성'),
    ('output=P', 'justification=MECH', '위치를 역학으로 정당화'),
    ('output=P', 'clash=CONSTR', '생성 시 회피로 위치 결정'),
    ('justification=MECH', 'clash=CONSTR', '역학 근거 + 생성시 회피'),
]

def load(path='papers.csv'):
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f))

def cross(rows, a, b):
    t = collections.Counter()
    for r in rows:
        t[(r.get(a,'?').strip(), r.get(b,'?').strip())] += 1
    return t

def show(rows, a, b):
    print(f"\n── {a} × {b} ──")
    ka, kb = list(AX[a]), list(AX[b])
    t = cross(rows, a, b)
    print(f"{'':<16}" + "".join(f"{AX[b][k][:10]:>12}" for k in kb))
    for x in ka:
        print(f"{AX[a][x][:14]:<16}" + "".join(f"{t[(x,y)] or '·':>12}" for y in kb))

def main():
    rows = load()
    print(f"등록 문헌 {len(rows)}편  |  서지 미확인 {sum(1 for r in rows if r['verified'].strip()!='yes')}편")
    for a, b in (('output','mechanism'), ('justification','clash'), ('output','justification')):
        show(rows, a, b)

    print("\n── gap 판정 (비어 있어야 주장이 선다) ──")
    for c1, c2, desc in CLAIM_CELLS:
        (k1,v1), (k2,v2) = (c1.split('='), c2.split('='))
        hit = [r['id'] for r in rows if r.get(k1,'').strip()==v1 and r.get(k2,'').strip()==v2]
        enough = len(rows) >= 25
        if hit:
            mark = f"선행연구 {len(hit)}편: {', '.join(hit)} → 주장 수정 필요"
        elif enough:
            mark = "비어 있음 → 주장 가능"
        else:
            mark = f"비어 있으나 표본 부족({len(rows)}/25) → 아직 아무 것도 주장할 수 없음"
        print(f"  [{desc:<22}] {mark}")

    thin = [k for k,v in collections.Counter(r['mechanism'].strip() for r in rows).items()]
    need = {'RULE':5,'OPT':5,'FIELD':5,'LEARN':3,'TOOL':3}
    cnt = collections.Counter(r['mechanism'].strip() for r in rows)
    print("\n── 축별 최소 확보량 ──")
    for k, n in need.items():
        print(f"  {AX['mechanism'][k]:<14} {cnt[k]:>2} / {n} {'✓' if cnt[k]>=n else '부족'}")

    if '--prisma' in sys.argv:
        try:
            with open('screening.csv', encoding='utf-8') as f:
                sc = [r for r in csv.DictReader(f) if r.get('found_id','').strip()]
        except FileNotFoundError:
            sc = []
        dec = collections.Counter(r['decision'].strip().lower() for r in sc)
        print("\n── 조사 절차 (2장에 그대로 옮긴다) ──")
        print(f"  R1 검색으로 확인한 후보      {len(sc):>4} 편")
        print(f"     제목·초록에서 제외        {dec['exclude']:>4} 편")
        print(f"     전문 확인 대상            {dec['include']:>4} 편")
        print(f"  R2 코딩 완료(papers.csv)     {len(rows):>4} 편")
        print(f"     서지 확인 완료            {sum(1 for r in rows if r['verified'].strip()=='yes'):>4} 편")
        srcs = collections.Counter(r['source'].strip() for r in sc)
        if srcs:
            print("  출처별: " + ", ".join(f"{k} {v}" for k, v in srcs.most_common()))
        if not sc:
            print("  (screening.csv 가 비어 있다 — R1 을 아직 시작하지 않았다)")

    if '--bib' in sys.argv:
        print()
        for r in rows:
            if r['verified'].strip() != 'yes':
                print(f"% {r['id']}: 서지 미확인 — 원문 확보 후 채울 것", file=sys.stderr)
                continue
            print(f"@article{{{r['id']},\n  author  = {{{r['authors']}}},\n  title   = {{{r['title']}}},"
                  f"\n  journal = {{{r['venue']}}},\n  year    = {{{r['year']}}},"
                  + (f"\n  doi     = {{{r['doi']}}}," if r['doi'].strip() else "") + "\n}}\n")

    if '--md' in sys.argv:
        print("\n\n## 2장용 표\n")
        for m in AX['mechanism']:
            sel = [r for r in rows if r['mechanism'].strip()==m]
            if not sel: continue
            print(f"\n### {AX['mechanism'][m]}\n")
            print("| 문헌 | 산출 | 정당화 | 간섭 | 주장 | 한계 |")
            print("|---|---|---|---|---|---|")
            for r in sorted(sel, key=lambda r: r['year']):
                print(f"| {r['authors']} ({r['year']}) | {AX['output'].get(r['output'].strip(),'?')} "
                      f"| {AX['justification'].get(r['justification'].strip(),'?')} "
                      f"| {AX['clash'].get(r['clash'].strip(),'?')} | {r['claim']} | {r['limitation']} |")

if __name__ == '__main__':
    main()
