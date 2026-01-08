"""
이미지 매칭 모듈

OpenCV를 사용한 템플릿 매칭 및 이미지 비교 기능 제공
"""

import time
import cv2
import numpy as np
from typing import Tuple, Optional

from config.settings import Settings


class ImageMatcher:
    """이미지 매칭 및 비교 클래스"""
    
    def __init__(self, screen_capture):
        """
        Args:
            screen_capture: ScreenCapture 인스턴스
        """
        self.screen_capture = screen_capture
    
    def find_image(self, image_name: str, threshold: float = None, timeout: int = None) -> Optional[Tuple[int, int, float]]:
        """
        이미지를 찾아서 중심 좌표 반환
        
        Args:
            image_name: 찾을 이미지 이름 (확장자 제외)
            threshold: 매칭 임계값 (기본값: Settings.DEFAULT_THRESHOLD)
            timeout: 타임아웃 (초) (기본값: Settings.IMAGE_FIND_TIMEOUT)
            
        Returns:
            Optional[Tuple[int, int, float]]: (center_x, center_y, match_score) 또는 None
        """
        if threshold is None:
            threshold = Settings.DEFAULT_THRESHOLD
        if timeout is None:
            timeout = Settings.IMAGE_FIND_TIMEOUT
        
        template_path = f'{Settings.REF_IMG_DIR}/{image_name}.png'
        template = cv2.imread(template_path)
        
        if template is None:
            print(f"참조 이미지를 찾을 수 없음: {template_path}")
            return None
        
        start_time = time.time()
        
        while True:
            if time.time() - start_time > timeout:
                print(f"{timeout}초 동안 이미지를 찾지 못했습니다: {image_name}")
                return None
            
            try:
                screen = self.screen_capture.capture(save_to_disk=True)
                screen_bgr = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
                
                result = cv2.matchTemplate(screen_bgr, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= threshold:
                    h, w = template.shape[:2]
                    center_x = max_loc[0] + w // 2
                    center_y = max_loc[1] + h // 2
                    return (center_x, center_y, max_val)
                else:
                    time.sleep(1)
            except Exception as e:
                print(f"이미지 매칭 중 오류: {str(e)}")
                time.sleep(1)
    
    def wait_for_image(self, image_name: str, threshold: float = None, timeout: int = None) -> bool:
        """
        이미지가 나타날 때까지 대기
        
        Args:
            image_name: 대기할 이미지 이름
            threshold: 매칭 임계값
            timeout: 타임아웃 (초) (기본값: Settings.IMAGE_WAIT_TIMEOUT)
            
        Returns:
            bool: 이미지를 찾았는지 여부
        """
        if timeout is None:
            timeout = Settings.IMAGE_WAIT_TIMEOUT
        
        result = self.find_image(image_name, threshold, timeout)
        return result is not None
    
    def compare_images(self, image1_name: str, image2_name: str, threshold: float = None) -> Tuple[bool, bool]:
        """
        두 이미지 중 하나라도 화면에 있는지 비교
        
        Args:
            image1_name: 첫 번째 이미지 이름
            image2_name: 두 번째 이미지 이름
            threshold: 매칭 임계값 (기본값: Settings.COMPARE_THRESHOLD)
            
        Returns:
            Tuple[bool, bool]: (image1_found, image2_found)
        """
        if threshold is None:
            threshold = Settings.COMPARE_THRESHOLD
        
        try:
            screen = self.screen_capture.capture(save_to_disk=False)
            screen_bgr = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
            
            # 첫 번째 이미지 확인
            template1 = cv2.imread(f'{Settings.REF_IMG_DIR}/{image1_name}.png')
            result1 = False
            if template1 is not None:
                match_result = cv2.matchTemplate(screen_bgr, template1, cv2.TM_CCOEFF_NORMED)
                _, max_val1, _, _ = cv2.minMaxLoc(match_result)
                result1 = max_val1 >= threshold
            
            # 두 번째 이미지 확인
            template2 = cv2.imread(f'{Settings.REF_IMG_DIR}/{image2_name}.png')
            result2 = False
            if template2 is not None:
                match_result = cv2.matchTemplate(screen_bgr, template2, cv2.TM_CCOEFF_NORMED)
                _, max_val2, _, _ = cv2.minMaxLoc(match_result)
                result2 = max_val2 >= threshold
            
            return (result1, result2)
        except Exception as e:
            print(f"이미지 비교 중 오류 발생: {str(e)}")
            return (False, False)
