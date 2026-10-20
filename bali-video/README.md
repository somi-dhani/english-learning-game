# 부산갈 줄 알았던 우리, 발리 갑니다. (59팀 골든키)

15초 세로형(1080×1920, 30fps) 숏폼 영상. 결과물: `bali_59team.mp4`

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
