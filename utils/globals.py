import time

from utils.auth_handler import Auth


args = None
auth:Auth = None

script_time_seconds: float = time.time()
script_time_milli_seconds: int = int(script_time_seconds*1000)
script_date: str = time.strftime("%m/%d/%Y", time.localtime(script_time_seconds))
script_time: str = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(script_time_seconds))
