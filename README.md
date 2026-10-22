# Sikk2d

React + TypeScript + PixiJS 8 기반 2D 애니메이션 편집기 PoC입니다. Python CLI로 PSD를 투명 PNG 레이어와 manifest v1 bundle로 변환합니다. 웹 앱은 빈 WebGL 캔버스, 레이어/속성 빈 상태와 12 FPS · 24 프레임 타임라인 셸을 제공합니다. 웹 bundle 로드·편집·저장·출력은 후속 단계입니다.

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

`check`는 Prettier, warning을 허용하지 않는 type-aware ESLint 9, strict TypeScript, Vitest, Vite production build, Ruff lint/format, pytest, Playwright 순서로 실행합니다. Playwright는 개발 서버(React StrictMode 포함)와 production preview를 직접 시작하고 종료하며, 실제 PixiJS canvas 초기화·리사이즈·페이지 재로드와 24프레임 타임라인을 확인합니다. 실행 전 4173/5173 포트를 비워 두세요. Python integration 단계는 실제 PSD 세 개를 변환합니다. 비공개 PSD가 없는 checkout에서는 각 파일 경로와 복구 안내를 명시하고 skip합니다. Google Drive 연결은 필요하지 않습니다.

| 명령                                      | 용도                                         |
| ----------------------------------------- | -------------------------------------------- |
| `npm run lint` / `npm run typecheck`      | 웹 코드 검사                                 |
| `npm run format` / `npm run format:check` | 웹/문서 형식 적용/검사                       |
| `npm test`                                | Vitest 단위 smoke                            |
| `npm run build`                           | production build (`app/dist`)                |
| `npm run preview`                         | 빌드 확인 (http://127.0.0.1:4173/)           |
| `npm run test:e2e`                        | build 후 개발/production 브라우저 smoke      |
| `npm run python:check`                    | Ruff, synthetic 테스트, 실제 PSD integration |
| `uv run ruff format tools`                | Python format 적용                           |
| `uv run sikk2d-psd-import --help`         | PSD import CLI 진입점                        |

## PSD 변환

원본은 읽기 전용이며 출력은 **Git checkout 밖의 새 디렉터리 또는 빈 디렉터리**여야 합니다. 기존 bundle을 덮어쓰지 않습니다.

```sh
uv run sikk2d-psd-import \
  /tmp/sasfairy-private-assets/SAS-1/test1.psd \
  /tmp/sasfairy-private-assets/SAS-1/bundles/test1 --compare
```

출력은 `manifest.json`, `layers/layer-*.png`, `--compare` 지정 시 `comparison.json`입니다. 비교 통과는 종료 코드 0, 비교 불일치는 1, 입력·출력 오류는 2입니다. 재실행은 다른 빈 출력 경로를 사용하세요. 변환만 하려면 `--compare`를 생략합니다.

[Manifest v1 규칙](docs/manifest-v1.md)과 [JSON Schema](tools/psd_import/manifest-v1.schema.json)에 필드, 순서, 숨김·빈 레이어 및 지원 범위를 설명합니다. `psd-tools[composite]`, Pillow, jsonschema와 dev 도구는 `uv.lock`, 웹 의존성은 `package-lock.json`으로 고정합니다.

외부 테스트 PSD 위치를 바꾸려면 `SIKK2D_TEST_ASSETS`를 지정합니다. 파일 이름은 `test1.psd`~`test3.psd`입니다.

```sh
SIKK2D_TEST_ASSETS=/path/outside/repository npm run python:check
```

Synthetic 테스트는 작은 PSD를 실제 파일로 생성해 변환합니다. Integration은 세 PSD 모두를 읽어 768×768 canvas, 20/15/18 레이어, mask alpha, 반복 변환 동일성, 원본 무변경과 재합성 픽셀 차이를 검사합니다. PSD와 파생물은 임시 디렉터리에서만 사용합니다.

## 구조와 비공개 자산

- `app/src/canvas`: PixiJS canvas 생명주기
- `app/src/App.tsx`: 초기 화면과 timeline shell
- `app/tests/e2e`: 브라우저 smoke
- `tools/psd_import`: Python CLI와 tests

사용자 테스트 PSD와 파생 PNG/manifest는 **항상 저장소 밖**에 보관하세요. 실행 환경의 보관 위치는 `/tmp/sasfairy-private-assets/SAS-1`이며 영구 보관 위치가 아닙니다. 원본은 Paperclip 원본 작업 첨부에서 복구합니다. `.gitignore`는 PSD/PSB, PNG, `manifest.json`, `comparison.json`과 알려진 자산 폴더를 제외합니다. CLI도 Git checkout 안으로의 출력을 거부합니다. 사용자 artwork를 저장소 안으로 복사하지 마세요.

다음 기능 단계 착수 전에 PRD/PoC의 연결 변경 확인, reparent transform, pivot, FPS 관련 차이를 정리해야 합니다. 이번 단계는 해당 동작을 구현하지 않습니다.
