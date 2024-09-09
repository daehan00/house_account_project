import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import os

class ChangeHandler(FileSystemEventHandler):
    """파일 시스템 변경 이벤트를 처리하는 핸들러"""
    def __init__(self, command):
        self.command = command

    def start_server(self):
        """서버 최초 시작"""
        self.process = subprocess.Popen(self.command, shell=True)
        print("Server started initially.")

    def on_any_event(self, event):
        if event.is_directory:
            return
        if event.event_type in ['modified', 'created']:
            print(f'{event.src_path} has been changed. Restarting the server...')
            self.restart_server()

    def restart_server(self):
        """Flask 서버 재시작"""
        try:
            # 현재 실행 중인 Flask 서버 프로세스 종료
            if hasattr(self, 'process') and self.process.poll() is None:
                self.process.kill()
                self.process.wait()
            # 새로운 서버 프로세스 시작
            self.process = subprocess.Popen(self.command, shell=True)
        except Exception as e:
            print(f"Failed to restart the server: {e}")

def start_watcher(path, command):
    """디렉토리 감시 시작"""
    event_handler = ChangeHandler(command=command)
    event_handler.start_server()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print("Starting observer...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    # 감시할 디렉토리와 Flask 실행 명령
    watch_path = os.path.abspath('.')
    cmd = 'flask run --host=0.0.0.0 --port=8088'
    start_watcher(watch_path, cmd)