import os
import subprocess

import chromedriver_autoinstaller
from chromedriver_py import binary_path
from common.util import logger


class VersionManager:
    def __init__(self):
        self.standard_path = binary_path
        self.chromedriver_version = self.get_chromedriver_version()
        self.start()
        self.get_executable_path()

    def get_installed_chrome_version(self):
        try:
            installed_version_bytes = subprocess.check_output(["google-chrome", "--version"])
            installed_version = installed_version_bytes.decode("UTF-8").split()[-1]
            return installed_version
        except Exception as e:
            logger.debug("Chrome not installed...installing...")
            return False

    def get_chromedriver_version(self):
        try:
            cmd = [self.standard_path, "--version"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout.split()[1]
        except IndexError:
            logger.info("No ChromeDriver version found")
            return False

    def start(self):
        if not self.chromedriver_version:
            chromedriver_autoinstaller.install()
            return self.get_executable_path()
        installed_chrome_version = self.get_installed_chrome_version()
        if not installed_chrome_version:
            self.install_chrome(self.chromedriver_version)
        elif installed_chrome_version != self.chromedriver_version:
            self.install_chrome(self.chromedriver_version)
        else:
            logger.info("Chrome is up to date")

        return self.get_executable_path()

    def install_chrome(self, version):
        if os.geteuid() != 0:
            logger.info("Insufficient rights")
        try:
            chrome_download_url = f"https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/google-chrome-stable_{version}-1_amd64.deb"  # https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.90-1_amd64.deb
            chrome_installer_path = f"google-chrome-stable_{version}-1_amd64.deb"
            # subprocess.run(["apt", "--fix-broken", "install", "-f"], check=True)  # sudo apt --fix-broken install
            subprocess.run(["dpkg", "--configure", "--force-overwrite", "-a"], check=True)
            subprocess.run(["dpkg", "-i", chrome_installer_path], check=True)
            # subprocess.run(["apt-mark", "hold", "google-chrome-stable"], check=True)
        except subprocess.CalledProcessError as e:
            logger.info(f"Operation failed with error code: {e.returncode}...trying latest version")
            chrome_download_url = "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"  # https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.90-1_amd64.deb
            subprocess.run(["wget", chrome_download_url], check=True)  # sudo apt --fix-broken install
            subprocess.run(["dpkg", "-i", "google-chrome-stable_current_amd64.deb"], check=True)
            subprocess.run(["apt-get", "install", "-f"], check=True)

    def get_executable_path(self):  # /snap/bin/chromium.chromedriver
        return self.standard_path
        # return ChromeDriverManager().install()  # TODO check where UC is installing the driver to
