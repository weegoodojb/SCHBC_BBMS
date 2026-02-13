---
description: 작업 시작 전 ACT_NOW.txt 읽기 및 작업 완료 후 LOG.md 업데이트. 사용자가 '굿' 또는 '완료'라고 말하면 LOG.md 작성 후 ACT_NOW.txt를 비운다.
---

# 작업 전/후 필수 절차

## 작업 시작 전 (Pre-Task)

// turbo
1. `c:\code\antigravity\PBM\ACT_NOW.txt` 파일을 읽어 현재 지시사항을 확인한다.
2. 파일 내용을 기반으로 현재 작업 방향을 결정한다.

## 작업 완료 후 (Post-Task)

3. `c:\code\antigravity\PBM\LOG.md` 파일에 작업 내용을 추가한다.
   - 파일이 없으면 새로 생성한다.
   - 기존 내용이 있으면 최상단에 새 항목을 추가한다 (최신순 정렬).
   - 형식:
     ```markdown
     ## [YYYY-MM-DD HH:MM] 작업 제목
     - **작업 내용**: 수행한 작업 요약
     - **변경 파일**: 변경된 주요 파일 목록
     - **결과**: 성공/실패 및 참고사항
     ```

## 트리거 키워드: '완료'

사용자가 **'완료'**라고 말하면 다음을 자동으로 수행한다:

// turbo-all
1. `c:\code\antigravity\PBM\LOG.md`에 현재까지 수행한 작업 내용을 위 형식에 맞춰 기록한다.
2. `c:\code\antigravity\PBM\ACT_NOW.txt` 파일 내용을 완전히 비운다 (빈 파일로 덮어쓰기).
3. 사용자에게 LOG.md 업데이트 및 ACT_NOW.txt 초기화가 완료되었음을 알린다.
