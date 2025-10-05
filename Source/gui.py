import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import threading
import queue
import logging

# 로거 설정
logger = logging.getLogger('ReseMara')
logger.setLevel(logging.DEBUG)

class QueueHandler(logging.Handler):
    """로그 메시지를 queue.Queue로 보내는 핸들러"""
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))

class MacroApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- 데이터 및 상태 변수 ---
        self.macro_data = []
        self.selected_command_index = None
        self.command_widgets = []
        self.macro_thread = None
        self.stop_event = None
        self.log_queue = queue.Queue()

        # 1. 윈도우 설정
        self.title("ReseMara GUI")
        self.geometry("1200x700")

        # 2. 메인 프레임 설정
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=2)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 3. 왼쪽 프레임: 매크로 목록 및 제어
        self.left_frame = ctk.CTkFrame(self, width=400)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.left_frame.grid_propagate(False)
        self.left_frame.grid_rowconfigure(1, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.left_frame, text="매크로 명령어 목록", font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=0, padx=10, pady=10)
        self.macro_list_frame = ctk.CTkScrollableFrame(self.left_frame)
        self.macro_list_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        self.macro_control_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.macro_control_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.macro_control_frame.grid_columnconfigure((0,1,2,3,4), weight=1)
        ctk.CTkButton(self.macro_control_frame, text="Add", command=self.add_command).grid(row=0, column=0, padx=2)
        ctk.CTkButton(self.macro_control_frame, text="Modify", command=self.modify_command).grid(row=0, column=1, padx=2)
        ctk.CTkButton(self.macro_control_frame, text="Delete", command=self.delete_command).grid(row=0, column=2, padx=2)
        ctk.CTkButton(self.macro_control_frame, text="Up", command=lambda: self.move_command("up")).grid(row=0, column=3, padx=2)
        ctk.CTkButton(self.macro_control_frame, text="Down", command=lambda: self.move_command("down")).grid(row=0, column=4, padx=2)

        # 4. 중앙 프레임: 파라미터 입력
        self.center_frame = ctk.CTkFrame(self, width=400)
        self.center_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.center_frame.grid_propagate(False)
        self.center_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.center_frame, text="파라미터 설정", font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        # 위젯들...
        ctk.CTkLabel(self.center_frame, text="Command:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.command_var = ctk.StringVar(value="Image_Click")
        self.command_menu = ctk.CTkOptionMenu(self.center_frame, variable=self.command_var, values=["Image_Click", "Click_Pos", "Pos_Click_Then_Image_Click", "Input_Text", "Close_App", "Special_Command"])
        self.command_menu.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(self.center_frame, text="Image Name:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.image_name_entry = ctk.CTkEntry(self.center_frame)
        self.image_name_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(self.center_frame, text="Wait Time (s):").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.wait_time_entry = ctk.CTkEntry(self.center_frame)
        self.wait_time_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(self.center_frame, text="Position X:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.pos_x_entry = ctk.CTkEntry(self.center_frame)
        self.pos_x_entry.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(self.center_frame, text="Position Y:").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.pos_y_entry = ctk.CTkEntry(self.center_frame)
        self.pos_y_entry.grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(self.center_frame, text="Comment:").grid(row=6, column=0, padx=10, pady=5, sticky="w")
        self.comment_entry = ctk.CTkEntry(self.center_frame)
        self.comment_entry.grid(row=6, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(self.center_frame, text="Command Box", font=ctk.CTkFont(size=15, weight="bold")).grid(row=7, column=0, columnspan=2, padx=10, pady=(20, 5))
        self.command_box_frame = ctk.CTkFrame(self.center_frame, height=200)
        self.command_box_frame.grid(row=8, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.command_box_frame.pack_propagate(False)
        ctk.CTkLabel(self.command_box_frame, text="Not Implemented Yet").pack(expand=True)

        # 5. 오른쪽 프레임: 실행 및 로그
        self.right_frame = ctk.CTkFrame(self, width=350)
        self.right_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        self.right_frame.grid_propagate(False)
        self.right_frame.grid_rowconfigure(2, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.run_control_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.run_control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.run_control_frame.grid_columnconfigure((0,1), weight=1)
        self.start_button = ctk.CTkButton(self.run_control_frame, text="Start", height=40, fg_color="green", command=self.start_macro)
        self.start_button.grid(row=0, column=0, padx=5, sticky="ew")
        self.stop_button = ctk.CTkButton(self.run_control_frame, text="Stop", height=40, fg_color="red", command=self.stop_macro)
        self.stop_button.grid(row=0, column=1, padx=5, sticky="ew")
        ctk.CTkLabel(self.right_frame, text="로그", font=ctk.CTkFont(size=15, weight="bold")).grid(row=1, column=0, padx=10, pady=5)
        self.log_textbox = ctk.CTkTextbox(self.right_frame, state="disabled")
        self.log_textbox.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # 6. 메뉴바 설정
        self.menubar = tk.Menu(self)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Load", command=self.load_file)
        self.filemenu.add_command(label="Save", command=self.save_file)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.quit)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.config(menu=self.menubar)

        # 7. 로깅 설정
        self.setup_logging()
        self.process_log_queue()

    # --- 로깅 및 스레드 관리 ---
    def setup_logging(self):
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

        # 기존 핸들러 제거 (콘솔 출력 방지)
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # GUI 텍스트 박스로 로그를 보내는 핸들러
        queue_handler = QueueHandler(self.log_queue)
        queue_handler.setFormatter(formatter)
        logger.addHandler(queue_handler)

        # 파일 핸들러 (선택적)
        file_handler = logging.FileHandler('ReseMara_GUI.log', mode='w', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    def process_log_queue(self):
        try:
            while True:
                record = self.log_queue.get_nowait()
                self.log_textbox.configure(state="normal")
                self.log_textbox.insert("end", record + "\n")
                self.log_textbox.configure(state="disabled")
                self.log_textbox.see("end")
        except queue.Empty:
            pass
        self.after(100, self.process_log_queue)

    def start_macro(self):
        if self.macro_thread and self.macro_thread.is_alive():
            messagebox.showwarning("실행 중", "매크로가 이미 실행 중입니다.")
            return

        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

        self.stop_event = threading.Event()
        self.macro_thread = threading.Thread(target=self._run_macro_thread_wrapper, daemon=True)
        self.macro_thread.start()

    def stop_macro(self):
        if not self.macro_thread or not self.macro_thread.is_alive():
            messagebox.showinfo("정보", "실행 중인 매크로가 없습니다.")
            return
        logger.info("--- 중지 신호 보냄 ---")
        self.stop_event.set()

    def _run_macro_thread_wrapper(self):
        from ReseMara import ReseMara
        from macro_engine import MacroEngine

        device = None
        port_log_file = "port.log"
        try:
            logger.info("매크로 스레드 시작됨.")

            port = self._get_adb_port(port_log_file)
            if not port:
                logger.error("ADB 포트를 찾지 못해 매크로를 시작할 수 없습니다.")
                return

            device = ReseMara(port)
            logger.info(f"ADB 포트 {port}에 성공적으로 연결되었습니다.")

            # 연결 성공 시 port.log에 기록
            try:
                with open(port_log_file, 'a') as f:
                    f.write(f"{port}\n")
            except Exception as e:
                logger.error(f"포트 로그 파일 쓰기 실패: {e}")

            flow_to_run = {"GUI_Generated_Flow": self.macro_data}
            engine = MacroEngine(device, flow_to_run, self.stop_event)
            engine.run()

            if self.stop_event.is_set():
                logger.info("매크로가 사용자에 의해 중지되었습니다.")
            else:
                logger.info("매크로 실행이 완료되었습니다.")

        except Exception as e:
            logger.error(f"매크로 실행 중 심각한 오류 발생: {e}", exc_info=True)
        finally:
            if device:
                # 성공적으로 사용된 포트를 port.log에서 제거하는 로직 (선택적)
                try:
                    if os.path.exists(port_log_file):
                        with open(port_log_file, 'r') as f:
                            ports = f.readlines()

                        current_port_str = str(device.port)
                        remaining_ports = [p.strip() for p in ports if p.strip() != current_port_str]

                        with open(port_log_file, 'w') as f:
                            f.write('\n'.join(remaining_ports) + '\n')
                except Exception as e:
                    logger.error(f"포트 로그 파일 정리 중 오류 발생: {e}")

                device.close()

            logger.info("매크로 스레드 종료됨.")

    def _get_adb_port(self, port_log_file):
        from ReseMara import ReseMara

        mumu_ports = [16384, 16416, 16448, 16480, 16512, 16544, 16576]
        ports_to_try = []

        if os.path.exists(port_log_file):
            try:
                with open(port_log_file, 'r') as f:
                    used_ports = [int(p.strip()) for p in f.readlines() if p.strip()]
                    ports_to_try.extend(used_ports)
                    logger.info(f"이전 성공 포트 목록: {used_ports}")
            except Exception as e:
                logger.error(f"포트 로그 파일 읽기 실패: {e}")

        # 중복을 피하면서 mumu_ports 추가
        for port in mumu_ports:
            if port not in ports_to_try:
                ports_to_try.append(port)

        logger.info("ADB 포트 자동 검색 시작...")
        for port in ports_to_try:
            try:
                logger.debug(f"포트 {port}로 연결 테스트 중...")
                device = ReseMara(port)
                device.close()
                logger.info(f"포트 {port} 자동 연결 성공!")
                return port
            except Exception:
                logger.debug(f"포트 {port} 연결 실패.")
                continue

        logger.warning("자동으로 ADB 포트를 찾지 못했습니다. 수동 입력을 요청합니다.")
        port_input = ctk.CTkInputDialog(text="자동으로 ADB 포트를 찾지 못했습니다.\n사용할 ADB 포트를 입력하세요:", title="ADB 포트 수동 입력").get_input()
        if port_input:
            try:
                port_to_try_manually = int(port_input)
                logger.debug(f"수동으로 포트 {port_to_try_manually}에 연결 테스트 중...")
                device = ReseMara(port_to_try_manually)
                device.close()
                logger.info(f"포트 {port_to_try_manually} 수동 연결 성공!")
                return port_to_try_manually
            except (ValueError, TypeError):
                logger.error("유효하지 않은 포트 번호입니다.")
                return None
            except Exception as e:
                logger.error(f"수동 포트 연결 실패: {e}")
                return None
        return None

    # --- 파일 및 명령어 관리 기능 (이전과 동일) ---
    def refresh_macro_list(self):
        for widget in self.command_widgets: widget.destroy()
        self.command_widgets.clear()
        self.selected_command_index = None
        for i, command_data in enumerate(self.macro_data):
            action, comment = command_data.get('action', 'N/A'), command_data.get('comment', '')
            frame = ctk.CTkFrame(self.macro_list_frame, border_width=1, border_color="gray")
            frame.pack(fill="x", padx=5, pady=2)
            label = ctk.CTkLabel(frame, text=f"{i+1}. {action}: {comment}", anchor="w")
            label.pack(fill="x", padx=5, pady=5)
            frame.bind("<Button-1>", lambda e, index=i: self.select_command(index))
            label.bind("<Button-1>", lambda e, index=i: self.select_command(index))
            self.command_widgets.append(frame)
        self.update_selection_highlight()

    def select_command(self, index):
        self.selected_command_index = index
        self.update_selection_highlight()
        self.populate_params_from_selection()

    def update_selection_highlight(self):
        for i, frame in enumerate(self.command_widgets):
            frame.configure(fg_color=ctk.ThemeManager.theme["CTkButton" if i == self.selected_command_index else "CTkFrame"]["hover_color" if i == self.selected_command_index else "fg_color"])

    def populate_params_from_selection(self):
        if self.selected_command_index is None: return
        command_data = self.macro_data[self.selected_command_index]
        params = command_data.get('params', {})
        self.command_var.set(command_data.get('action', ''))
        self.image_name_entry.delete(0, 'end'); self.image_name_entry.insert(0, params.get('wait_image', ''))
        self.wait_time_entry.delete(0, 'end'); self.wait_time_entry.insert(0, str(params.get('wait_time', '')))
        self.pos_x_entry.delete(0, 'end'); self.pos_x_entry.insert(0, str(params.get('x', '')))
        self.pos_y_entry.delete(0, 'end'); self.pos_y_entry.insert(0, str(params.get('y', '')))
        self.comment_entry.delete(0, 'end'); self.comment_entry.insert(0, command_data.get('comment', ''))

    def gather_params_to_dict(self):
        params = {}
        if self.image_name_entry.get(): params['wait_image'] = self.image_name_entry.get()
        if self.wait_time_entry.get(): params['wait_time'] = int(self.wait_time_entry.get())
        if self.pos_x_entry.get(): params['x'] = int(self.pos_x_entry.get())
        if self.pos_y_entry.get(): params['y'] = int(self.pos_y_entry.get())
        return {'action': self.command_var.get(), 'params': params, 'comment': self.comment_entry.get()}

    def add_command(self):
        self.macro_data.append(self.gather_params_to_dict())
        self.refresh_macro_list()

    def modify_command(self):
        if self.selected_command_index is None: return messagebox.showwarning("Warning", "수정할 명령어를 먼저 선택하세요.")
        self.macro_data[self.selected_command_index] = self.gather_params_to_dict()
        self.refresh_macro_list()
        self.select_command(self.selected_command_index)

    def delete_command(self):
        if self.selected_command_index is None: return messagebox.showwarning("Warning", "삭제할 명령어를 먼저 선택하세요.")
        del self.macro_data[self.selected_command_index]
        self.refresh_macro_list()

    def move_command(self, direction):
        if self.selected_command_index is None: return messagebox.showwarning("Warning", "이동할 명령어를 먼저 선택하세요.")
        idx, new_idx = self.selected_command_index, self.selected_command_index + (-1 if direction == "up" else 1)
        if 0 <= new_idx < len(self.macro_data):
            self.macro_data[idx], self.macro_data[new_idx] = self.macro_data[new_idx], self.macro_data[idx]
            self.refresh_macro_list()
            self.select_command(new_idx)

    def load_file(self):
        filepath = filedialog.askopenfilename(title="Load Macro File", filetypes=(("JSON files", "*.json"), ("All files", "*.*")), initialdir=os.getcwd())
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8') as f: full_data = json.load(f)
            self.macro_data = []; [self.macro_data.extend(actions) for actions in full_data.values()]
            self.refresh_macro_list()
            messagebox.showinfo("Success", f"'{os.path.basename(filepath)}' 파일을 성공적으로 불러왔습니다.")
        except Exception as e: messagebox.showerror("Error", f"파일을 불러오는 중 오류 발생: {e}")

    def save_file(self):
        filepath = filedialog.asksaveasfilename(title="Save Macro File", filetypes=(("JSON files", "*.json"),), initialdir=os.getcwd(), defaultextension=".json")
        if not filepath: return
        try:
            save_data = {"GUI_Generated_Flow": self.macro_data}
            with open(filepath, 'w', encoding='utf-8') as f: json.dump(save_data, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Success", f"파일이 '{filepath}'에 성공적으로 저장되었습니다.")
        except Exception as e: messagebox.showerror("Error", f"파일을 저장하는 중 오류 발생: {e}")

if __name__ == "__main__":
    # 콘솔 버전의 ReseMara.py를 직접 실행하지 않도록 __main__ 블록 제거
    # 대신 이 gui.py를 메인 실행 파일로 사용
    app = MacroApp()
    app.mainloop()