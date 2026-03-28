# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

Svg2Vector는 Android Studio의 Svg2Vector 기능을 Python으로 포팅한 프로젝트입니다. SVG 파일을 Android의 VectorDrawable XML 형식으로 변환합니다.

- **원본 소스**: https://android.googlesource.com/platform/tools/base/+/refs/heads/mirror-goog-studio-main/sdk-common/src/main/java/com/android/ide/common/vectordrawable
- **라이선스**: Apache License 2.0

## 개발 환경 설정

### 필수 사항
- Python 3.7+ (f-string, type hints 사용)
- 표준 라이브러리만 사용 (외부 의존성 없음)

### 테스트 실행

```bash
# 모든 테스트 실행
cd test
python test.py

# 특정 테스트만 실행
python -m unittest test.Svg2VectorTest.testCircle
```

테스트는 각 SVG 파일과 예상 XML 출력을 비교합니다.

### 로깅

프로젝트는 Python `logging` 모듈을 사용합니다. 로거는 `logging.getLogger('Svg2Vector')`로 생성됩니다.

```bash
# 로그를 파일로 저장
python -c "import logging; logging.basicConfig(filename='svg2vector.log', level=logging.DEBUG)"
```

## 아키텍처

### 핵심 변환 파이프라인

```
SVG 파일 (XML)
    ↓
Svg2Vector.parseSvgToXml()  [Svg2Vector.py]
    ↓
SvgTree 구성  [SvgTree.py]
    ↓
VectorDrawable XML 생성  [VdNodeRender.py]
    ↓
OutputStreamWriter → 최종 XML
```

### 주요 클래스

**Svg2Vector.py** (진입점)
- `parseSvgToXml()`: SVG를 VectorDrawable XML로 변환하는 정적 메서드
- SVG 요소들을 파싱하고 적절한 SvgNode 인스턴스로 변환

**SvgTree.py** (SVG 데이터 구조)
- SVG 파일의 내부 표현을 트리 형태로 구성
- ViewBox, 크기, 루트 변환 등 SVG 메타데이터 관리
- ID 맵을 통한 요소 참조 해석 (use, href)

**노드 계층** (상속 구조)
```
SvgNode (추상 기본 클래스)
├── SvgGroupNode (g 요소)
├── SvgLeafNode (모양 요소)
│   └── Path, Circle, Rect, Ellipse, Line, Polygon, Polyline
├── SvgGradientNode (linearGradient, radialGradient)
└── SvgClipPathNode (clipPath)
```

**VectorDrawable 생성**
- `VdNodeRender.py`: SvgNode를 VectorDrawable 속성으로 변환
- `VdPath.py`: 경로 명령 저장 및 처리
- `VdElement.py`: 개별 VectorDrawable 요소
- `OutputStreamWriter.py`: 최종 XML 문자열 생성

**기하학 및 변환 유틸리티**
- `Path2D.py`: SVG 경로 처리
- `AffineTransform.py`: 행렬 변환 (크기가 매우 큼 - 55KB)
- `PathBuilder.py`: 경로 구성
- `Rectangle2D.py`, `Point2D.py`: 기하학 자료구조
- `EllipseSolver.py`: 타원 호 변환

**유틸리티**
- `PathParser.py`: SVG d 속성 파싱
- `SvgColor.py`: SVG 색상 파싱
- `XmlUtils.py`: XML 처리
- `PositionXmlParser.py`: 위치 기반 XML 파싱
- `VdUtil.py`: 유틸리티 함수

## 코딩 규칙

### 스타일
- **들여쓰기**: 2칸 (프로젝트 표준)
- **임포트**: sys.path 조작으로 모듈 로드 (test/test.py 참고)
- **로깅**: `logger = logging.getLogger('Svg2Vector')`로 로거 생성

### Python 버전
- f-string 사용
- Type hints 사용 (예: `list[VdPath.Node]`, `Self`)
- 표준 라이브러리만 사용

### 주의사항

1. **경로 임포트**: test 디렉토리에서 실행하는 테스트는 `sys.path.append('../src')`로 src 모듈을 로드합니다. 상대 경로 조정 필요.

2. **테스트 케이스 문제**: test.py에 동일한 메서드명 `testCircle`이 두 번 정의되어 있습니다 (circle과 clipPath). 향후 수정 필요.

3. **SVG 요소 지원**: 모든 SVG 요소가 지원되지는 않습니다. 지원되는 요소는:
   - 기본 도형: circle, ellipse, rect, line, polygon, polyline
   - 경로: path
   - 그룹: g, defs, clipPath
   - 그래디언트: linearGradient, radialGradient
   - 기타: use, style, transform

4. **로깅 메시지**: SvgTree는 파싱 중 발견된 경고/오류를 `mLogMessages` 리스트에 저장합니다.

## 일반적인 작업

### 새로운 SVG 요소 지원 추가
1. `Svg2Vector.py`에서 요소 처리 로직 추가
2. 적절한 SvgNode 서브클래스 생성 또는 기존 클래스 확장
3. `VdNodeRender.py`에서 VectorDrawable 속성으로의 변환 로직 추가
4. test/ 디렉토리에 SVG 샘플과 예상 XML 파일 추가 및 테스트 작성

### 버그 수정 시
- git log에서 이슈 번호(#N) 참고
- 관련 테스트 케이스 확인 또는 생성
- 변환 결과 검증
