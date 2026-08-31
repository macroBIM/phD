# 부록 B. 문헌 조사 프로토콜

> 2장을 채우기 위한 실행 절차다. 목적은 읽은 논문 수를 늘리는 것이 아니라
> **1.2절의 gap 문장을 방어 가능하게 만드는 것**이며, 방어할 수 없다면 gap 문장을 고치는 것이다.

## B.1 무엇을 방어해야 하는가

현재 gap 문장은 다음을 주장한다.

1. 단면 형상만으로 목표 위치를 자동·생성적으로 도출하는 이론적 틀이 없다.
2. avoidance-by-construction 의 이론적·정량적 근거가 없다.

**둘 다 "없다"는 부재(不在) 주장이다.** 부재는 표본 없이 주장할 수 없다. 현재 확보 문헌은
배근 분야 2편(Liu 2020, Xu 2022) + 로보틱스 2편이며, 이 상태로는 어느 것도 말할 수 없다.

## B.2 분류 축

각 문헌을 아래 네 축으로 코딩한다. 축은 gap 문장에서 역산해 만들었다 —
**주장하려는 칸이 비어 있는지를 보기 위한 축**이다.

| 축 | 값 | 뜻 |
|---|---|---|
| `output` 무엇을 내놓는가 | `Q` / `P` / `R` / `C` | 소요량만 / 위치·좌표 / 경로·형상 / 간섭판정만 |
| `mechanism` 어떻게 정하는가 | `RULE` / `OPT` / `FIELD` / `LEARN` / `TOOL` | 규칙 / 최적화 / 장 / 학습 / 도구지원 |
| `justification` 왜 그 자리인가 | `GEO` / `CODE` / `MECH` / `NONE` | 기하만 / 기준충족 / 역학 목적함수 / 없음 |
| `clash` 간섭을 언제 다루는가 | `POST` / `CONSTR` / `NONE` | 생성 후 탐지·수정 / 생성 시 회피 / 다루지 않음 |

보조 항목: `domain`, `member`, `dim`(2D/3D), `obstacles`(none·duct·opening·rebar·mep),
`validation`(none·example·case·drawing·experiment), `n_cases`, `relevance`(1–5).

### 주장 칸

아래 조합이 **비어 있어야** 1.2의 gap 이 선다. 하나라도 차면 그 문장을 고쳐야 한다.

| 조합 | 뜻 |
|---|---|
| `output=P` × `mechanism=FIELD` | 장으로 위치를 생성 |
| `output=P` × `justification=MECH` | 위치를 역학으로 정당화 |
| `output=P` × `clash=CONSTR` | 생성 시 회피로 위치 결정 |
| `justification=MECH` × `clash=CONSTR` | 역학 근거 + 생성시 회피 |

## B.3 반드시 파야 할 인접 분야 — 여기서 gap 이 무너질 수 있다

조사를 미루면 가장 늦게, 가장 아프게 발견되는 것들이다. **먼저 본다.**

| 분야 | 왜 위험한가 |
|---|---|
| **스트럿-타이 모델(STM)** | 역학(응력장)이 철근의 위치를 정하는 고전적 방법이다. "위치를 역학으로 정당화"라는 칸을 이미 차지하고 있을 수 있다 |
| **주응력 궤적 기반 배근** | 응력 궤적을 따라 철근을 놓는 연구 계열. 부록 A 의 수요장과 발상이 겹친다 |
| **위상최적화 기반 보강재 배치** | "역학적 수요 분포 → 재료 배치"를 이미 푸는 분야. A.2 의 정식화와 가장 가깝다 |
| **콘크리트 3D 프린팅 보강재 경로계획** | 최근 문헌이 많고 장·경로 기반 방법이 흔하다 |
| **점 분포 이론**(CVT, 최적수송, Poisson-disk) | 도메인 문헌은 아니지만 A.2 해법의 출처이자 신규성의 경계 |

**이 다섯을 먼저 조사한다.** 여기서 선행연구가 나오면 논문의 자리가 바뀌므로,
나머지를 조사하기 전에 알아야 한다.

## B.4 검색

### 검색어 (영문, 조합해 사용)

```
(rebar OR reinforcement) AND (layout OR placement OR arrangement OR detailing)
                         AND (automat* OR generative OR optimi* OR algorithm*)
reinforcement detailing automation
rebar congestion            rebar clash detection BIM
constructability reinforcement
"potential field" AND (rebar OR reinforcement OR construction)
strut-and-tie AND (layout OR automat*)
"principal stress" AND (trajectory OR trajectories) AND reinforcement
topology optimization AND (reinforcement OR rebar) AND concrete
3D printed concrete AND reinforcement AND (path OR planning)
centroidal Voronoi tessellation      capacity-constrained point distribution
"optimal transport" AND (sampling OR "blue noise")      Poisson disk sampling
```

### 검색어 (국문)

```
배근 자동화 / 철근 상세 자동화 / 배근 간섭 / 철근 간섭 검토
RC 배근 최적설계 / 철근 배치 최적화 / 스트럿-타이 / 응력 궤적 배근
```

### 데이터베이스

Scopus, Web of Science, Google Scholar, ASCE Library, ScienceDirect(Automation in
Construction, Engineering Structures), Springer, 그리고 국문은 KCI·RISS·DBpia.
학술대회 논문(ISARC, ICCCBE)도 이 분야에서 비중이 크다.

## B.5 포함·제외 기준

**포함**: 철근의 위치·형상을 자동으로 만들거나, 배근 간섭을 다루거나,
A.2 의 해법 계열(점분포·최적수송)을 제공하는 문헌.

**제외**: 재료·실험만 다루는 것, 배근과 무관한 BIM 일반론, 본문 확인이 불가능한 것.

기간 제한은 두지 않는다(고전 포함). 다만 자동화 계열은 2010년 이후를 중심으로 본다.

## B.6 절차 — 3라운드

| 라운드 | 할 일 | 목표 |
|---|---|---|
| R1 선별 | B.3 의 다섯 분야 먼저, 그다음 B.4 검색어. 제목·초록만 보고 거른다 | 후보 80–120편 |
| R2 코딩 | 본문 확인 후 `papers.csv` 의 축을 채운다. 못 채우면 relevance 를 낮춘다 | 확정 30–40편 |
| R3 스노볼링 | 확정 문헌의 인용·피인용을 훑어 누락을 메운다 | 빈 축 보완 |

**축별 최소 확보량**: `RULE` 5, `OPT` 5, `FIELD` 5, `LEARN` 3, `TOOL` 3.
전체 25편 미만에서는 어떤 부재 주장도 하지 않는다 — 스크립트가 이를 막는다.

## B.7 산출물

```
tools/litreview/screening.csv     R1 선별 기록 — 검색으로 본 후보 1편 = 1행
tools/litreview/papers.csv        R2 확정 문헌 1편 = 1행. 네 축을 코딩한다
tools/litreview/build_review.py   집계 · gap 판정 · 2장 원고 생성

python3 build_review.py           교차표 + 주장 칸 판정 + 축별 확보량
python3 build_review.py --prisma  검색 → 선별 → 확정 편수 (2장 조사절차 서술용)
python3 build_review.py --md      2장에 그대로 붙일 마크다운 표
python3 build_review.py --bib     BibTeX 초안 (서지 확인된 것만; 나머지는 경고)
```

**두 파일을 나눈 이유.** R1 에서 본 후보는 대부분 버려지지만 **몇 편을 보고 몇 편을 왜
버렸는지가 2장에 들어가야 한다**(조사의 재현성). `screening.csv` 는 그 기록이고
(`decision` 은 include/exclude, `reason` 에 한 줄), `papers.csv` 는 살아남은 것만 담는다.
`--prisma` 가 두 파일에서 편수를 뽑아 2장 서술에 쓸 숫자를 만든다.

`verified` 열은 **서지사항을 원문으로 확인했는지**를 기록한다. 현재 4편 모두 `no` 다 —
Liu 2020·Xu 2022 는 제목조차 확인되지 않은 상태이므로, 인용하기 전에 원문을 확보해야 한다.

## B.8 gap 이 무너졌을 때

주장 칸이 차면 **문장을 고치지 논문을 접지 않는다.** 대응은 세 갈래다.

1. **좁힌다** — 예: 선행연구가 3D 부재를 다뤘다면 "임의 위상 2D 단면에서"로 한정.
2. **옮긴다** — 위치 생성이 이미 있다면, 기여를 "덕트·개구부가 정의역과 수요 양쪽에
   관여하는 통합 정식화"로 옮긴다(A.3).
3. **인정하고 비교로 간다** — 선행연구를 baseline 으로 삼아 정량 비교를 기여로 만든다(H5).

어느 쪽이든 **조사 전에 결정할 수 없다.** 그래서 이 프로토콜이 먼저다.
