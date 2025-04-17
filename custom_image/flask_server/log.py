import os
import logging

from logging.handlers import RotatingFileHandler

class SystemLogger:
    def __init__(self, app:str): # app => 앱 이름(app/api)
        # 로그 디렉토리 생성
        if not os.path.exists('logs'):
            os.mkdir('logs')

        self.EXCLUDED_PATHS = ['/static', '/health']
        # 포맷 지정
        self.formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s'
        )
        self.logger = logging.getLogger('app')
        self.set_file_handler(app+".log")
        self.add_handler()

    def set_file_handler(self, filename):
        # 파일 핸들러: info 이상 로그 저장
        self.file_handler = RotatingFileHandler(f'logs/{filename}', maxBytes=1_000_000, backupCount=5)
        self.file_handler.setLevel(logging.INFO)
        self.file_handler.setFormatter(self.formatter)

        # 콘솔 핸들러: warning 이상만 출력
        self.stream_handler = logging.StreamHandler()
        self.stream_handler.setLevel(logging.WARNING)
        self.stream_handler.setFormatter(self.formatter)

    def add_handler(self):
        # 로거 설정
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.stream_handler)
    
    def is_excluded_path(self, path:str):
        return any(
            path == excluded or path.startswith(excluded + '/')
            for excluded in self.EXCLUDED_PATHS
        )

    def log(self, request, response=None):
        path = request.path

        # 제외 경로면 아무 로그도 남기지 않음
        if self.is_excluded_path(path):
            return response

        if response:
            status_code = response.status_code
            log_msg = f"[{request.method}] {path} → {status_code}"

            if status_code >= 500:
                self.logger.error(log_msg)
            elif status_code >= 400:
                self.logger.warning(log_msg)
            else:
                self.logger.info(log_msg)
        else:
            self.logger.info(f"[{request.method}] {request.path} 요청 수신 (IP: {request.remote_addr})")
        
        return response