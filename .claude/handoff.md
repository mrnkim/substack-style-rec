# Handoff Notes

## Session — 2026-03-26: Strand Design System 폰트 적용

### 배경
- James 피드백: Strand design system (TwelveLabs brand guidelines) 적용 여부 확인
- 확인 결과: 색상 토큰/spacing은 이미 적용되어 있었으나, 폰트가 Strand가 아닌 Geist/Instrument Serif 사용 중이었음

### 작업 내용
- [x] Strand 폰트 `@font-face` 선언 추가 (`globals.css`)
  - Milling (brand, CDN: `d2n8i6crd2t3p1.cloudfront.net`), weight 400/700
  - Noto Sans (system, `next/font/google`)
  - IBM Plex Mono (mono, `next/font/google`)
- [x] `layout.tsx`에서 Geist/Instrument Serif → Noto Sans + IBM Plex Mono 교체
- [x] CSS 토큰 추가: `--font-brand`, `--font-sans`, `--font-mono`
- [x] 5개 파일에서 `--font-display` italic → `--font-brand` (Milling) 교체
  - `hero-feature.tsx`, `watch/[id]/page.tsx`, `search/page.tsx`, `creator/[id]/page.tsx`, `explore/page.tsx`
- [x] `.vercelignore` 추가 (`scripts/` 5.2GB 제외 — Vercel 100MB 제한 대응)
- [x] Vercel 프로덕션 배포 완료

### Strand 토큰 적용 현황
| 카테고리 | 적용 상태 |
|---|---|
| 색상 (bg, text, border) | ✅ Strand 기반 warm charcoal 변형 |
| Semantic (info, warning, success, error) | ✅ |
| 폰트 (Milling, Noto Sans, IBM Plex Mono) | ✅ 이번 세션에서 적용 |
| Radius, Spacing | ✅ |
| Signature gradient | ❌ 미적용 |
| 카테고리 pill 색상 (보라, 파랑 등) | 앱 자체 추가 (Strand에 없음) |

### 참고
- Milling 폰트는 Google Fonts에 없는 커스텀 폰트 → CloudFront CDN에서 woff2 로드
- `scripts/` 폴더 (5.2GB, 비디오 다운로드 등)가 Vercel 배포 제한 초과 → `.vercelignore`로 제외
