import json
import logging
import os
import time

logger = logging.getLogger('ReseMara')

class MacroEngine:
    def __init__(self, device, macro_flow, stop_event, progress_file='progress.json'):
        self.device = device
        self.macro_flow = macro_flow
        self.state_keys = list(self.macro_flow.keys())
        self.progress_file = progress_file
        self.stop_event = stop_event

        self.current_state_index = 0
        self.current_action_index = 0
        self._load_progress()

    def _load_progress(self):
        """Loads the macro progress from the progress file."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)

                last_state = progress.get('current_state')
                self.current_action_index = progress.get('current_action_index', 0)

                if last_state in self.state_keys:
                    self.current_state_index = self.state_keys.index(last_state)
                    logger.info(f"진행 상황을 불러왔습니다. '{last_state}' 상태의 {self.current_action_index + 1}번째 행동부터 재개합니다.")
                else:
                    logger.info("저장된 상태를 찾을 수 없습니다. 처음부터 시작합니다.")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"진행 상황 파일을 읽는 데 실패했습니다: {e}. 처음부터 시작합니다.")
                self._reset_progress()
        else:
            logger.info("진행 상황 파일이 없습니다. 처음부터 시작합니다.")

    def _save_progress(self, state_index, action_index):
        """Saves the current macro progress."""
        progress = {
            'current_state': self.state_keys[state_index],
            'current_action_index': action_index + 1  # Save the index of the *next* action
        }
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=4)
        logger.debug(f"진행 상황 저장됨: 상태={progress['current_state']}, 다음 행동 인덱스={progress['current_action_index']}")

    def _reset_progress(self):
        """Resets the progress file."""
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
        self.current_state_index = 0
        self.current_action_index = 0
        logger.info("진행 상황이 초기화되었습니다.")

    def run(self):
        """Runs the entire macro flow."""
        while self.current_state_index < len(self.state_keys):
            if self.stop_event.is_set():
                logger.info("매크로 중지 신호 감지됨 (상태 루프).")
                break

            state_name = self.state_keys[self.current_state_index]
            actions = self.macro_flow[state_name]

            logger.info(f"========[ 상태 시작: {state_name} ]========")

            while self.current_action_index < len(actions):
                if self.stop_event.is_set():
                    logger.info("매크로 중지 신호 감지됨 (액션 루프).")
                    break

                action_details = actions[self.current_action_index]
                comment = action_details.get('comment', 'N/A')
                logger.info(f"-----> 행동 실행: {action_details['action']} ({comment})")

                success, result = self._execute_action(action_details)

                if self.stop_event.is_set():
                    logger.info("행동 실행 후 중지 신호 감지됨.")
                    break

                if not success:
                    if action_details.get('optional', False):
                        logger.warning("선택적 행동에 실패했지만 계속 진행합니다.")
                        self.current_action_index += 1
                        self._save_progress(self.current_state_index, self.current_action_index -1)
                        continue
                    else:
                        logger.error("필수 행동에 실패하여 매크로를 중단합니다. 문제를 해결하고 다시 실행하세요.")
                        return # Stop execution

                # Handle special commands returned from actions
                if result == '__RESTART__':
                    logger.info("매크로를 처음부터 다시 시작합니다...")
                    self._reset_progress()
                    # Restart the outer loop
                    self.current_state_index = 0
                    self.current_action_index = 0
                    break # break action loop
                elif result == '__END__':
                    logger.info("목표를 달성하여 매크로를 성공적으로 종료합니다.")
                    self._reset_progress() # Clean up for next run
                    return
                elif result and result in self.state_keys: # Branching
                    logger.info(f"'{result}' 상태로 분기합니다.")
                    self.current_state_index = self.state_keys.index(result)
                    self.current_action_index = 0
                    self._save_progress(self.current_state_index -1, len(self.macro_flow[self.state_keys[self.current_state_index -1]])-1)
                    break # break action loop to jump to the new state

                # If we successfully executed an action, save progress and move to the next
                self._save_progress(self.current_state_index, self.current_action_index)
                self.current_action_index += 1

            else: # This 'else' belongs to the inner 'while' loop, runs if the loop finished without 'break'
                self.current_state_index += 1
                self.current_action_index = 0
                continue # Continue to the next state

            # This code is reached if the inner loop was broken by a command (branch, restart, stop)
            if self.stop_event.is_set():
                break
            if result == '__RESTART__':
                continue # Restart the outer while loop
            elif result and result in self.state_keys:
                continue # Continue the outer while loop at the new state index

    def _execute_action(self, action_details):
        """Dispatches to the correct action method."""
        action_type = action_details.get('action')
        params = action_details.get('params', {})

        action_map = {
            'Image_Click': self._perform_image_click,
            'Pos_Click_Then_Image_Click': self._perform_pos_click_then_image_click,
            'Click_Pos': self.device.click_position,
            'Input_Text': self.device.input_text_via_adb,
            'Close_App': self.device.close_current_app,
            'Special_Command': self._handle_special_command,
        }

        method = action_map.get(action_type)
        if not method:
            logger.error(f"알 수 없는 행동 유형: {action_type}")
            return False, None

        try:
            # Pass stop_event to methods that support it
            if action_type in ['Image_Click', 'Pos_Click_Then_Image_Click', 'Special_Command']:
                params['stop_event'] = self.stop_event

            result = method(**params)
            if isinstance(result, tuple):
                return result
            return result, None
        except Exception as e:
            logger.error(f"'{action_type}' 행동 실행 중 오류 발생: {e}")
            return False, None

    # --- Action Implementations ---

    def _perform_image_click(self, wait_image, click_image=None, wait_time=5, threshold=0.75, timeout=20, stop_event=None):
        if click_image is None:
            click_image = wait_image

        logger.debug(f"이미지 '{wait_image}'를 기다리는 중...")
        if self.device.wait_for_image(wait_image, threshold=threshold, timeout=timeout, stop_event=stop_event):
            if stop_event and stop_event.is_set(): return False
            logger.debug(f"이미지 '{click_image}'를 클릭하는 중...")
            if self.device.find_and_click(click_image, threshold=threshold, timeout=5, stop_event=stop_event):
                logger.info(f"'{click_image}' 클릭 성공.")
                if stop_event and stop_event.is_set(): return False
                time.sleep(wait_time)
                return True
            else:
                logger.error(f"'{click_image}' 클릭 실패.")
                return False
        else:
            logger.error(f"'{wait_image}' 이미지를 시간 내에 찾지 못했습니다.")
            return False

    def _perform_pos_click_then_image_click(self, x=300, y=300, wait_image=None, click_image=None, wait_time=5, threshold=0.75, timeout=20, stop_event=None):
        if click_image is None and wait_image is not None:
            click_image = wait_image

        if stop_event and stop_event.is_set(): return False
        time.sleep(2)
        self.device.click_position(x, y) # Initial touch

        if not wait_image:
            if stop_event and stop_event.is_set(): return False
            time.sleep(wait_time)
            return True

        logger.debug(f"이미지 '{wait_image}'를 기다리는 중...")
        if self.device.wait_for_image(wait_image, threshold=threshold, timeout=timeout, stop_event=stop_event):
            if stop_event and stop_event.is_set(): return False
            self.device.click_position(x, y) # Second touch before image click
            logger.debug(f"이미지 '{click_image}'를 클릭하는 중...")
            if self.device.find_and_click(click_image, threshold=threshold, timeout=5, stop_event=stop_event):
                logger.info(f"'{click_image}' 클릭 성공.")
                if stop_event and stop_event.is_set(): return False
                time.sleep(wait_time)
                return True
            else:
                logger.error(f"'{click_image}' 클릭 실패.")
                return False
        else:
            logger.error(f"'{wait_image}' 이미지를 시간 내에 찾지 못했습니다.")
            return False

    # --- Special Command Handlers ---

    def _handle_special_command(self, command, stop_event=None, **kwargs):
        """Handles special commands that require more complex logic."""
        if command == 'compare_and_branch':
            result = self.device.compare_images(kwargs['image1_name'], kwargs['image2_name'])
            if result == 1: # Success
                return True, kwargs['success_state']
            else: # Fail
                return True, kwargs['fail_state']

        elif command == 'repeat_beginner_gacha':
            for i in range(kwargs.get('count', 5)):
                if stop_event and stop_event.is_set():
                    logger.info("매크로 중지됨 (special_command).")
                    return False
                logger.info(f"초보자 뽑기 {i+1}/{kwargs.get('count', 5)}회차 진행...")
                if not self._perform_image_click('recruit_button', wait_time=2, stop_event=stop_event): return False, None
                if not self._perform_image_click('beginner_draw_10_times', wait_time=5, stop_event=stop_event): return False, None
                if not self.device.close_current_app(): return False, None
                if stop_event and stop_event.is_set(): return False, None
                time.sleep(10)
                if not self._perform_image_click('app_icon', wait_time=2, stop_event=stop_event): return False, None
                if not self._perform_image_click('title_start', wait_time=5, optional=True, stop_event=stop_event):
                    self._perform_image_click('title_start', wait_time=5, stop_event=stop_event) # Retry
            return True, None

        elif command == 'app_restart':
            self.device.close_current_app()
            if stop_event and stop_event.is_set(): return False, None
            time.sleep(5)
            self._perform_image_click('app_icon', wait_time=5, stop_event=stop_event)
            if not self._perform_image_click('title_start', wait_time=5, optional=True, stop_event=stop_event):
                 self._perform_image_click('title_start', wait_time=5, stop_event=stop_event) # Retry
            return True, None

        elif command == '__RESTART__':
            return True, '__RESTART__'

        else:
            logger.error(f"알 수 없는 특수 명령어: {command}")
            return False, None

        return True, None