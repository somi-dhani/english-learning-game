# 부산갈 줄 알았던 우리, 발리 갑니다. (59팀 골든키)

15초 세로형(1080×1920, 30fps) 숏폼 영상. 결과물: `bali_59team.mp4`

음악: `audio.py`로 직접 합성한 130BPM 트로트-EDM 오리지널 비트. 11.2초 발리 당첨 알림 → 빌드업 → 12초 "아모르 파티!" 드롭.
원곡 「아모르 파티」 음원은 저작권 때문에 들어있지 않음. 쓰려면 릴스·틱톡·캡컷의 음원 라이브러리에서 12초 지점에 맞춰 얹으면 됨.

| 파일 | 역할 |
| --- | --- |
| `scene.html` | 모든 장면을 시간 `t`의 함수로 그리는 SVG 애니메이션 (`render(t)`) |
| `render.mjs` | Playwright로 프레임을 캡처해 ffmpeg로 인코딩 (`out/silent.mp4`) |
| `audio.py` | 120BPM 비트 + 장면별 효과음 합성 (`out/audio.wav`) |
| `fetch_fonts.py` | Black Han Sans / Jua 웹폰트를 로컬로 내려받음 |

다시 만들기:

```sh
python3 fetch_fonts.py
node render.mjs                 # 미리보기만: node render.mjs --stills 1,7,13
python3 audio.py
ffmpeg -y -i out/silent.mp4 -i out/audio.wav -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart bali_59team.mp4
```
