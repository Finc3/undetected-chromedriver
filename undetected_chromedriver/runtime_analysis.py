import subprocess
import time

import psutil
from common.util import logger


class Analysis:
    def main_logger(self, message):
        chromedriver_processes = self.count_chromedriver_processes()
        used_memory, total_memory = self.get_memory_usage()
        mongo_processes = self.count_mongo_processes()
        count_files = self.count_open_files()
        count_processes = self.count_processes()
        log = f"{message} | count of Chrome processes: {chromedriver_processes} | count of MongoDB processes: {mongo_processes} | count of processes: {count_processes} | count of open files: {count_files} | {used_memory}GB out of {total_memory}GB are being used"
        logger.info(log)
        return self.return_logging_file(log)

    def count_chromedriver_processes(self):
        count = 0
        time.sleep(1)
        for process in psutil.process_iter(attrs=["name"]):
            try:
                process_info = process.info
                if process_info["name"] == "chrome" or process_info["name"] == "chromedriver":
                    count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return count

    def count_mongo_processes(self):
        count = 0
        time.sleep(1)
        for process in psutil.process_iter(attrs=["name"]):
            try:
                process_info = process.info
                if process_info["name"] == "mongo" or process_info["name"] == "mongodb" or process_info["name"] == "mongod":
                    count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return count

    def count_processes(self):
        process_output = subprocess.check_output("lsof", shell=True).decode()
        count = len(process_output.splitlines()) - 1  # Subtracted bc of header line
        return count

    def count_open_files(self):
        try:
            files_output = subprocess.check_output("lsof", shell=True).decode()
            count = len(files_output.splitlines())
            return count
        except Exception:
            return 0

    def get_memory_usage(self):
        memory = psutil.virtual_memory()
        total_memory = round(memory.total / (1024**3), 2)  # Raised to the power of three to convert bytes into GB
        used_memory = round(memory.used / (1024**3), 2)
        return used_memory, total_memory

    def return_logging_file(self, log):
        with open("logger_file.txt", mode="a") as f:
            f.write(log + "\n")
