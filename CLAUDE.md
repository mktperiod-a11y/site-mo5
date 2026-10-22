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
  - 파일: 금지 문자열, `*.github.io` 주소, `CNAME`, probe 파일, 이미지의 EXIF·XMP·IPTC·텍스트·시간 정보(base64로 넣은 이미지와 ICO 안의 이미지 포함), SVG 편집 도구 흔적, 검색 등록 확인 토큰과 확인 파일, 이메일 주소·전화번호·사업자등록번호·분석·광고 계정 ID·사용자 폴더 경로
  - 커밋: 작성자·커미터 이메일, 병합 메시지의 계정 이름, 세션 링크, 커밋 메시지의 금지 문자열
- 금지 문자열은 Secrets의 `PRIVACY_PATTERNS`(한 줄에 하나)에만 있다. 값을 코드·대화·로그에 옮기지 않는다.
- push 전에 로컬에서 먼저 돌린다. 로컬에는 `PRIVACY_PATTERNS`가 없어 금지 문자열만 건너뛰고 나머지는 그대로 검사한다.

  ```sh
  python3 .github/scripts/privacy_check.py files
  python3 .github/scripts/privacy_check.py commits origin/main..HEAD
  ```

- 검사가 실패하면 원인을 고친다. 통과시키려고 검사 스크립트나 워크플로를 약하게 바꾸지 않는다.

## 이 저장소

- 빌드 도구 없는 정적 HTML 사이트다. 스타일은 `assets/css/main.css`(모든 페이지 공통, 홈 컴포넌트)와 `page.css`(가이드 페이지 추가분)에 둔다. 가이드 페이지는 홈의 헤더·모바일 메뉴·intro·side-box·live-row·footer를 그대로 쓰고, 모바일 메뉴 스크립트는 `assets/js/menu.js`에 있다. 새 페이지도 이 컴포넌트로 만든다. CSS를 고치면 HTML의 `?v=` 숫자를 올려 브라우저가 새로 받게 한다.
- 웹하드 목록과 순위는 `data/webhards.json`에 있다. 배열 순서가 순위이고, `status`가 `ready`인 항목 중 앞에서 `rankLimit`(10)개만 메인에 노출한다. 나머지는 저장만 해 둔다.
  - 순위는 모아온 지수 순서다. `.github/scripts/score.py`가 각 항목의 `metrics`와 `weights`로 `index`·`score`를 계산하고 배열을 다시 정렬한다. 계산 방식은 `criteria.html#index`에 공개하고, 공식을 바꾸면 그 페이지도 함께 고친다.
  - `metrics`는 `.github/workflows/collect.yml`이 매주 월요일 00:00(KST)에 `.github/scripts/collect.py`로 모은다. 구글 플레이 한국 스토어의 추정 다운로드·평점·평가 수, NAVER API HUB 검색어 트렌드(`searchAnchor` 업체를 100으로 둔 상대 검색량과 지난주 변동 폭), 키가 있으면 검색광고 월간 조회수. 결과를 `data/webhards.json`과 `data/metrics-history.json`(최근 26주)에 커밋하고 배포를 시작한다. 수집에 실패한 값은 지난 값을 쓴다.
  - 검색어 트렌드는 NAVER API HUB 주소(`naverapihub.apigw.ntruss.com`)와 `X-NCP-APIGW-API-KEY-ID`·`X-NCP-APIGW-API-KEY` 헤더를 쓴다. 예전 개발자센터 주소(`openapi.naver.com`)는 이 키로 동작하지 않는다.
  - 기본값은 `data/baseline.json`(2026-10-21 수집값)이다. 소유자가 "기본 값으로 돌려줘"라고 하면 `python3 .github/scripts/score.py --restore`로 되돌린다. 기본값을 바꾸라고 할 때만 `--baseline`으로 새로 저장한다.
  - 주간 보정: 배포 때 `render_ranking.py`가 (`.github/scripts/ranking.py`의 `weekly`로) 그 주 월요일(KST)을 시드로 `weeklyAdjust.items`개 항목에 최대 ±`weeklyAdjust.max`점을 더해 순위를 다시 정하고, 지난주 순위와 비교한 ▲▼를 표시한다. 지난주 순위는 월요일 수집 때 `collect.py`가 바꾸기 전 데이터로 계산해 `previousRanks`에 남긴다. 수집이 끝나면 `collect.yml`이 배포를 시작한다. 기본값(`baseline.json`)에는 보정이 들어가지 않는다.
  - `maxRank`({id: 최저 순위})에 적은 항목은 지수·주간 보정과 관계없이 그 순위 아래로 내려가지 않는다. 지금은 온디스크 2위, 케이디스크 8위다. 더 내려가면 그 순위 자리로 올린다.
  - 카드 종합신뢰도(별점)는 모아온 지수를 5점 만점으로 바꾼 값이며 `minScore`(3.5) 아래로 내려가지 않는다.
  - 사이트에는 타사처럼 "순위는 참고용이며 서비스 선택은 이용자 본인의 판단"이라고 안내한다.
  - `pending`은 공식 주소·로고를 확인하지 못한 항목이다. 주소를 추측해서 채우지 않는다. 확인되면 `url`·`logo`를 채우고 `go/<id>/index.html`을 만든 뒤 `ready`로 바꾼다.
  - 업체 로고는 sharp로 다시 저장해 SVG에 넣고, 다른 로고와 같은 229×100 상자에 비슷한 넓이로 맞춘다.
    - 로고에는 업체 이름 글자(워드마크)와 공식 심볼만 넣는다. 받은 이미지에 마스코트·장식(예: 파일몽의 도토리)이 붙어 있으면 잘라 낸다.
    - 흰 글자 로고는 어두운 상자를 깔지 않는다. 글자 색을 어둡게 바꿔 흰 카드 위에 바로 올린다(파일몽: #2f2a26).
    - 넣은 뒤에는 흰 카드 위에서 렌더링해 보고, 상자·여백·잘린 조각이 남지 않았는지 확인한다.
  - 순위·내용을 바꾸면 `updated`(갱신일)도 바꾼다. 페이지 제목·갱신일·sitemap 날짜가 이 값을 따른다.
- 업체별 상세 페이지(`webhard/<id>/`)는 배포 때 `render_ranking.py`가 `.github/templates/webhard.html`로 순위에 오른 모든 업체에 대해 만든다(저장소에는 없다). 모아온 지수 구성, 순위 변동, 구글 플레이 평점·추정 다운로드, 네이버 검색 관심도를 보여주고 sitemap·llms.txt에도 넣는다. 지어낸 후기·평가는 넣지 않는다.
- "사이트 바로가기"는 링크가 아니라 `<button data-go="<id>">`다. `assets/js/go.js`가 새 탭으로 `go/<id>/`를 열고, `data-detail`이 있으면 지금 탭을 그 업체 상세 페이지로 옮긴다. 상세 페이지의 "공식 사이트 이동"은 새 탭만 연다. 카드의 업체 이름은 상세 페이지로 가는 일반 링크라 검색엔진이 따라간다.
- 메인 순위(카드·실시간 순위·차트·요약 문장·구조화 데이터)는 브라우저에서 만들지 않는다. 배포 때 `.github/scripts/render_ranking.py`가 `data/webhards.json`으로 `index.html`·`llms.txt`·`sitemap.xml`의 `{{…}}`와 `<!-- ranking:… -->` 자리를 채운다. 자바스크립트를 실행하지 않는 검색·AI 수집기도 순위를 읽게 하려는 것이다. 저장소의 `index.html`은 빈 자리만 있으므로, 로컬에서 볼 때는 사본에 이 스크립트를 돌려서 본다.
- 배포는 `.github/workflows/deploy.yml`이 맡는다. 개인정보 검사 → 순위 채우기 → 자리표시 치환 → Pages 배포 순서이고, 앞 단계가 실패하면 배포하지 않는다.
- 쓰는 Secret: `PRIVACY_PATTERNS`(금지 문자열), `NAVER_CLIENT_ID`·`NAVER_CLIENT_SECRET`(NAVER API HUB 검색어 트렌드), `NAVER_AD_API_KEY`·`NAVER_AD_SECRET`·`NAVER_AD_CUSTOMER_ID`(검색광고, 선택). 워크플로에서 값을 출력하지 않는다.
- 사이트 결과물에서 `.github`, `.gitattributes`, `.gitignore`, `README.md`, `CLAUDE.md`와 `data/`(순위를 채운 뒤 지운다)는 빠진다. `.gitattributes`는 GitHub 언어 통계에 `.github/scripts`의 파이썬을 넣으려고 둔다. 사이트에 올리지 않을 파일을 루트에 추가하면 `deploy.yml`의 제외 목록에도 넣는다.
