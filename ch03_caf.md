# 제3장 CAF 이론 정식화

## 3.1 포텐셜 함수 정의

CAF는 단면 경계 $\partial\Omega$ 로부터의 인력항과 장애물 집합 $\mathcal{O}$ 로부터의
척력항으로 구성된다. 철근 후보점 $\mathbf{x} \in \Omega$ 에 대하여

$$U_{\text{CAF}}(\mathbf{x}) = k_a \, U_{\text{att}}(\mathbf{x};\partial\Omega)
   + \sum_{o \in \mathcal{O}} k_r \, U_{\text{rep}}(\mathbf{x}; o)$$

로 두고, 배근은 $-\nabla U_{\text{CAF}}$ 를 따르는 이완(relaxation)으로 얻는다.

> 작성 예정: $U_{\text{att}}$ 를 피복거리 기반으로 정의하는 식, $U_{\text{rep}}$ 의 유효반경
> $\rho_0$ 와 절단(cut-off), 기호표(notation table).

## 3.2 H1 — well-definedness (방향정합성 조건)

**H1 (주장).** 인력항이 정의하는 방향과 척력항이 정의하는 방향이 정합적일 때,
$U_{\text{CAF}}$ 는 $\Omega$ 내부에서 잘 정의되며 그 기울기장은 유일하다.

- 필요한 것: 경계 법선의 부호 규약, 다중 경계(외곽/중공)에서의 안쪽 방향 정의,
  경계 근방에서의 미분가능성.
- 증명 전략: 부호거리함수(signed distance)의 국소 성질 → 방향정합성 조건 → 유일성.

> 작성 예정: 조건의 형식적 진술과 증명. 반례(방향이 뒤집히는 오목부) 그림.

## 3.3 H3 — 기존 APF는 CAF의 특수 사례

**H3 (주장).** 목표를 점 $\mathbf{x}_g$ 로, 경계를 무한대로 두면 $U_{\text{CAF}}$ 는
고전 APF 로 환원된다.

- 환원 사상(reduction map)을 명시하고, 어떤 항이 사라지는지 항별로 대응시킨다.
- 이 명제가 성립하면 제4장의 안정조건은 APF 문헌의 결과를 특수해로 포함하게 된다.

> 작성 예정: 환원 절차의 단계별 유도.
