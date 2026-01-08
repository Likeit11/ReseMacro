"""
화면 캡처 및 관리 모듈

ADB를 통한 화면 캡처 및 스크린샷 파일 관리 기능 제공
"""

import time
import numpy as np
from PIL import Image
import io
from typing import Optional

from config.settings import Settings
from utils.file_manager import FileManager


class ScreenCapture:
    """화면 캡처 및 관리 클래스"""
    
    def __init__(self, adb_manager):
        """
        Args:
            adb_manager: ADBManager 인스턴스
        """
        self.adb = adb_manager
        self.file_manager = FileManager()
    
    def capture(self, save_to_disk: bool = True) -> Optional[np.ndarray]:
        """
        화면 캡처
        
        Args:
            save_to_disk (bool): 파일로 저장 여부 (기본값: True)
            
        Returns:
            Optional[np.ndarray]: 캡처된 이미지 (numpy 배열)
        """
        try:
            result = self.adb.capture_screen_raw()
            image = Image.open(io.BytesIO(result))
            
            if save_to_disk:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"{Settings.ROW_SCREEN_DIR}/screen_{timestamp}.png"
                image.save(filename)
                
                # 스크린샷 파일 개수 관리
                self.file_manager.manage_old_files(
                    Settings.ROW_SCREEN_DIR,
                    Settings.MAX_SCREENSHOTS,
                    '.png'
                )
            
            return np.array(image)
        except Exception as e:
            print(f"화면 캡처 실패: {str(e)}")
            raise
    
    def save_account_screenshot(self, screen_array: np.ndarray, prefix: str = "account"):
        """
        계정 정보 스크린샷 저장
        
        Args:
            screen_array: 스크린샷 이미지 배열
            prefix: 파일명 접두사
        """
        import cv2
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{Settings.ACCOUNTS_DIR}/{prefix}_{timestamp}.png"
        
        screen_bgr = cv2.cvtColor(screen_array, cv2.COLOR_RGB2BGR)
        cv2.imwrite(filename, screen_bgr)
