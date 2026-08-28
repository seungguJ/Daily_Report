# AGENTS.md — Daily_Report

이 저장소는 **콘텐츠 원본**이다. 화면은 별도 저장소 `Daily_Report_App`이 담당한다.
두 저장소는 아래 계약으로만 연결된다. 계약을 바꾸면 App도 같이 바꿔야 한다.

## 1. 저장소 관계

```
seungguJ/Daily_Report                 (이 저장소 · 콘텐츠 원본)
├─ reports/YYYY-MM-DD.md              AI 조사 리포트
├─ concerts/YYYY-MM-DD.md             콘서트 알림
├─ state/*_seen.json                  선정 이력 (중복 방지 + 구조화 인덱스)
└─ scripts/*.py                       카카오톡 발송
        │
        ├─ push → .github/workflows/send-kakao-report.yml    → 카카오톡
        ├─ push → .github/workflows/send-concert-alert.yml   → 카카오톡
        └─ push → .github/workflows/notify-app.yml
                    └─ repository_dispatch(content-updated)
                          ▼
seungguJ/Daily_Report_App             (웹앱 · Astro 정적 사이트)
└─ .github/workflows/deploy.yml
     1. 이 저장소를 `_source/`로 체크아웃
     2. src/lib/content.ts 가 _source 의 마크다운/JSON 파싱
     3. astro build → GitHub Pages 배포
```

App은 이 저장소를 **읽기 전용 원본**으로 본다. App에는 콘텐츠 사본을 두지 않는다.
`_source/`는 CI가 만드는 체크아웃 디렉터리이며 App 저장소에 커밋하지 않는다.

## 2. 콘텐츠 계약 (App이 의존하는 형식)

계약을 어기면 App 빌드는 성공하지만 화면에서 **조용히 누락**된다. 형식 변경은 반드시 App 수정과 한 쌍으로 진행한다.

### `reports/YYYY-MM-DD.md`

- 파일명이 곧 slug이자 날짜다. `YYYY-MM-DD.md` 외 형식 금지.
- 첫 줄: `[AI Morning Brief - YYYY-MM-DD]` — App이 제목 추출 후 본문에서 제거한다.
- 나머지는 자유 마크다운. App이 `markdown-it`으로 HTML 렌더링한다 (`html: false`, raw HTML 무시).

### `concerts/YYYY-MM-DD.md`

- 공연 하나당 `## 아티스트 | 공연제목` 섹션 하나.
- 섹션 본문 필드는 `- 라벨: 값` 형식. App이 읽는 라벨:

  | 라벨 | 필수 | 용도 |
  |---|---|---|
  | `공연일시` | 예 | `YYYY-MM-DD` 부분을 정규식으로 뽑아 정렬·지난 공연 숨김에 사용 |
  | `장소` | 예 | 카드 표시 |
  | `티켓오픈` | 아니오 | 카드 표시 |
  | `예매처` | 아니오 | 링크 라벨 |
  | `링크` | 아니오 | 예매 링크 |

- 같은 공연의 여러 회차는 `아티스트::제목::장소::링크`가 같으면 App이 한 카드로 합친다. 이 네 값을 회차마다 동일하게 쓸 것.
- `공연일시`에서 날짜를 못 뽑으면 삭제하지 않고 "날짜 확인 필요" 상태로 표시된다.

### `state/*_seen.json`

중복 방지용이지만 App의 **논문·도구 아카이브 데이터 원본**이기도 하다. 배열 형태를 유지할 것.

| 파일 | 필수 키 | 선택 키 |
|---|---|---|
| `papers_seen.json` | `title`, `link`, `selected_date` | `venue`, `publication_date`, `normalized_title` |
| `tools_seen.json` | `name`, `link`, `selected_date` | `announcement_date`, `canonical_project`, `github_repo` |
| `concerts_seen.json` | (App 미사용) | |

`selected_date`는 해당 항목이 실린 리포트 날짜(`YYYY-MM-DD`)여야 한다. App이 이 값으로 정렬하고 리포트로 역링크한다.

## 3. 새 feature 추가 절차

새 콘텐츠 종류·필드·디렉터리를 추가할 때 아래를 **순서대로** 수행한다. App 반영을 빠뜨리면 데이터는 쌓이는데 화면에 안 나온다.

1. **이 저장소**: 콘텐츠 생성/발송 로직 추가 (`scripts/`, 워크플로).
2. **이 문서 2장 갱신**: 새 디렉터리·파일명 규칙·필드를 계약에 명시한다. 문서화 없이 넘어가지 않는다.
3. **`Daily_Report_App` 수정** — 최소 4곳:
   - `src/lib/content.ts` — 타입 + `getX()` 로더. 원본이 없으면 빈 배열 반환(빌드 실패 금지).
   - `src/pages/<x>/index.astro` — 목록 화면. 기존 `page-intro` / `listing-wrap` / `SearchBox` 패턴 재사용.
   - `src/layouts/BaseLayout.astro` — `section` 유니온 타입 + 헤더 nav 링크.
   - `scripts/check-content.mjs` — 개수·정렬·필터 단언 추가.
4. **App 검증**: `npm run test:content && npm run build`. 두 개 다 통과해야 한다.
5. **양쪽 push**: 이 저장소를 먼저 push하고 App을 나중에 push한다. `notify-app.yml`이 App 재배포를 즉시 트리거한다.

`state/*_seen.json`에 키를 **추가만** 하는 경우는 App 수정 없이 안전하다. 키 이름 변경·삭제는 App 수정이 필요하다.

## 4. 배포 체인

- App은 아래 네 가지로 재배포된다: App main push / 매일 00:30 UTC(09:30 KST) cron / 수동 실행 / 이 저장소의 `repository_dispatch: content-updated`.
- `notify-app.yml`은 `GH_PAT` 시크릿을 쓴다 (스코프: `Daily_Report_App` repo write). 없으면 워크플로는 조용히 넘어가고 콘텐츠는 다음 cron에 반영된다.
- 카카오 워크플로는 `KAKAO_REST_API_KEY`, `KAKAO_REFRESH_TOKEN`, `KAKAO_CLIENT_SECRET`, `GH_PAT`(리프레시 토큰 갱신 저장용)를 쓴다.

## 5. 저장소 지식 그래프

`graphify-out/`에 두 저장소를 합친 지식 그래프가 있다. 구조 질문은 그래프를 먼저 조회한다.

```bash
graphify query "리포트 마크다운이 화면까지 어떻게 흐르나"
```

콘텐츠나 App 구조를 크게 바꾼 뒤에는 `/graphify . --update`로 갱신한다.
