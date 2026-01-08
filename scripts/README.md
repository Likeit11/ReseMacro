# 스크립트 작성 가이드

매크로 스크립트를 작성하는 방법을 안내합니다.

## 기본 구조

모든 스크립트는 `run(macro)` 함수를 포함해야 합니다:

```python
"""
스크립트 설명
"""

def run(macro):
    """
    매크로 실행 함수
    
    Args:
        macro: BaseMacro 인스턴스
    """
    # 여기에 매크로 로직 작성
    macro.macro_sequence("app_icon")
    # ...
```

## 사용 가능한 메서드

### 1. macro_sequence(wait_image, click_image=None, wait_time=5)
이미지를 찾아서 클릭하는 기본 시퀀스

```python
# 같은 이미지를 찾고 클릭
macro.macro_sequence("title_start")

# 다른 이미지를 찾고 클릭
macro.macro_sequence("tuto_dialog_5", "tuto_action_2")

# 클릭 후 대기 시간 지정 (초)
macro.macro_sequence("app_icon", wait_time=10)
```

### 2. macro_touch_sequence(x=300, y=300, wait_image=None, click_image=None, wait_time=5)
좌표를 클릭한 후 이미지를 찾아 클릭

```python
# 좌표 클릭 후 이미지 대기 및 클릭
macro.macro_touch_sequence(x=300, y=450, wait_image="cutscene_skip")

# 좌표만 클릭
macro.macro_touch_sequence(x=100, y=400, wait_time=3)
```

### 3. click_position(x, y, wait_time=1)
특정 좌표를 직접 클릭

```python
macro.click_position(100, 450, wait_time=2)
```

### 4. input_text_via_adb(text)
텍스트 입력

```python
macro.input_text_via_adb("Delete")
macro.input_text_via_adb("MyNickname")
```

### 5. close_current_app()
현재 실행 중인 앱 종료

```python
macro.close_current_app()
```

## 조건문과 반복문

Python 문법을 그대로 사용할 수 있습니다:

```python
def run(macro):
    # 조건문
    if not macro.macro_sequence("title_start"):
        macro.macro_sequence("title_start")  # 재시도
    
    # 반복문
    for i in range(4):
        macro.macro_sequence(f"tuto_dialog_{i+1}")
    
    # while 반복
    retry_count = 0
    while not macro.macro_sequence("level_up") and retry_count < 3:
        time.sleep(2)
        retry_count += 1
```

## 예제 스크립트

### 간단한 예제 (simple_test.py)

```python
"""
간단한 테스트 스크립트
"""

def run(macro):
    """앱을 실행하고 로그인"""
    macro.macro_sequence("app_icon")
    macro.macro_sequence("title_start")
    macro.macro_sequence("guest_login")
```

### 복잡한 예제 (tutorial.py)

```python
"""
게임 튜토리얼 자동 진행
"""

import time

def run(macro):
    """튜토리얼 전체 진행"""
    # 게임 시작
    macro.macro_sequence("app_icon")
    
    if not macro.macro_sequence("title_start"):
        macro.macro_sequence("title_start")
    
    macro.macro_sequence("guest_login")
    
    # 컷신 스킵
    if not macro.macro_touch_sequence(wait_image="first_cutscene", click_image="cutscene_skip"):
        macro.macro_touch_sequence(wait_image="cutscene_skip")
    
    # 튜토리얼 대사 반복
    for i in range(1, 5):
        macro.macro_sequence(f"tuto_dialog_{i}")
    
    # 튜토리얼 액션
    macro.macro_sequence("tuto_action_1")
    macro.macro_sequence("tuto_dialog_5", "tuto_action_2")
    
    # 나머지 로직...
```

## 주의사항

1. **이미지 파일**: 모든 이미지는 `Ref_Img/` 폴더에 PNG 형식으로 저장되어야 합니다
2. **확장자 제외**: 이미지 이름에 `.png` 확장자를 포함하지 마세요
3. **대기 시간**: 너무 짧으면 실패할 수 있으니 적절한 대기 시간을 설정하세요
4. **에러 처리**: 중요한 부분은 조건문으로 재시도 로직을 추가하세요

## 스크립트 실행

```bash
# 스크립트 실행
python Source/main.py --script scripts/my_script.py
```
