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
    """==========[ 매크로 핵심 기능 ]=========="""
    def macro_sequence(self, wait_image, click_image=None, wait_time=5):
        """이미지 찾아서 클릭하는 시퀀스
        
        Args:
            wait_image (str): 대기할 이미 이름
            click_image (str): 클릭할 이미지 이름 (None이면 wait_image와 동일)
            wait_time (float): 대기 시간 (기본값: 1초)
            
        Returns:
            bool: 시퀀스 성공 여부 (True: 성공, False: 실패)
        """
        if click_image is None:
            click_image = wait_image
        
        # 이미지를 찾았을 때만 클릭 실행
        if self.wait_for_image(wait_image):
            if self.find_and_click(click_image):
                logger.info(f"{click_image} 버튼을 찾아 클릭했습니다")
                time.sleep(wait_time)
                return True
            else:
                logger.info(f"{click_image} 버튼 클릭에 실패했습니다")
                return False
        else:
            logger.info(f"{wait_image} 이미지를 찾지 못해 다음 동작으로 어갑니다")
            return False

    def macro_touch_sequence(self, x=300, y=300, wait_image=None, click_image=None, wait_time=5):
        """특정 좌표를 클릭한 후 이미지를 찾아 클릭하는 시퀀스
        
        Args:
            x (int): 클릭할 x 좌표 (기본값: 300)
            y (int): 클릭할 y 좌표 (기본값: 300)
            wait_image (str): 대기할 이미지 이름
            click_image (str): 클릭할 이미지 이름 (None이면 wait_image와 동일)
            wait_time (float): 대기 시간 (기본값: 1초)
        
        Returns:
            bool: 시퀀스 성공 여부 (True: 성공, False: 실패)
        """
        if click_image is None and wait_image is not None:
            click_image = wait_image
        
        time.sleep(2)
        self.click_position(x, y)
        
        if wait_image:
            # 이미지를 찾았을 때만 클릭 실행
            if self.wait_for_image(wait_image):
                self.click_position(x, y)
                if self.find_and_click(click_image):
                    logger.info(f"{click_image} 버튼을 찾아 클릭했습니다")
                    time.sleep(wait_time)
                    return True
                else:
                    logger.info(f"{click_image} 버튼 클릭에 실패했습니다")
                    return False
            else:
                logger.info(f"{wait_image} 이미지를 찾지 못 다음 동작으로 넘어갑니다")
                return False
        else:
            time.sleep(wait_time)
            return True  # 이미지 검사가 없는 경우는 공으로 간주

    def run_macro(self):
        try:
            # 기존의 반복적인 패턴을 macro_sequence로 변경
            self.macro_sequence("app_icon")
            if not self.macro_sequence("title_start"):
                self.macro_sequence("title_start")
            self.macro_sequence("guest_login")
            #self.macro_sequence("guest_login_confirm")

            # 컷신 스킵 시도 (실패시 재시도)
            if not self.macro_touch_sequence(wait_image="first_cutscean", click_image="cutscene_skip"):
                self.macro_touch_sequence(wait_image="cutscene_skip")
            
            # 튜토리얼 대사 시퀀스 1-4
            self.macro_sequence("tuto_dialog_1")
            self.macro_sequence("tuto_dialog_2")
            self.macro_sequence("tuto_dialog_3")
            self.macro_sequence("tuto_dialog_4")
            
            self.macro_sequence("tuto_action_1")
            self.macro_sequence("tuto_dialog_5", "tuto_action_2")
            self.macro_sequence("tuto_dialog_6", "tuto_action_3")
            self.macro_sequence("tuto_dialog_7", "battle_confirm_button")
            
            # 튜대 8-9
            self.macro_sequence("tuto_dialog_8")
            self.macro_sequence("tuto_dialog_9")
            
            self.macro_touch_sequence(wait_image="cutscene_skip")
            
            # 튜토대사 10-17
            self.macro_sequence("tuto_dialog_10")
            self.macro_sequence("tuto_dialog_11")
            self.macro_sequence("tuto_dialog_12")
            self.macro_sequence("tuto_dialog_13")
            self.macro_sequence("tuto_dialog_14")
            self.macro_sequence("tuto_dialog_15")
            self.macro_sequence("tuto_dialog_16")
            
            # 튜토행동 5-8
            self.macro_sequence("tuto_dialog_17", "tuto_action_5")
            self.macro_sequence("tuto_action_6", wait_time=5)
            self.macro_sequence("tuto_action_7")
            self.macro_sequence("tuto_action_8")
            
            self.macro_sequence("battle_confirm_button", wait_time=5)
            
            # 튜토대사 18-27
            self.macro_sequence("tuto_dialog_18")
            self.macro_sequence("tuto_dialog_19")
            self.macro_sequence("tuto_dialog_20")
            self.macro_sequence("tuto_dialog_21")
            self.macro_sequence("tuto_dialog_22", wait_time=5)
            self.macro_sequence("tuto_dialog_23")
            self.macro_sequence("tuto_dialog_24")
            self.macro_sequence("tuto_dialog_25")
            self.macro_sequence("tuto_dialog_26")
            self.macro_sequence("tuto_dialog_27")
            
            self.macro_touch_sequence(wait_image="cutscene_skip", wait_time=5)
            self.macro_touch_sequence(wait_image="cutscene_skip", wait_time=5)

            # 여 지휘관을 원하면 아래의 코드로 실행
            #self.macro_touch_sequence(wait_image="nickname_creation_confirm", wait_time=5)
            # 남지휘관 코드
            self.macro_sequence("nickname_input_confirm")
            self.macro_sequence("nickname_creation_confirm", wait_time=5)

            self.macro_sequence("skip_after_creation")
            self.macro_sequence("story_skip_confirm")


            # 1-1 대 시퀀스
            self.macro_sequence("1-1_dialog_1")
            self.macro_sequence("1-1_dialog_2")
            self.macro_sequence("1-1_dialog_3")
            self.macro_sequence("1-1_dialog_4")
            self.macro_sequence("1-1_dialog_5")
            self.macro_sequence("1-1_dialog_6")
            self.macro_sequence("1-1_dialog_7")
            self.macro_sequence("1-1_dialog_8", "1-1_action_1")
            self.macro_sequence("1-1_dialog_9", "1-1_action_2")
            self.macro_sequence("1-1_dialog_10", "battle_confirm_button")

            self.macro_sequence("1-1_dialog_11")
            self.macro_sequence("1-1_action_3")
            self.macro_sequence("battle_confirm_button")

            self.macro_sequence("1-1_dialog_12", wait_time=5)
            self.macro_sequence("dialog_skip_button", wait_time=5)
            self.macro_sequence("1-1_dialog_13")
            self.macro_sequence("1-1_dialog_14")
            self.macro_sequence("1-1_dialog_15")
            self.macro_sequence("1-1_dialog_16")
            self.macro_sequence("1-1_dialog_17")
            self.macro_sequence("1-1_dialog_18")
            self.macro_sequence("1-1_dialog_19")
            self.macro_sequence("1-1_dialog_20", "1-1_action_4")
            self.macro_sequence("1-1_dialog_21", "1-1_action_5")
            self.macro_sequence("1-1_dialog_22", "battle_confirm_button")
            self.macro_sequence("1-1_dialog_23")
            self.macro_sequence("1-1_dialog_24")
            self.macro_sequence("1-1_dialog_25", "1-1_action_6")
            self.macro_sequence("1-1_dialog_26")
            self.macro_sequence("1-1_dialog_27", "1-1_action_13")
            self.macro_sequence("battle_confirm_button", wait_time=5)
            self.macro_sequence("1-1_action_7")
            self.macro_sequence("battle_confirm_button", wait_time=5)
            self.macro_sequence("1-1_action_8")
            self.macro_sequence("battle_confirm_button", wait_time=5)
            self.macro_sequence("1-1_dialog_28", wait_time=5)
            self.macro_sequence("dialog_skip_button", wait_time=5)
            self.macro_sequence("dialog_skip_button", wait_time=5)

            self.macro_sequence("1-1_dialog_29")
            self.macro_sequence("1-1_dialog_30")
            self.macro_sequence("1-1_dialog_31")

            self.macro_sequence("1-1_action_11", wait_time=5)
            self.macro_sequence("1-1_action_11", wait_time=5)
            self.macro_sequence("1-1_dialog_32")
            self.macro_sequence("1-1_dialog_33")

            self.macro_sequence("1-1_action_11", wait_time=5)
            self.macro_sequence("1-1_action_11", wait_time=5)

            if not self.macro_sequence("1-1_dialog_34"):
                logger.info("클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("1-1_dialog_34")

            self.macro_sequence("1-1_action_12")

            self.macro_sequence("1-1_dialog_35")
            self.macro_sequence("1-1_dialog_36", wait_time=5)

            if not self.macro_sequence("level_up"):
                logger.info("레벨업 클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("level_up")
                
            if not self.macro_sequence("mission_complete"):
                logger.info("미션컴플리트 클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("level_up")
                self.macro_sequence("mission_complete")

            self.macro_sequence("stage_clear_confirm")
            self.macro_touch_sequence(wait_image="cutscene_skip", wait_time=5)
            self.macro_touch_sequence(wait_image="cutscene_skip", wait_time=5)
            self.macro_sequence("dialog_skip_button")
            self.macro_touch_sequence(wait_image="cutscene_skip", wait_time=5)

            self.macro_sequence("lobby_event_screen")
            self.macro_sequence("lobby_preparation")
            self.macro_sequence("1st_stage_entry_confirm")

            self.macro_sequence("1-2_stage_select")
            self.macro_sequence("stage_entry")
            self.macro_sequence("dialog_skip_button", wait_time=5)
            self.macro_sequence("1-2_dialog_1")
            self.macro_sequence("1-2_dialog_2")
            self.macro_sequence("1-2_dialog_3")
            self.macro_sequence("1-2_dialog_4")
            self.macro_sequence("1-2_dialog_5")
            self.macro_sequence("1-2_dialog_6")
            self.macro_sequence("1-2_dialog_7")

            self.macro_sequence("1-2_dialog_8")
            self.macro_sequence("1-2_dialog_9")
            self.macro_sequence("1-2_dialog_10", "1-2_action_1")
            self.macro_sequence("1-2_dialog_11", "1-2_action_2")
            self.macro_sequence("1-2_dialog_12", "1-2_action_3")
            self.macro_sequence("1-2_dialog_13", "1-2_action_2")
            self.macro_sequence("1-2_dialog_14", "1-2_action_4")
            self.macro_sequence("1-2_dialog_15", "auto_stage", wait_time=20)
            self.macro_sequence("1-2_dialog_16", wait_time=10)

            if not self.macro_sequence("level_up"):
                logger.info("레벨업 클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("level_up")

            if not self.macro_sequence("mission_complete"):
                logger.info("미션컴플리트 클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("level_up")
                self.macro_sequence("mission_complete")
            
            self.macro_sequence("stage_clear_confirm_small")
            self.macro_sequence("dialog_skip_button", wait_time=5)

            self.macro_sequence("1-3_stage_select")
            self.macro_sequence("stage_entry") # 여기서부터 재검해야함
            self.macro_sequence("1-3_dialog_1")
            self.macro_sequence("1-3_dialog_2", wait_time=5)
            self.macro_sequence("1-3_dialog_3")
            self.macro_sequence("1-3_dialog_4")
            self.macro_sequence("1-3_dialog_5")
            self.macro_sequence("1-3_dialog_6")
            self.macro_sequence("1-3_dialog_7")
            #self.macro_touch_sequence(wait_image="cutscene_skip", wait_time=5)

            #self.macro_sequence("skip_notification_popup")
            #self.macro_sequence("skip_popup_check_done", "skip_done_confirm")
            # 디버깅용 스탑포인트
            #wait_for_user_input()
            self.macro_sequence("1-3_action_1", wait_time=7)
            self.click_position(100, 450, wait_time=8)
            self.macro_sequence("auto_stage", wait_time=15)
            self.macro_sequence("1-3_dialog_8")
            
            if not self.macro_sequence("1-3_action_3", wait_time=5):
                logger.info("1-3_action_3 클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("1-3_action_3", wait_time=5)

            self.macro_sequence("1-3_dialog_9")

            if not self.macro_sequence("level_up"):
                logger.info("레벨업 클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("level_up")
                
            if not self.macro_sequence("mission_complete"):
                logger.info("미션컴플리트 클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("level_up")
                self.macro_sequence("mission_complete")
            self.macro_sequence("stage_clear_confirm")

            self.macro_sequence("sl-1-1_stage_select")
            self.macro_sequence("story_stage_view")
            self.macro_sequence("dialog_skip_button", wait_time=5)
            self.macro_sequence("empty_area_touch")

            self.macro_sequence("1-4_stage_select")
            self.macro_sequence("stage_entry")
            self.macro_sequence("dialog_skip_button", wait_time=5)
            self.macro_sequence("1-4_dialog_1")
            self.macro_sequence("1-4_dialog_2")
            self.macro_sequence("1-3_action_1")
            self.macro_sequence("auto_stage", wait_time=25)

            if not self.macro_sequence("level_up"):
                logger.info("레벨업 클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("level_up")
                
            if not self.macro_sequence("mission_complete"):
                logger.info("미션컴플리트 클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("level_up")
                self.macro_sequence("mission_complete")

            self.macro_sequence("stage_clear_confirm")

            self.macro_sequence("sl-1-2_stage_select")
            self.macro_sequence("story_stage_view")
            self.macro_sequence("dialog_skip_button", wait_time=5)
            self.macro_sequence("empty_area_touch")

            self.macro_sequence("recruit_dialog_1", "lobby_button", wait_time=10)
            self.macro_sequence("empty_area_touch")
            if not self.macro_sequence("recruit_dialog_2", "recruit_button"):
                logger.info("recruit_dialog_2 클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("empty_area_touch")
                self.macro_sequence("recruit_dialog_2", "recruit_button")
            self.macro_sequence("recruit_dialog_3", "recruit_action_3")
            self.macro_sequence("recruit_dialog_4", "recruit_action_4")
            if not self.macro_touch_sequence(wait_image="gacha_preview_skip", wait_time=20):
                logger.info("gacha_preview_skip 클릭 실패, 재시도")
                time.sleep(5)
                self.click_position(100, 400, wait_time=20)
            if not self.macro_touch_sequence(wait_image="gacha_result_close", wait_time=5):
                logger.info("gacha_result_close 클릭 실패, 재시도")
                time.sleep(5)
                self.click_position(100, 400, wait_time=5)
                self.macro_touch_sequence(wait_image="gacha_result_close", wait_time=5)
            if not self.macro_sequence("recruit_dialog_5", "lobby_button"):
                logger.info("lobby_button 클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("lobby_button_other")

            self.macro_sequence("recruit_dialog_6", "maintenance_button")
            self.macro_touch_sequence(wait_image="cutscene_skip", wait_time=5)
            self.macro_sequence("maintenance_tutorial_skip")
            if not self.macro_sequence("lobby_button"):
                logger.info("lobby_button 클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("lobby_button_other")

            # self.macro_sequence("lobby_preparation")
            # self.macro_sequence("1st_stage_entry_confirm")

            # self.macro_sequence("1-5_stage_select")
            # self.macro_sequence("stage_entry")
            # self.macro_sequence("1-5_dialog_1")
            # self.macro_sequence("1-5_dialog_2")
            # self.macro_sequence("1-3_action_1", wait_time=5)
            # self.macro_sequence("1-5_dialog_3")
            # self.macro_sequence("1-5_dialog_4")
            # self.macro_sequence("1-5_dialog_5")
            # self.macro_sequence("1-3_action_3")
            # self.macro_sequence("auto_stage", wait_time=20)

            # if not self.macro_sequence("level_up"):
            #     logger.info("레벨업 클릭 실패, 재시도")
            #     time.sleep(2)
            #     self.macro_sequence("level_up")
                
            # if not self.macro_sequence("mission_complete"):
            #     logger.info("션컴플리트 클릭 실패, 재도")
            #     time.sleep(2)
            #     self.macro_sequence("level_up")
            #     self.macro_sequence("mission_complete")

            # self.macro_sequence("1-5_dialog_6" ,"stage_clear_confirm")
            # self.macro_sequence("dialog_skip_button", wait_time=5)
            # self.macro_sequence("weapon_tutorial_skip")
            # if not self.macro_sequence("lobby_button"):
            #     logger.info("lobby_button 클릭 실패, 재시도")
            #     time.sleep(2)
            #     self.macro_sequence("lobby_button_other")
            # self.macro_sequence("empty_area_touch")
            # self.macro_sequence("1-3_action_3")

            # self.macro_sequence("beppo_reward_popup")
            # self.macro_sequence("beppo_reward_popup_receive")
            # self.macro_sequence("empty_area_touch")
            # self.macro_sequence("back_button")

            self.macro_sequence("mail_button")
            self.macro_sequence("mail_all_receive", wait_time=15)
            self.click_position(100, 450, wait_time=5)
            if not self.macro_touch_sequence(wait_image="empty_area_touch", wait_time=5):
                logger.info("empty_area_touch 클릭 실패, 재시도")
                time.sleep(2)
                self.click_position(100, 450, wait_time=5)
                self.macro_sequence("empty_area_touch", wait_time=5)
            if not self.macro_sequence("back_button"):
                logger.info("back_button 릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("back_button_other")

            # 초보자뽑기 40연차
            self.macro_sequence("recruit_button")
            self.macro_sequence("beginner_draw_10_times", wait_time=5)
            self.close_current_app()
            time.sleep(10)
            self.macro_sequence("app_icon")
            if not self.macro_sequence("title_start", wait_time=5):
                logger.info("title_start 클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("title_start", wait_time=5)
            # 초보자뽑기 10연차
            self.macro_sequence("recruit_button")
            self.macro_sequence("beginner_draw_10_times", wait_time=5)
            self.close_current_app()
            time.sleep(10)
            self.macro_sequence("app_icon")
            if not self.macro_sequence("title_start", wait_time=5):
                logger.info("title_start 클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("title_start", wait_time=5)
            #
            self.macro_sequence("recruit_button")
            self.macro_sequence("beginner_draw_10_times", wait_time=5)
            self.close_current_app()
            time.sleep(10)
            self.macro_sequence("app_icon")
            if not self.macro_sequence("title_start", wait_time=5):
                logger.info("title_start 클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("title_start", wait_time=5)
            # 초보자뽑기 30연차
            self.macro_sequence("recruit_button")
            self.macro_sequence("beginner_draw_10_times", wait_time=5)
            self.close_current_app()
            time.sleep(10)
            self.macro_sequence("app_icon")
            if not self.macro_sequence("title_start", wait_time=5):
                logger.info("title_start 클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("title_start", wait_time=5)
            # 초보자뽑기 40연차
            self.macro_sequence("recruit_button")
            self.macro_sequence("beginner_draw_10_times", wait_time=5)
            self.close_current_app()
            time.sleep(10)
            self.macro_sequence("app_icon")
            if not self.macro_sequence("title_start", wait_time=5):
                logger.info("title_start 클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("title_start", wait_time=5)
            # 초보자뽑기 50연차 완료

            self.macro_sequence("recruit_button")
            self.macro_sequence("gacha_shop")
            self.macro_sequence("pickup_item_purchase")
            self.macro_sequence("purchase_item_available")
            self.macro_sequence("purchase_item_available")
            self.macro_sequence("purchase_item_available")
            self.macro_sequence("purchase_item_available")
            self.macro_sequence("purchase_item_available")
            self.macro_sequence("gacha_item_confirm")
            self.macro_sequence("empty_area_touch")
            if not self.macro_sequence("back_button"):
                logger.info("back_button 클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("back_button_other")
            self.macro_sequence("number_of_items")
            self.macro_sequence("pickup_10_times", wait_time=3)
            #self.macro_sequence("gacha_item_confirm", wait_time=5)
            self.close_current_app()
            time.sleep(5)
            self.macro_sequence("app_icon", wait_time=5)
            if not self.macro_sequence("title_start", wait_time=5):
                logger.info("title_start 클릭 실패, 재시도")
                time.sleep(2)
                self.macro_sequence("title_start", wait_time=5)

            self.macro_sequence("maintenance_button")
            self.macro_sequence("maintenance_list_expand", wait_time=5)

            # 이미지 교 및 용자 선택 처리
            choice = self.compare_images("suomi", "kyeongu")
            if choice == 1:
                logger.info("목표 달성하여 매크로 종료를 선택했습니다.")
                return
            elif choice == 2:
                logger.info("계정 리셋을 시작합니다.")
                self.reset_account()
                self.run_macro()  # 매크로 재시작
            
        except Exception as e:
            logger.error(f"매크로 실행 중 오류 발생: {str(e)}")
            wait_for_user_input()

    def reset_account(self):
        """
        계정 리을 위한 함수
        """
        # 향후 리셋 로직 구현
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
    def find_and_click(self, image_name, threshold=0.75, timeout=30):
        try:
            template_path = f'Ref_Img/{image_name}.png'
            
            template = cv2.imread(template_path)
            if template is None:
                logger.error(f"참조 이미지를 찾을 수 없음: {template_path}")
                wait_for_user_input()
                return False
            
            start_time = time.time()
            while True:
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

    def wait_for_image(self, image_name, threshold=0.75, timeout=20):
        try:
            template_path = f'Ref_Img/{image_name}.png'
            
            template = cv2.imread(template_path)
            if template is None:
                logger.error(f"참조 이미지를 찾을 수 없음: {template_path}")
                wait_for_user_input()
                return False
            
            start_time = time.time()
            while True:
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
                if result1 and result2:  # 둘 중 하나라도 발견되면 종료
                    logger.info("목표 캐릭터가 발견되어 매크로를 종료합니다.")
                    return 1
                else:  # 둘 다 발견되지 않으면 리셋
                    logger.info("목표 캐릭터가 발견되지 않아 리셋을 시작합니다.")
                    return 2
        except Exception as e:
            logger.error(f"이미지 비교 중 오류 발생: {str(e)}")
            return 1  # 오류 발생시 종료
    
if __name__ == "__main__":
    logger.debug("프로그램 시작")
    # 종료 시 cleanup 함수 등록
    atexit.register(cleanup)
    
    # Ctrl+C핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    
    # port.log 파일 경로 바탕화면으로 설정
    port_log_file = os.path.join(os.path.expanduser("~"), "Desktop", "port.log")
    
    # 포트 입력 또는 자동 순환
    port_input = input("MuMu Player의 ADB 포트를 입력하세요 (자동 검색은 Enter): ").strip()

    if port_input:
        # 수동 포트 입력의 경우
        try:
            adb_port = int(port_input)
            if 1024 <= adb_port <= 65535:
                ports_to_try = [adb_port]
            else:
                logger.error("유효하지 않은 포트 번호입니다. 자동 검색을 시작합니다.")
                ports_to_try = [16384, 16416, 16448, 16480, 16512, 16544, 16576]
        except ValueError:
            logger.error("올바른 포트 번호가 아닙니다. 자동 검색을 시작합니다.")
            ports_to_try = [16384, 16416, 16448, 16480, 16512, 16544, 16576]
    else:
        # 자동 순환의 경우, 먼저 port.log 확인
        try:
            # MuMu 에뮬레이터의 일반적인 ADB 포트 리스트
            mumu_ports = [16384, 16416, 16448, 16480, 16512, 16544, 16576]
            
            if os.path.exists(port_log_file):
                with open(port_log_file, 'r') as f:
                    used_ports = [int(port.strip()) for port in f.readlines() if port.strip()]
                    logger.info(f"이전 성공 포트들: {used_ports}")
                    # 이미 사용 중인 포트들을 제외한 나머지 포트들 리스트 생성
                    ports_to_try = [p for p in mumu_ports if p not in used_ports]
            else:
                ports_to_try = mumu_ports
                logger.info("포트 자동 검색을 시작합니다 (MuMu 에뮬레이터 포트)")
        except Exception as e:
            logger.error(f"포트 로그 파일 읽기 실패: {str(e)}")
            ports_to_try = mumu_ports
    
    macro = None
    try:
        # port.log 파일 생성/추가
        try:
            # port.log 파일이 없으면 생성, 있으면 유지
            if not os.path.exists(port_log_file):
                open(port_log_file, 'w').close()
        except Exception as e:
            logger.error(f"포트 로그 파일 생성 실패: {str(e)}")

        for port in ports_to_try:
            try:
                logger.debug(f"포트 {port}로 연결 시도 중...")
                macro = ReseMara(port)
                logger.info(f"포트 {port}로 연결 성공!")
                # 성공한 포트 번호를 파일에 추가
                try:
                    with open(port_log_file, 'a') as f:
                        f.write(f"{port}\n")
                except Exception as e:
                    logger.error(f"포트 로그 파일 쓰기 실패: {str(e)}")
                break
            except Exception as e:
                logger.debug(f"포트 {port} 연결 실패: {str(e)}")
                continue
        
        if macro is None:
            logger.error("사용 가능한 ADB 포트를 찾지 못했습니다.")
            exit(1)
        
        logger.info("연결 테스트가 완료되었습니다.")
        logger.info("매크로를 시작합니다.")
        
        macro.run_macro()
        logger.info("매크로가 완료되었습니다.")
            
    except KeyboardInterrupt:
        logger.info("\n사용자가 프로그램을 중단했습니다.")
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {str(e)}")
