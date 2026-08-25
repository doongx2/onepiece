# P-Bandai 재고/신상품 알리미

프리미엄 반다이(台灣) 특정 상품의 재입고와, 시리즈 목록 페이지의 신상품 등록을 감지해서
디스코드로 알림을 보내주는 GitHub Actions 봇입니다.

## 1. Discord 웹훅 URL 만들기

1. 알림 받을 디스코드 채널 설정(톱니바퀴) → **연동(Integrations)** → **웹후크(Webhooks)** → **새 웹후크**
2. 이름 설정 후 **웹후크 URL 복사**

## 2. GitHub 저장소 만들기

1. GitHub에서 새 저장소(Private 추천)를 만듭니다.
2. 이 폴더(`pbandai-monitor`)의 파일들을 그대로 업로드/푸시합니다.
   ```bash
   cd pbandai-monitor
   git init
   git add .
   git commit -m "init"
   git branch -M main
   git remote add origin https://github.com/<내계정>/<저장소이름>.git
   git push -u origin main
   ```

## 3. 웹훅 URL을 GitHub Secret으로 등록

1. 저장소 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
2. Name: `DISCORD_WEBHOOK_URL`
3. Value: 1번에서 복사한 웹훅 URL 붙여넣기

## 4. 확인할 상품/시리즈 URL 수정

`monitor.py` 상단의 설정 부분을 원하는 상품/목록 URL로 수정하세요.

```python
ITEM_URLS = [
    "https://p-bandai.com/tw/item/A2866729001",
]

SERIES_URLS = [
    "https://p-bandai.com/tw/series/onepiece-series?_f_series=03-002&offset=0&limit=20&sortType=NewArrival&_f_productStatuses=Waiting,On",
]
```

여러 개 등록하려면 리스트에 URL을 콤마로 구분해 추가하면 됩니다.

## 5. 실행 확인

- 저장소 → **Actions** 탭 → `P-Bandai Monitor` 워크플로우 → **Run workflow** 버튼으로 수동 실행해서 테스트
- 정상 동작 시 20분마다 자동으로 실행됩니다 (`.github/workflows/monitor.yml`의 cron 값으로 주기 조절 가능)
- 첫 실행은 "최초 확인"이라 알림이 오지 않는 게 정상입니다 (비교 기준을 저장하는 단계). 그 다음 실행부터 변화가 있으면 알림이 옵니다.

## 6. 주의사항

- 이 사이트는 robots.txt로 자동 접속을 제한하고 있습니다. 개인 용도로 저빈도(20분 이상 간격)로 사용하는 걸 권장하며,
  간격을 너무 짧게 줄이지 마세요. 사이트 정책 변경이나 구조 변경(HTML/키워드)이 있으면 스크립트가 오작동할 수 있습니다.
- `OUT_OF_STOCK_KEYWORDS`는 실제 페이지 표기와 다를 수 있습니다. 알림이 잘 안 온다면
  상품 페이지의 "품절/재고없음" 표시 문구를 확인해서 리스트에 추가해주세요.
