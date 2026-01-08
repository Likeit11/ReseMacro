# ReseMacro

ADB를 사용한 안드로이드 게임 매크로 자동화 도구

## 개요

ReseMacro는 MuMu Player 에뮬레이터에서 게임을 자동으로 플레이하는 매크로 도구입니다. OpenCV를 사용한 이미지 인식으로 게임 화면을 분석하고 자동으로 클릭합니다.

## 주요 기능

- 🎮 **자동 게임 플레이**: 이미지 인식 기반 자동 클릭
- 📜 **Python 스크립팅**: 커스텀 매크로를 Python 스크립트로 작성
- 🔄 **계정 리셋**: 자동 계정 리셋 및 재시작
- 📸 **화면 캡처**: 자동 스크린샷 저장 및 관리
- 🔌 **다중 포트 지원**: 여러 에뮬레이터 동시 지원

## 프로젝트 구조

```
ReseMacro/
├── Source/
│   ├── main.py              # 메인 진입점
│   ├── config/              # 설정 모듈
│   ├── core/                # ADB 및 이미지 처리
│   ├── macro/               # 매크로 실행 로직
│   └── utils/               # 유틸리티
├── Ref_Img/                 # 참조 이미지 (템플릿)
├── scripts/                 # 매크로 스크립트
│   └── README.md            # 스크립트 작성 가이드
└── README.md                # 이 파일
```

## 설치 방법

### 필수 요구사항

- Python 3.7+
- MuMu Player (또는 다른 안드로이드 에뮬레이터)
- ADB 활성화

### 패키지 설치

```bash
cd Source
pip install -r requirements.txt
```

필요한 패키지:
- `adb-shell`: ADB 연결
- `pillow`: 이미지 처리
- `opencv-python`: 이미지 매칭
- `numpy`: 배열 처리

## 사용 방법

### 기본 실행

```bash
cd Source
python main.py
```

ADB 포트는 자동으로 검색됩니다 (MuMu Player 기본 포트: 16384, 16416, ...).

### 포트 지정

```bash
python main.py --port 16384
```

### 스크립트 실행

```bash
python main.py --script ../scripts/my_macro.py
```

## 스크립트 작성

`scripts/` 디렉토리에 Python 스크립트를 작성하여 커스텀 매크로를 만들 수 있습니다.

### 기본 구조

```python
def run(macro):
    """매크로 실행 함수"""
    # 앱 실행
    macro.macro_sequence("app_icon")
    macro.macro_sequence("title_start")
    
    # 로그인
    macro.macro_sequence("guest_login")
    
    # ... 나머지 로직
```

자세한 내용은 [scripts/README.md](scripts/README.md)를 참고하세요.

## 빌드

실행 파일(.exe)로 빌드하기:

```bash
cd Source
python build.py
```

빌드된 파일: `Source/dist/ReseMara.exe`

## 이미지 추가

`Ref_Img/` 폴더에 PNG 형식의 참조 이미지를 추가하세요:

1. 게임 화면에서 클릭할 버튼 스크린샷
2. PNG 형식으로 저장
3. 의미있는 이름 지정 (예: `login_button.png`)
4. 스크립트에서 확장자 없이 사용 (예: `macro.macro_sequence("login_button")`)

## 로그

- **ReseMara.log**: 전체 실행 로그
- **Row_Screen/**: 캡처된 화면 (최대 30개 자동 관리)
- **Accounts/**: 계정 스크린샷 저장

## 문제 해결

### ADB 연결 실패

```
사용 가능한 ADB 포트를 찾지 못했습니다.
```

**해결 방법:**
1. MuMu Player가 실행 중인지 확인
2. ADB가 활성화되어 있는지 확인
3. 포트 번호를 직접 지정: `python main.py --port 16384`

### 이미지를 찾지 못함

```
30초 동안 이미지를 찾지 못했습니다: button_name
```

**해결 방법:**
1. `Ref_Img/button_name.png` 파일이 존재하는지 확인
2. 이미지가 실제 게임 화면과 일치하는지 확인
3. 화면 해상도가 동일한지 확인

## 라이선스

이 프로젝트는 개인 사용 목적으로 제작되었습니다.

## 기여

문제가 발생하거나 개선 사항이 있으면 Issue를 생성해주세요.
