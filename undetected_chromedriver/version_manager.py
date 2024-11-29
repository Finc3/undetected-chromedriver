import os
import pathlib
import subprocess
import time

<<<<<<< HEAD
from common.util import logger
=======
>>>>>>> 0fb2ce5303a63c5f4f2374566f2160b26aba4103


class VersionManager:
    def __init__(self):
        self.standard_path = os.path.join(str(pathlib.Path(__name__).parent.resolve()))
        self.instances_path = f"{self.standard_path}/.ucdriver/instances"
        self.purge_redundant_drivers()
        self.version_file_path = self.version_file()
        self.chromedriver_version = self.get_chromedriver_version()

    def purge_redundant_drivers(self):
        files = os.listdir(self.instances_path)
        for _file in files:
            os.remove(f"{self.instances_path}/{_file}")

    def version_file(self):
        path = os.path.join(str(pathlib.Path(__name__).parent.resolve()))
        chromedriver_version = self.get_chromedriver_version()
        if not chromedriver_version:
            return
        version_file_path = f"{path}/.ucdriver/version.txt"
        version_exists = os.path.exists(version_file_path)

        if not version_exists:
            os.makedirs(os.path.dirname(version_file_path), exist_ok=True)
            with open(version_file_path, "w") as f:
                version = chromedriver_version
                f.write(version)
                return version
        else:
            with open(version_file_path, "r") as f:
                version = f.read()
                return version

    def get_installed_chrome_version(self):
        try:
<<<<<<< HEAD
            installed_version_bytes = subprocess.check_output(["google-chrome", "--version"])
            installed_version = installed_version_bytes.decode("UTF-8").split()[-1]
            return installed_version
        except Exception as e:
            logger.debug("Chrome not installed...installing...")
=======
            if os.getenv("USE_MAC_QUEUE") == "true":
                installed_version_bytes = subprocess.check_output(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome","--version"])
            else:
                installed_version_bytes = subprocess.check_output(["google-chrome", "--version"])
            installed_version = installed_version_bytes.decode("UTF-8").split()[-1]
            return installed_version
        except Exception as e:
>>>>>>> 0fb2ce5303a63c5f4f2374566f2160b26aba4103
            return False

    def get_chromedriver_version(self):
        try:
            files = os.listdir(self.instances_path)
            files.sort()
            if files:
                first_instance = files[0]
                cmd = [os.path.join(self.instances_path, first_instance), "--version"]
                self.standard_path = os.path.join(self.instances_path, first_instance)
                result = subprocess.run(cmd, capture_output=True, text=True)
                return result.stdout.split()[1]
            return False
        except (IndexError, PermissionError, FileNotFoundError):
<<<<<<< HEAD
            logger.info("No ChromeDriver version found")
=======
>>>>>>> 0fb2ce5303a63c5f4f2374566f2160b26aba4103
            return False

    def start(self):
        installed_chrome_version = self.get_installed_chrome_version()
        if not installed_chrome_version and not self.chromedriver_version:
            print("No Chrome installed or ChromeDriver version found")
            self.install_chrome(version=None)
        elif not installed_chrome_version and self.chromedriver_version:
            print("No Chrome installed")
            self.install_chrome(self.chromedriver_version)
        elif self.chromedriver_version and installed_chrome_version != self.chromedriver_version:
            print("Chrome is not up to date")
            self.install_chrome(self.chromedriver_version)
        else:
<<<<<<< HEAD
            logger.info("Chrome is up to date")
=======
            pass
>>>>>>> 0fb2ce5303a63c5f4f2374566f2160b26aba4103
        path = self.get_executable_path()
        return path

    def install_chrome(self, version):
<<<<<<< HEAD
        if os.geteuid() != 0:
            logger.info("Insufficient rights")
        try:
            if version:
                chrome_download_url = f"https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/google-chrome-stable_{version}-1_amd64.deb"  # https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.90-1_amd64.deb
                chrome_installer_path = f"google-chrome-stable_{version}-1_amd64.deb"
                subprocess.run(["apt", "install", "-y", f"./{chrome_installer_path}"], check=True)
            else:
                chrome_download_url = "https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/google-chrome-stable_122.0.6261.128-1_amd64.deb"  #Just a test
                subprocess.run(["wget", chrome_download_url], check=True)
                result = subprocess.run(["apt", "install", "-y", "./google-chrome-stable_122.0.6261.128-1_amd64.deb"], check=True)
=======
        try:
            if os.getenv("USE_MAC_QUEUE") == "true":
                result = subprocess.run(["brew", "install", "--cask", "google-chrome"], check=True)
            else:
                chrome_download_url = "https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/google-chrome-stable_127.0.6533.72-1_amd64.deb"
                subprocess.run(["wget", chrome_download_url])
                subprocess.run(["dpkg", "--configure", "-a"])
                result = subprocess.run(["apt", "install", "-y", "./google-chrome-stable_127.0.6533.72-1_amd64.deb"])
                os.remove("google-chrome-stable_127.0.6533.72-1_amd64.deb")
>>>>>>> 0fb2ce5303a63c5f4f2374566f2160b26aba4103
        except subprocess.CalledProcessError as e:
            raise e

        if self.confirm_installation(result):
            return True

    def confirm_installation(self, result):
        while True:
            try:
                time.sleep(1)
                if result.returncode == 0:
                    return True
            except subprocess.CalledProcessError:
<<<<<<< HEAD
                logger.info("Chrome not installed yet")
=======
>>>>>>> 0fb2ce5303a63c5f4f2374566f2160b26aba4103
                continue

    def get_executable_path(self):
        return self.instances_path
