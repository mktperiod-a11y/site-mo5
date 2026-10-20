# 작업 지침

## 개인정보 규칙 (항상 지킴)

- 코드·문서·커밋 메시지·PR 제목과 본문·이슈·댓글에 사이트 도메인, GitHub 계정 이름, 저장소 이름, 본명, 개인·회사 이메일을 적지 않는다.
- 커밋 작성자 이메일은 GitHub 비공개 주소(`…@users.noreply.github.com`)만 쓴다. 커밋 전에 `git log --format='%ae %ce'`로 확인한다.
- 사이트 주소는 코드에 적지 않는다. 코드에는 `https://site-url.invalid` 자리표시만 두고, 배포 워크플로가 `actions/configure-pages`의 `base_url`을 받아 빌드 결과물에서 바꿔 넣는다. 자리표시가 남으면 배포를 멈춘다.
- `CNAME` 파일을 두지 않는다. 배포는 GitHub Actions로 하고, 도메인은 저장소 Settings → Pages에만 둔다.
- README는 두지 않거나 서비스 이름·주소 없이 쓴다. `package.json`의 `name`도 일반 이름으로 한다.
- 수집 봇 User-Agent에 사이트 주소를 넣지 않는다.
- 저장소에 넣는 이미지는 sharp로 다시 저장해 EXIF·XMP·IPTC·텍스트·시간 정보를 지운다. SVG·HTML 안에 base64로 넣은 이미지도 같다. SVG는 `<metadata>`와 편집 도구(Inkscape·Illustrator 등)가 남긴 흔적도 지운다.
- API 키 등은 GitHub Secrets에만 넣고 대화·코드·로그에 쓰지 않는다. 워크플로에서 비밀 값을 출력하지 않는다.
- 다른 운영 사이트로 가는 링크를 넣지 않는다.
- 확인용 임시 파일(probe 등)은 PR 전에 지운다.

## 신원 노출 방지 (항상 지킴)

저장소(지금 파일과 커밋 기록)와 배포된 사이트만 보고 운영자 개인을 특정할 수 없어야 한다.

- 검색 등록 확인 코드(구글 서치콘솔·네이버 서치어드바이저 등)와 분석·광고 계정 ID는 소유자 확인 없이 사이트에 넣지 않는다. 확인용 HTML 파일(`google….html`, `naver….html`)도 같다.
  - 구글 확인 코드는 같은 구글 계정이면 사이트가 달라도 값이 같다. 여러 사이트에 붙이면 페이지 소스만 비교해도 같은 운영자로 묶인다. 2026-07 기록에서 사이트 다섯 곳이 같은 값을 쓴 것으로 확인했다.
  - 확인 코드는 공개된 페이지에 붙어 있어야 작동한다. Secrets로 옮기거나 다른 파일에 넣어도 방문자에게 그대로 보이므로 숨길 방법이 없다.
  - 네이버 확인 코드는 사이트마다 값이 달라 사이트끼리 묶이지 않는다.
  - 이 사이트에서는 소유자 결정(2026-10)으로 구글 확인 코드를 뺐다. 다시 넣자는 요청이 오면 위 내용을 먼저 알린다.
- 사이트 문구와 메타 태그에는 브랜드 이름만 쓴다. 운영자 이름, 연락처(이메일·전화), 사업자등록번호, 주소, `author` 메타, 개인 SNS·블로그 링크를 넣지 않는다. 문의 창구가 필요하면 먼저 소유자에게 묻는다.
- 이메일 주소는 어떤 파일에도 적지 않는다. 커밋 작성자 정보는 git 설정으로만 다룬다.
- 작업 PC의 사용자 폴더 이름이 드러나는 로컬 경로, 작성자 주석, 편집 도구가 남긴 정보를 파일에 남기지 않는다.
- 커밋 메시지에는 `Co-Authored-By` 줄까지만 쓴다. `Claude-Session:` 세션 링크 줄은 넣지 않는다.
- 이미 커밋된 식별 정보는 지우는 커밋만으로 사라지지 않는다. 공개 저장소의 기록과 GitHub에 남은 예전 커밋(SHA로 열림)에 그대로 남는다. 발견하면 소유자에게 알린다. 기록 재작성, 강제 push, 저장소 재생성은 소유자 확인을 받은 뒤에만 한다.
- 새로운 종류의 식별 정보를 찾으면 이 문서와 `privacy_check.py`에 함께 추가한다.

## 저장소 밖 설정 (소유자가 관리)

코드로는 막을 수 없어 소유자가 GitHub와 외부 서비스 설정에서 관리한다. 관련 작업을 하면 Claude가 상기시킨다.

- 공개 저장소에서 Pages로 배포하면 저장소의 Deployments(github-pages 환경)와 Actions 실행 기록에 사이트 주소가 보인다. 그래서 계정과 사이트가 이어진다. 끊으려면 저장소를 비공개로 돌린다. 개인 계정에서 비공개 저장소로 Pages를 쓰려면 GitHub Pro가 필요하다.
- GitHub 계정 이름은 실명, 개인 이메일, 다른 서비스 아이디와 겹치지 않게 한다. 프로필의 이름·소개·회사·위치·웹사이트·공개 이메일은 비워 둔다.
- 구글 서치콘솔처럼 확인 코드가 계정 단위인 서비스는, 한 계정으로 여러 사이트를 확인하면 사이트끼리 묶인다. 묶이지 않게 하려면 사이트마다 다른 계정을 써야 한다.

## 커밋과 병합

- 클라우드 세션의 기본 커밋 이메일은 비공개 주소가 아니다. 첫 커밋 전에 기존 기록에 있는 비공개 주소로 맞춘다.

  ```sh
  addr=$(git log --format='%ae' | grep '@users.noreply.github.com$' | grep -v '\[bot\]' | head -1)
  git config user.email "$addr"
  git config user.name "$(git log -1 --format='%an' --author="$addr")"
  ```

- PR은 Squash 또는 Rebase로 합친다. "Create a merge commit"은 병합 메시지(`Merge pull request #N from …`)에 계정 이름을 남긴다.
- 커밋 메시지에 GitHub 링크(계정·저장소 경로가 들어간 주소)를 쓰지 않는다.

## 자동 검사

- `.github/workflows/privacy-check.yml`이 push와 PR마다 `.github/scripts/privacy_check.py`를 실행한다.
  - 파일: 금지 문자열, `*.github.io` 주소, `CNAME`, probe 파일, 이미지의 EXIF·XMP·IPTC·텍스트·시간 정보(base64로 넣은 이미지 포함), SVG 편집 도구 흔적, 검색 등록 확인 토큰과 확인 파일, 이메일 주소·전화번호·사업자등록번호·분석·광고 계정 ID·사용자 폴더 경로
  - 커밋: 작성자·커미터 이메일, 병합 메시지의 계정 이름, 세션 링크, 커밋 메시지의 금지 문자열
- 금지 문자열은 Secrets의 `PRIVACY_PATTERNS`(한 줄에 하나)에만 있다. 값을 코드·대화·로그에 옮기지 않는다.
- push 전에 로컬에서 먼저 돌린다. 로컬에는 `PRIVACY_PATTERNS`가 없어 금지 문자열만 건너뛰고 나머지는 그대로 검사한다.

  ```sh
  python3 .github/scripts/privacy_check.py files
  python3 .github/scripts/privacy_check.py commits origin/main..HEAD
  ```

- 검사가 실패하면 원인을 고친다. 통과시키려고 검사 스크립트나 워크플로를 약하게 바꾸지 않는다.

## 이 저장소

- 빌드 도구 없는 정적 HTML 사이트다.
- 메인 순위는 `index.html` 하단의 `services` 배열 순서로 정한다.
- 배포는 `.github/workflows/deploy.yml`이 맡는다. 개인정보 검사 → 자리표시 치환 → Pages 배포 순서이고, 앞 단계가 실패하면 배포하지 않는다.
- 쓰는 Secret은 `PRIVACY_PATTERNS`(금지 문자열) 하나다.
- 사이트 결과물에서 `.github`, `README.md`, `CLAUDE.md`는 빠진다. 사이트에 올리지 않을 파일을 루트에 추가하면 `deploy.yml`의 제외 목록에도 넣는다.
