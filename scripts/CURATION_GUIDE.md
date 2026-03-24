# Video Curation Guide

## Target Mix (25-30 videos, 8-10 creators)

| Category | % | Count | Per Creator |
|---|---|---|---|
| Interview/Conversation | 40% | 10-12 | 2-4 videos |
| Commentary/Analysis | 30% | 7-9 | 2-3 videos |
| Creative/Performance | 20% | 5-6 | 2-3 videos |
| Educational/How-To | 10% | 2-3 | 1-2 videos |

## Selection Criteria

- English content
- 10min+ longform (ideal: 15-45min)
- Good audio/video quality
- Diverse topics across creators (크로스 크리에이터 추천 시연용)
- Creator당 2-4 videos (같은 크리에이터 내 딥 카탈로그 시연)

## Candidate Channels by Category

### Interview/Conversation (40%) — 3-4 creators, 10-12 videos

| Channel | Why | Content Style |
|---|---|---|
| **Lex Fridman Podcast** | Long-form tech/science/philosophy interviews, huge catalog | Deep 1-on-1, serious tone, 1-3hr (clip segments available) |
| **The Diary of a CEO (Steven Bartlett)** | Entrepreneurship/psychology interviews | Casual but deep, 1-2hr |
| **Colin and Samir** | Creator economy interviews + analysis | Energetic, 20-40min |
| **Rich Roll Podcast** | Health/wellness/endurance interviews | Reflective, long-form |
| **Theo Von** | Comedy/conversation interviews | Lighthearted, casual |

**Pick 3 creators, 3-4 videos each.** Topical overlap 있으면 좋음 (e.g., Lex와 Diary of CEO 둘 다 AI 인터뷰 → 크로스 추천 가능).

### Commentary/Analysis (30%) — 2-3 creators, 7-9 videos

| Channel | Why | Content Style |
|---|---|---|
| **Vox** | Explainer journalism, wide topic range | Polished, visual essays, 10-20min |
| **Johnny Harris** | Geopolitics/culture deep dives | Story-driven, 15-30min |
| **Wendover Productions** | Logistics/economics/infrastructure analysis | Analytical, 15-25min |
| **ColdFusion** | Tech industry analysis/history | Documentary style, 15-30min |
| **MKBHD** | Tech reviews + industry commentary | Clean, authoritative, 10-20min |

**Pick 2-3 creators, 3 videos each.** 토픽이 다른 카테고리와 겹치면 ideal (e.g., tech commentary ↔ tech interview → 크로스 추천).

### Creative/Performance (20%) — 1-2 creators, 5-6 videos

| Channel | Why | Content Style |
|---|---|---|
| **Vox (Earworm / Borders series)** | Music/culture mini-docs | Cinematic, 10-20min |
| **Every Frame a Painting** | Film analysis (CC licensed!) | Essay film, 5-15min |
| **KEXP** | Live music performances + interviews | Performance + conversation |
| **Kirsten Dirksen** | Alternative living documentaries (CC!) | Observational documentary, 10-30min |
| **The New Yorker Documentary** | Short documentaries | Polished, narrative |

**Pick 2 creators, 2-3 videos each.**

### Educational/How-To (10%) — 1 creator, 2-3 videos

| Channel | Why | Content Style |
|---|---|---|
| **3Blue1Brown** | Math visualization (CC licensed) | Educational, visual, 15-30min |
| **Kurzgesagt** | Science explainers (CC licensed) | Animated, 10-15min |
| **TED** | Talks on everything (CC licensed) | Lecture, 10-20min |
| **Veritasium** | Science deep dives | Investigative, 15-25min |
| **Ali Abdaal** | Productivity/learning | Casual educational, 15-25min |

**Pick 1 creator, 2-3 videos.**

## Recommended Starter Combination (Example)

이건 하나의 예시 조합. 크로스 크리에이터 추천이 잘 작동하도록 토픽 겹침을 고려한 배합:

| # | Creator | Category | Videos | Topic Focus |
|---|---|---|---|---|
| 1 | Lex Fridman | Interview | 4 | AI, science, philosophy |
| 2 | Colin and Samir | Interview | 3 | Creator economy, tech, media |
| 3 | The Diary of a CEO | Interview | 3 | Entrepreneurship, psychology, AI |
| 4 | Johnny Harris | Commentary | 3 | Geopolitics, culture, economics |
| 5 | ColdFusion | Commentary | 3 | Tech history, AI, industry |
| 6 | Vox (Earworm) | Creative | 3 | Music, culture, storytelling |
| 7 | Kirsten Dirksen | Creative | 2 | Alternative living, design (CC) |
| 8 | 3Blue1Brown | Educational | 3 | Math, visualization (CC) |
| **Total** | **8 creators** | | **24 videos** | |

**Cross-recommendation opportunities:**
- AI topic: Lex ↔ ColdFusion ↔ Diary of CEO
- Creator/media economy: Colin & Samir ↔ Diary of CEO
- Culture: Johnny Harris ↔ Vox Earworm
- Science/education: Lex ↔ 3Blue1Brown

## How to Fill the CSV

1. YouTube에서 각 크리에이터 채널 방문
2. 10min+ 영상 중 위 토픽에 맞는 것 선택
3. URL에서 video_id 추출 (e.g., `youtube.com/watch?v=ABC123` → `ABC123`)
4. `curate_videos.csv`에 기입
5. `download_script.py` 실행 → `upload_to_twelvelabs.py` 실행
