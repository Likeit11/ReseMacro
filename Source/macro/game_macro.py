"""
게임 특화 매크로 모듈

게임의 run_macro 및 reset_account 로직을 포함
참고: run_macro는 매우 길기 때문에 scripts/ 디렉토리의 Python 스크립트로 분리 권장
"""

import time
from macro.base_macro import BaseMacro
from utils.logger import get_logger

logger = get_logger()


class GameMacro(BaseMacro):
    """게임 특화 매크로 클래스"""
    
    def reset_account(self):
        """
        계정 리셋을 위한 함수
        """
        if not self.macro_sequence("lobby_button"):
            logger.info("lobby_button 클릭 실패, 재시도")
            time.sleep(2)
            self.macro_sequence("lobby_button_other")
        
        self.macro_sequence("guest_login_action_1", wait_time=5)
        self.macro_sequence("guest_login_action_2", wait_time=5)
        self.macro_sequence("guest_login_action_3", wait_time=5)
        self.macro_sequence("guest_login_action_4", wait_time=5)
        self.macro_sequence("guest_login_action_5", wait_time=5)
        self.macro_sequence("guest_login_action_6", wait_time=5)
        
        self.input_text_via_adb("Delete")
        
        self.macro_sequence("guest_login_action_7", wait_time=5)
        self.close_current_app()
    
    def run_macro(self):
        """
        게임 매크로 실행 (튜토리얼부터 가챠까지)
        
        참고: 이 메서드는 매우 길기 때문에 (500줄+) 
        scripts/tutorial.py와 같은 별도 스크립트 파일로 분리하는 것을 권장합니다.
        
        예: python main.py --script scripts/full_macro.py
        """
        # 기존 ReseMara.py의 run_macro() 내용을 여기에 이식할 수 있지만,
        # 더 나은 방법은 scripts/ 디렉토리에 Python 스크립트로 작성하는 것입니다.
        
        # 간단한 예시 구현:
        try:
            self.macro_sequence("app_icon")
            if not self.macro_sequence("title_start"):
                self.macro_sequence("title_start")
            
            self.macro_sequence("guest_login")
            
            # ... 나머지 로직은 scripts/full_macro.py에 작성 권장
            
            logger.info("매크로가 완료되었습니다 (또는 scripts/ 사용 권장)")
            
        except Exception as e:
            logger.error(f"매크로 실행 중 오류 발생: {str(e)}")
            raise
