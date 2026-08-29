# 제3장 Cover-Attractive Field 이론 정식화

## 3.1 포텐셜 함수 정의

Cover-Attractive Field(이하 CAF)의 포텐셜은 인력항과 척력항의 합이다.

$$U(\mathbf{x}) = U_{\text{attr}}(\mathbf{x}) + U_{\text{rep}}(\mathbf{x})$$

인력항은 유효 attractor 까지의 거리에 대한 2차 포텐셜로 둔다.

$$U_{\text{attr}}(\mathbf{x}) = \tfrac{1}{2}\, k \; d\!\left(\mathbf{x},\, \Gamma_{\text{eff}}(\mathbf{x})\right)^{2}$$

여기서 $\Gamma_{\text{eff}}(\mathbf{x})$ 는 점 $\mathbf{x}$ 에서의 **유효 attractor** 이며,
단면 경계에서 피복두께만큼 오프셋된 **1차원 곡선**이다.

**핵심 차별점.** attractor 가 상수가 아니라 **상태 $\mathbf{x}$ 에 의존**한다는 것이다.
기존 APF 는 $\Gamma_{\text{eff}}$ 가 상수점 $\mathbf{x}_0$ 로 고정된 경우이며, 이는 CAF 의
특수 사례다(3.3). 목표를 0차원 점에서 1차원 곡선으로 올린 이 일반화가 논문의 이론적 축이다.

## 3.2 H1 — well-definedness (방향정합성 조건)

**H1.** CAF 는 well-defined 이다. attractor 판별 조건을 방향정합성(내적 조건)으로 명시적으로
정의하고 증명한다.

판별 조건은 세그먼트 법선과 벽면 법선의 내적으로 준다.

$$\mathbf{n}_{\text{seg}} \cdot \mathbf{n}_{\text{wall}} \;\le\; \alpha_{\text{th}}$$

- **현재 구현값**: `macroBIM/macroBIM` 의 `physics.js` 에서
  $\alpha_{\text{th}} = $ `OPPOSITE_THRESHOLD` $= -0.6$.
- 이는 $\theta \ge \arccos(-0.6) \approx 126.87^\circ$ 에 해당한다 — 즉 정반대 방향($180^\circ$)
  에서 $\pm 53.13^\circ$ 이내를 허용한다.

**검증 절차.** $\theta$ 를 $0^\circ$–$90^\circ$ 로 스윕하며 세 사례연구에서 두 지표를 측정한다.

| 지표 | 정의 |
|---|---|
| $f_1(\alpha)$ | 수렴 실패율 |
| $f_2(\alpha)$ | 오귀속률 — 세그먼트가 엉뚱한 경계에 붙는 비율 |

비볼록 단면(I빔)과 곡선 경계(중공교각)에서 민감도가 가장 클 것으로 예상한다.

> 다음 작업: $\alpha$ 스윕 실증 검증(0°–90°, 실패율·오귀속률 측정).

## 3.3 H3 — 기존 APF는 CAF의 특수 사례

**H3.** 기존 APF 는 CAF 의 **0차원 퇴화(degenerate) 특수 사례**다.
$\Gamma_{\text{eff}}(\mathbf{x}) \equiv \{\mathbf{x}_0\}$ 로 두면 CAF 의 인력항은 고전 APF 의
인력항으로 환원된다. 이 명제가 논문에서 가장 강력한 이론적 기여다.

**주의해야 할 함정.** "점은 길이 0 인 곡선"이라는 정의상 자명함에 그치면 기여가 되지 않는다.
따라서 이 일반화가 **실제로 여는 새로운 문제 클래스**를 정리(theorem) 형태로 명시해야 한다.
즉 $\Gamma_{\text{eff}}$ 가 1차원이고 상태의존적일 때 비로소 성립하는 성질 — placement 문제의
해 존재성, 다중경계 편입(제5장), 위상 일반화(제6장) — 을 환원 사상과 함께 진술한다.
