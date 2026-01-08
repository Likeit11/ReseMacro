"""
기본 매크로 실행 모듈

매크로 시퀀스 실행을 위한 베이스 클래스 제공
"""

import time
from typing import Optional

from core.adb_manager import ADBManager
from core.screen_capture import ScreenCapture
from core.image_matcher import ImageMatcher
from utils.logger import get_logger
from config.settings import Settings

logger = get_logger()


class BaseMacro:
    """기본 매크로 기능을 제공하는 베이스 클래스"""
    
    def __init__(self, adb_manager: ADBManager):
        """
        Args:
            adb_manager: ADBManager 인스턴스
        """
        self.adb = adb_manager
        self.screen_capture = ScreenCapture(adb_manager)
        self.image_matcher = ImageMatcher(self.screen_capture)
    
    def macro_sequence(self, wait_image: str, click_image: Optional[str] = None, wait_time: float = 5) -> bool:
        """
        이미지 찾아서 클릭하는 시퀀스
        
        Args:
            wait_image: 대기할 이미지 이름
            click_image: 클릭할 이미지 이름 (None이면 wait_image와 동일)
            wait_time: 대기 시간 (기본값: 5초)
            
        Returns:
            bool: 시퀀스 성공 여부
        """
        if click_image is None:
            click_image = wait_image
        
        # 이미지를 찾았을 때만 클릭 실행
        if self.image_matcher.wait_for_image(wait_image):
            result = self.image_matcher.find_image(click_image)
            if result:
                center_x, center_y, score = result
                logger.info(f"{click_image} 버튼을 찾아 클릭했습니다 (매칭 점수: {score:.4f})")
                self.adb.tap(center_x, center_y)
                time.sleep(wait_time)
                return True
            else:
                logger.info(f"{click_image} 버튼 클릭에 실패했습니다")
                return False
        else:
            logger.info(f"{wait_image} 이미지를 찾지 못해 다음 동작으로 넘어갑니다")
            return False
    
    def macro_touch_sequence(self, x: int = 300, y: int = 300, 
                            wait_image: Optional[str] = None, 
                            click_image: Optional[str] = None, 
                            wait_time: float = 5) -> bool:
        """
        특정 좌표를 클릭한 후 이미지를 찾아 클릭하는 시퀀스
        
        Args:
            x: 클릭할 x 좌표 (기본값: 300)
            y: 클릭할 y 좌표 (기본값: 300)
            wait_image: 대기할 이미지 이름
            click_image: 클릭할 이미지 이름 (None이면 wait_image와 동일)
            wait_time: 대기 시간 (기본값: 5초)
        
        Returns:
            bool: 시퀀스 성공 여부
        """
        if click_image is None and wait_image is not None:
            click_image = wait_image
        
        time.sleep(2)
        self.click_position(x, y)
        
        if wait_image:
            # 이미지를 찾았을 때만 클릭 실행
            if self.image_matcher.wait_for_image(wait_image):
                self.click_position(x, y)
                result = self.image_matcher.find_image(click_image)
                if result:
                    center_x, center_y, score = result
                    logger.info(f"{click_image} 버튼을 찾아 클릭했습니다")
                    self.adb.tap(center_x, center_y)
                    time.sleep(wait_time)
                    return True
                else:
                    logger.info(f"{click_image} 버튼 클릭에 실패했습니다")
                    return False
            else:
                logger.info(f"{wait_image} 이미지를 찾지 못해 다음 동작으로 넘어갑니다")
                return False
        else:
            time.sleep(wait_time)
            return True  # 이미지 검사가 없는 경우는 성공으로 간주
    
    def click_position(self, x: int, y: int, wait_time: float = 1) -> bool:
        """
        지정된 좌표를 클릭하고 지정된 시간만큼 대기
        
        Args:
            x: 클릭할 x 좌표
            y: 클릭할 y 좌표
            wait_time: 클릭 후 대기할 시간(초) (기본값: 1초)
            
        Returns:
            bool: 클릭 성공 여부
        """
        time.sleep(wait_time)
        
        logger.debug(f"좌표 클릭 시도: ({x}, {y})")
        result = self.adb.tap(x, y)
        time.sleep(wait_time)
        return result
    
    def input_text_via_adb(self, text: str) -> bool:
        """
        ADB를 통해 문자를 입력
        
        Args:
            text: 입력할 텍스트
            
        Returns:
            bool: 성공 여부
        """
        logger.debug(f"텍스트 입력: {text}")
        return self.adb.input_text(text)
    
    def close_current_app(self) -> bool:
        """
        현재 실행 중인 앱을 종료
        
        Returns:
            bool: 종료 성공 여부
        """
        package_name = self.adb.get_current_package()
        
        if package_name:
            logger.debug(f"앱 종료 시도: {package_name}")
            result = self.adb.force_stop_app(package_name)
            if result:
                logger.info(f"앱이 종료되었습니다: {package_name}")
            return result
        else:
            logger.error("종료할 앱을 찾을 수 없습니다")
            return False
