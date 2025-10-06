import cv2
import numpy as np
from adb_shell.adb_device import AdbDeviceTcp
import time
from PIL import Image
import io
import os
import logging
from datetime import datetime
import atexit
import signal
import sys

def setup_logger():
    logger = logging.getLogger('ReseMara')
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    
    file_handler = logging.FileHandler('ReseMara.log', mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger()

def wait_for_user_input():
    input("계속하려면 아무 키나 누르세요...")

def cleanup():
    """프로그램 종료 시 실행될 정리 함수"""
    # cleanup이 이미 실행되었는지 확인하는 플래그
    if hasattr(cleanup, 'is_running'):
        return
    cleanup.is_running = True
    
    logger.debug("정리 작업 시작")
    try:
        if 'macro' in globals() and macro is not None:
            macro.close()
            
            if os.path.exists(port_log_file):
                try:
                    # 파일의 모든 포트 번호 읽기
                    with open(port_log_file, 'r') as f:
                        ports = f.readlines()
                    
                    # 현재 포트 번호를 제외한 나머지 포트들만 유지
                    current_port = str(macro.port)
                    remaining_ports = [p.strip() for p in ports if p.strip() != current_port]
                    
                    if remaining_ports:
                        # 남은 포트들이 있으면 파일 업데이트
                        with open(port_log_file, 'w') as f:
                            f.write('\n'.join(remaining_ports) + '\n')
                    else:
                        # 남은 포트가 없으면 파일 삭제
                        os.remove(port_log_file)
                        logger.debug("port.log 파일이 삭제되었습니다.")
                except Exception as e:
                    logger.error(f"포트 로그 파일 처리 중 오류 발생: {str(e)}")
    except Exception as e:
        logger.error(f"정리 작업 중 오류 발생: {str(e)}")
    
    logger.debug("프로그램 종료")

def signal_handler(signum, frame):
    """시그널 핸들러"""
    logger.debug("시그널 핸들러 호출됨")
    cleanup()
    sys.exit(0)

class ReseMara:
    """==========[ 초기화 및 기본 기능 ]=========="""
    def __init__(self, adb_port):
        logger.debug(f"ADB 포트 {adb_port}로 연결 시도 ...")
          # 포트 번호 저장
        self.device = AdbDeviceTcp('127.0.0.1', adb_port)
        try:
            self.device.connect()
            logger.debug("ADB 연결 성공!")
            self.port = adb_port
            # 필요한 폴더들 생성
            for folder in ['Row_Screen', 'Ref_Img', 'Accounts']:
                if not os.path.exists(folder):
                    os.makedirs(folder)
                    logger.debug(f"{folder} 폴더 생성 완료")
            
        except Exception as e:
            logger.error(f"ADB 연결 실패: {str(e)}")
            raise

    def close(self):
        logger.debug("ADB 연결 종료 중...")
        try:
            self.device.close()
            logger.debug("ADB 연결 종료 완료")
        except Exception as e:
            logger.error(f"ADB 연결 종료 중 오류 발생: {str(e)}")

    def capture_screen(self):
        try:
            result = self.device.shell('screencap -p', decode=False)
            image = Image.open(io.BytesIO(result))
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"Row_Screen/screen_{timestamp}.png"
            
            image.save(filename)
            
            # 크린샷 파일 개수 관리
            self.manage_screenshots()
            
            return np.array(image)
            
        except Exception as e:
            logger.error(f"화면 캡처 실패: {str(e)}")
            raise

    def manage_screenshots(self, max_files=30):
        """
        Row_Screen 폴더의 이미지 파일 개수를 관하는 함수
        max_files를 초과하는 경우 가장 오래된 파일부터 삭제
        
        Args:
            max_files (int): 유지할 최대 파일 개수 (기본값: 30)
        """
        try:
            # Row_Screen 폴더의 모든 png 파일 목록 가져오기
            files = [f for f in os.listdir('Row_Screen') if f.endswith('.png')]
            
            # 파일 개가 max_files 초과하는 경우
            if len(files) > max_files:
                # 파일을 생성 시간 순으로 정렬
                files.sort(key=lambda x: os.path.getctime(os.path.join('Row_Screen', x)))
                
                # 초과하는 만큼 오래된 파일부터 삭제
                for f in files[:len(files) - max_files]:
                    file_path = os.path.join('Row_Screen', f)
                    os.remove(file_path)
                    
        except Exception as e:
            logger.error(f"스크린샷 관리 중 오류 발생: {str(e)}")

    def click_position(self, x, y, wait_time=1):
        """
        지정된 좌표를 클릭하고 지정된 시간만큼 대기하는 함수
        
        Args:
            x (int): 클릭할 x 좌표
            y (int): 클릭할 y 좌표
            wait_time (float): 클릭 후 대기할 시간(초) (기본값: 1초)
            
        Returns:
            bool: 클릭 성공 여부
        """
        time.sleep(wait_time)
        
        try:
            logger.debug(f"좌표 클릭 시도: ({x}, {y})")
            self.device.shell(f'input tap {x} {y}')
            time.sleep(wait_time)  # 클릭 후 지정된 시간만큼 대기
            return True
        except Exception as e:
            logger.error(f"좌표 클릭 중 오류 발생: {str(e)}")
            wait_for_user_input()
            return False

    def get_current_package(self):
        """
        현재 포커스된 앱의 패키지 이름을  함수
        
        Returns:
            str: 패키지  (찾지 못한 경우 None)
        """
        try:
            # 현재 포커스된  정보 가져기
            result = self.device.shell('dumpsys window | grep mCurrentFocus')
            logger.debug(f"현재 창 정보: {result}")
            
            # 패키지 이름 추출 (일반적인 형식: mCurrentFocus=Window{...} PackageName/...)
            if result:
                import re
                match = re.search(r'{\w+\s+\w+\s+(\S+)}', result)
                if match:
                    package_name = match.group(1).split('/')[0]
                    logger.info(f"현재 실 중인 앱: {package_name}")
                    return package_name
            
            logger.error("현재 실행 중인 앱을 찾을 수 없습니다")
            return None
            
        except Exception as e:
            logger.error(f"패키지 이름 확인 중 오류 발생: {str(e)}")
            wait_for_user_input()
            return None

    """==========[ 매크로 보 기능 ]=========="""
    def find_and_click(self, image_name, threshold=0.75, timeout=30, stop_event=None):
        try:
            template_path = f'Ref_Img/{image_name}.png'
            
            template = cv2.imread(template_path)
            if template is None:
                logger.error(f"참조 이미지를 찾을 수 없음: {template_path}")
                wait_for_user_input()
                return False
            
            start_time = time.time()
            while True:
                if stop_event and stop_event.is_set():
                    logger.info("매크로 중지됨 (find_and_click).")
                    return False
                if time.time() - start_time > timeout:
                    logger.error(f"{timeout}초 동안 이미지를 찾지 못했습니다: {image_name}")
                    return False
                
                try:
                    screen = self.capture_screen()
                    screen_bgr = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
                    
                    result = cv2.matchTemplate(screen_bgr, template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    logger.debug(f"[{image_name}] 이미지 매칭 점수: {max_val:.4f} (임계값: {threshold})")
                    
                    if max_val >= threshold:
                        h, w = template.shape[:2]
                        center_x = max_loc[0] + w//2
                        center_y = max_loc[1] + h//2
                        
                        logger.debug(f"[{image_name}] 이미지 발견 (매칭 점수: {max_val:.4f})")
                        logger.debug(f"[{image_name}] 클릭 실행: ({center_x}, {center_y})")
                        self.device.shell(f'input tap {center_x} {center_y}')
                        return True
                    else:
                        logger.debug(f"[{image_name}] 매칭된 이미지가 없습니다. 다시 시도합니다...")
                        time.sleep(1)
                        
                except Exception as e:
                    logger.error(f"화면 캡처 중 오류 발생: {str(e)}")
                    wait_for_user_input()
                    continue
                
        except Exception as e:
            logger.error(f"이미지 매칭/클릭 중 오류 발생: {str(e)}")
            wait_for_user_input()
            return False

    def wait_for_image(self, image_name, threshold=0.75, timeout=20, stop_event=None):
        try:
            template_path = f'Ref_Img/{image_name}.png'
            
            template = cv2.imread(template_path)
            if template is None:
                logger.error(f"참조 이미지를 찾을 수 없음: {template_path}")
                wait_for_user_input()
                return False
            
            start_time = time.time()
            while True:
                if stop_event and stop_event.is_set():
                    logger.info("매크로 중지됨 (wait_for_image).")
                    return False
                if time.time() - start_time > timeout:
                    logger.error(f"{timeout}초 동안 이미지를 찾지 못했습니다: {image_name}")
                    return False
                
                try:
                    screen = self.capture_screen()
                    screen_bgr = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
                    
                    result = cv2.matchTemplate(screen_bgr, template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    logger.debug(f"[{image_name}] 이미지 매칭 점수: {max_val:.4f} (임계값: {threshold})")
                    
                    if max_val >= threshold:
                        logger.debug(f"[{image_name}] 이미지 발견 (매칭 점수: {max_val:.4f})")
                        logger.info(f"이미지 발견: {image_name}")
                        return True
                    else:
                        logger.debug(f"[{image_name}] 매칭된 미지가 없습니다. 다시 시도합니다...")
                        time.sleep(1)
                        
                except Exception as e:
                    logger.error(f"화면 캡처 중 오류 발생: {str(e)}")
                    wait_for_user_input()
                    continue
                
        except Exception as e:
            logger.error(f"이미지 대기 중 오류 발생: {str(e)}")
            wait_for_user_input()
            return False

    def input_text_via_adb(self, text):
        """
        ADB를 통해 문자를 입력하는 함수
        
        Args:
            text (str): 입력할 텍스트
        """
        try:
            # 일반 텍스트 력
            self.device.shell(f'input text {text}')  # 따옴표 제거
            logger.debug(f"텍스트 입력 완료: {text}")
            return True
        
        except Exception as e:
            logger.error(f"텍스트 입력 중 오류 발생: {str(e)}")
            return False

    def close_current_app(self):
        """
        현재 실행 중인 앱을 종료하는 함수
        
        Returns:
            bool:  종료 성공 여부
        """
        try:
            # 현재 실행 중인 앱의 패키지 이름 져오기
            package_name = self.get_current_package()
            
            if package_name:
                logger.debug(f"앱 종료 시도: {package_name}")
                # force-stop 명령어  강제 료
                self.device.shell(f'am force-stop {package_name}')
                logger.info(f"앱이 종료되었습니다: {package_name}")
                return True
            else:
                logger.error("료할 앱을 찾을 수 없습니다")
                return False
                
        except Exception as e:
            logger.error(f"앱 종료 중 오류 발생: {str(e)}")
            wait_for_user_input()
            return False

    def compare_images(self, image1_name=None, image2_name=None, threshold=0.7):
        """
        두 이미지 비교하여 자동으로 판단하는 함수
        
        Args:
            image1_name (str): 첫 번째 비교할 이미지 이름
            image2_name (str): 두 번째 비교 이미지 이름
            threshold (float): 이미 매칭 임계값 (0~1)
            
        Returns:
            int: 판단 결과 (1: 종료, 2: 리셋)
        """
        try:
            result1 = False
            result2 = False
            
            if image1_name and image2_name:
                # 현재 시간을 파일명으 사용
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                account_filename = f"Accounts/account_{timestamp}"
                
                # 스크린샷 저장
                screen = self.capture_screen()
                screen_bgr = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
                cv2.imwrite(f"{account_filename}.png", screen_bgr)
                
                # 이미지 비교 로직
                template1 = cv2.imread(f'Ref_Img/{image1_name}.png')
                if template1 is not None:
                    result1 = cv2.matchTemplate(screen_bgr, template1, cv2.TM_CCOEFF_NORMED)
                    _, max_val1, _, _ = cv2.minMaxLoc(result1)
                    result1 = max_val1 >= threshold
                
                template2 = cv2.imread(f'Ref_Img/{image2_name}.png')
                if template2 is not None:
                    result2 = cv2.matchTemplate(screen_bgr, template2, cv2.TM_CCOEFF_NORMED)
                    _, max_val2, _, _ = cv2.minMaxLoc(result2)
                    result2 = max_val2 >= threshold
                
                # 결과 로
                logger.info(f"{image1_name}: {'발견' if result1 else '미발견'}")
                logger.info(f"{image2_name}: {'발견' if result2 else '미발견'}")
                
                #  파일 복사
                import shutil
                shutil.copy2('ReseMara.log', f"{account_filename}.log")
                
                # 자동 판단
                if result1 or result2:  # 둘 중 하나라도 발견되면 종료
                    logger.info("목표 캐릭터가 발견되어 매크로를 종료합니다.")
                    return 1
                else:  # 둘 다 발견되지 않으면 리셋
                    logger.info("목표 캐릭터가 발견되지 않아 리셋을 시작합니다.")
                    return 2
        except Exception as e:
            logger.error(f"이미지 비교 중 오류 발생: {str(e)}")
            return 1  # 오류 발생시 종료
    
