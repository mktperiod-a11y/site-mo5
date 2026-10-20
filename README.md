# 웹하드 비교 정적 사이트

- 메인 순위 변경: `index.html` 하단의 `services` 배열 순서를 수정합니다.
- 사이트 주소는 코드에 적지 않습니다. 절대 주소가 필요하면 `https://site-url.invalid` 자리표시를 쓰고, 배포 때 실제 주소로 바뀝니다.
- 배포: `main`에 push하면 GitHub Actions(`.github/workflows/deploy.yml`)가 GitHub Pages로 배포합니다. 도메인은 저장소 Settings → Pages에서만 관리합니다.
