# Sikk2d

React + TypeScript + PixiJS 8 기반 2D 애니메이션 편집기의 **단계 0 초기 환경**입니다. 빈 WebGL 캔버스, 레이어/속성 빈 상태와 12 FPS · 24 프레임 타임라인 셸을 제공합니다. 편집, PSD 변환, 저장, 출력 기능은 아직 없습니다.

## 새 checkout에서 실행

필수: Node.js 22.12 이상(22 또는 24 LTS 권장), npm, [uv](https://docs.astral.sh/uv/getting-started/installation/), WebGL을 지원하는 브라우저. Python은 `.python-version`으로 3.12를 지정하며 uv가 관리합니다.

```sh
git clone https://github.com/HyunseungJe/Sikk2d.git
cd Sikk2d
npm ci
uv python install 3.12
uv sync --locked
npm run dev
```

같은 컴퓨터의 브라우저에서 **http://127.0.0.1:5173/** 에 접속합니다. `Sikk2d`, 빈 체크무늬 캔버스, 하단 타임라인이 보이면 정상입니다. 포트가 사용 중이면 Vite가 출력한 주소를 사용합니다. `Ctrl+C`로 종료합니다.

원격 개발 머신에서 실행한다면 SSH 포트 포워딩을 사용하세요. 예: `ssh -L 5173:127.0.0.1:5173 <your-host>` 후 로컬 브라우저에서 위 주소로 접속합니다. 이 저장소는 공개 배포나 상시 미리보기를 구성하지 않습니다.

## 검증

```sh
npx playwright install chromium
# Linux에서 브라우저 시스템 라이브러리가 부족한 경우:
# npx playwright install --with-deps chromium
npm run check
```

`check`는 Prettier, warning을 허용하지 않는 type-aware ESLint 9, strict TypeScript, Vitest, Vite production build, Ruff lint/format, pytest, Playwright 순서로 실행합니다. Playwright는 개발 서버(React StrictMode 포함)와 production preview를 직접 시작하고 종료하며, 실제 PixiJS canvas 초기화·리사이즈·페이지 재로드와 24프레임 타임라인을 확인합니다. 실행 전 4173/5173 포트를 비워 두세요. 실제 PSD나 Google Drive는 필요하지 않습니다.

| 명령                                      | 용도                                    |
| ----------------------------------------- | --------------------------------------- |
| `npm run lint` / `npm run typecheck`      | 웹 코드 검사                            |
| `npm run format` / `npm run format:check` | 웹/문서 형식 적용/검사                  |
| `npm test`                                | Vitest 단위 smoke                       |
| `npm run build`                           | production build (`app/dist`)           |
| `npm run preview`                         | 빌드 확인 (http://127.0.0.1:4173/)      |
| `npm run test:e2e`                        | build 후 개발/production 브라우저 smoke |
| `npm run python:check`                    | Ruff 및 pytest                          |
| `uv run ruff format tools`                | Python format 적용                      |
| `uv run sikk2d-psd-import --help`         | PSD import CLI 진입점                   |

Python CLI는 도움말/버전만 제공하며 원본 PSD를 열거나 파생 파일을 만들지 않습니다. `psd-tools`와 Pillow 의존성 및 dev 도구는 `uv.lock`, 웹 의존성은 `package-lock.json`으로 고정합니다.

## 구조와 비공개 자산

- `app/src/canvas`: PixiJS canvas 생명주기
- `app/src/App.tsx`: 초기 화면과 timeline shell
- `app/tests/e2e`: 브라우저 smoke
- `tools/psd_import`: Python CLI와 tests

사용자 테스트 PSD와 파생 PNG/manifest는 **항상 저장소 밖**에 보관하세요. 실행 환경의 보관 위치는 `/tmp/sasfairy-private-assets/SAS-1`이며 영구 보관 위치가 아닙니다. 원본은 Paperclip 원본 작업 첨부에서 복구합니다. `.gitignore`는 PSD/PSB와 알려진 자산 폴더를 제외하지만 모든 파생 파일을 자동으로 구분하지는 않습니다. 사용자 artwork를 저장소 안으로 복사하지 마세요.

다음 기능 단계 착수 전에 PRD/PoC의 연결 변경 확인, reparent transform, pivot, FPS 관련 차이를 정리해야 합니다. 이번 단계는 해당 동작을 구현하지 않습니다.
