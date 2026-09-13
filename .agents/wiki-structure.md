# Wiki Structure

- Wiki path: ./wiki
- Format: OKF v0.1 style Markdown with YAML frontmatter
- Index policy: Every wiki directory contains index.md
- Change log: ./wiki/logs/

## Directory map

- concepts/: 프로젝트 개념, 도메인과 시스템 설명
- decisions/: 기술·제품 의사결정 기록 (ADR)
- references/: 외부 자료와 도구 참고 문서
- plans/: 진행 중·예정된 작업 항목 (기존 .tasks의 미완료 태스크 이관)
- logs/: 날짜·주제별 위키 변경 이력 및 완료된 작업 기록

## Rules

- 문서 하나에는 하나의 주제를 둔다.
- 새 문서와 새 디렉토리는 해당 디렉토리의 index.md에 등록한다.
- index.md는 하위 구조를 안내하는 지도이며 일반 지식 문서와 구분한다.
- logs/ 문서는 YYYY-MM-DD-kebab-case.md 형식을 사용하고, logs/index.md에 등록한다.
- plans/ 문서는 완료 시 logs/로 결과를 기록하고 plans/에서 제거한다.
- decisions/ 문서는 번호가 있는 ADR로 관리한다.
- 작업 관리는 .tasks(Plank) 대신 본 위키로 수행한다.
