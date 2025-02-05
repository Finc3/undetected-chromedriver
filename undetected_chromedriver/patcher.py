import os
import pathlib
import shutil
import zipfile
from uuid import uuid4
import random
import string
import sys
import time
import io
import json
import re
from urllib.request import urlopen, urlretrieve
from multiprocessing import Lock
from distutils.version import LooseVersion
import logging

logger = logging.getLogger(__name__)

IS_POSIX = sys.platform.startswith(("darwin", "cygwin", "linux", "linux2"))

_BASE_DRIVER_PATH = os.path.join(str(pathlib.Path(__name__).parent.resolve()), ".ucdriver")
DRIVER_PATH = os.path.join(_BASE_DRIVER_PATH, "base_driver")
INSTANCE_DRIVERS = os.path.join(_BASE_DRIVER_PATH, "instances")
os.makedirs(_BASE_DRIVER_PATH, exist_ok=True)
os.makedirs(INSTANCE_DRIVERS, exist_ok=True, mode=0o755)

class Patcher(object):
    lock = Lock()
    exe_name = "chromedriver%s"

    platform = sys.platform
    if platform.endswith("win32"):
        d = "~/appdata/roaming/undetected_chromedriver"
    elif "LAMBDA_TASK_ROOT" in os.environ:
        d = "/tmp/undetected_chromedriver"
    elif platform.startswith(("linux", "linux2")):
        d = "~/.local/share/undetected_chromedriver"
    elif platform.endswith("darwin"):
        d = "~/Library/Application Support/undetected_chromedriver"
    else:
        d = "~/.undetected_chromedriver"
    data_path = os.path.abspath(os.path.expanduser(d))

    def __init__(
        self,
        executable_path=None,
        force=False,
        version_main: int = 0,
        user_multi_procs=False,
    ):
        """
        Args:
            executable_path: None = automatic
                             a full file path to the chromedriver executable
            force: False
                    terminate processes which are holding lock
            version_main: 0 = auto
                specify main chrome version (rounded, ex: 82)
        """
        self.force = force
        self._custom_exe_path = False
        prefix = "undetected"
        self.user_multi_procs = user_multi_procs

        self.is_old_chromedriver = version_main and version_main <= 114
        # Needs to be called before self.exe_name is accessed
        self._set_platform_name()

        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path, exist_ok=True)

        if not executable_path:
            self.executable_path = os.path.join(
                self.data_path, "_".join([prefix, self.exe_name])
            )

        if not IS_POSIX:
            if executable_path:
                if not executable_path[-4:] == ".exe":
                    executable_path += ".exe"

        self.zip_path = os.path.join(self.data_path, prefix)

        if not executable_path:
            if not self.user_multi_procs:
                self.executable_path = os.path.abspath(
                    os.path.join(".", self.executable_path)
                )

        if executable_path:
            self._custom_exe_path = True
            self.executable_path = executable_path

        # Set the correct repository to download the Chromedriver from
        if self.is_old_chromedriver:
            self.url_repo = "https://chromedriver.storage.googleapis.com"
        else:
            self.url_repo = "https://googlechromelabs.github.io/chrome-for-testing"

        self.version_main = version_main
        self.version_full = None

    def _set_platform_name(self):
        """
        Set the platform and exe name based on the platform undetected_chromedriver is running on
        in order to download the correct chromedriver.
        """
        if self.platform.endswith("win32"):
            self.platform_name = "win32"
            self.exe_name %= ".exe"
        if self.platform.endswith(("linux", "linux2")):
            self.platform_name = "linux64"
            self.exe_name %= ""
        if self.platform.endswith("darwin"):
            if self.is_old_chromedriver:
                self.platform_name = "mac64"
            else:
                self.platform_name = "mac-x64"
            self.exe_name %= ""

    def auto(self, executable_path=None, force=False, version_main=None, _=None):
        """
        Automatically downloads and patches chromedriver.
        """
        p = pathlib.Path(self.data_path)

        if self.user_multi_procs:
            with Lock():
                files = list(p.rglob("*chromedriver*"))
                most_recent = max(files, key=lambda f: f.stat().st_mtime)
                files.remove(most_recent)
                list(map(lambda f: f.unlink(), files))
                if self.is_binary_patched(most_recent):
                    self.executable_path = str(most_recent)
                    return True

        if executable_path:
            self.executable_path = executable_path
            self._custom_exe_path = True

        if self._custom_exe_path:
            ispatched = self.is_binary_patched(self.executable_path)
            if not ispatched:
                return self.patch_exe()
            else:
                return

        if version_main:
            self.version_main = version_main
        if force is True:
            self.force = force

        try:
            os.unlink(self.executable_path)
        except PermissionError:
            if self.force:
                self.force_kill_instances(self.executable_path)
                return self.auto(force=not self.force)
            try:
                if self.is_binary_patched():
                    # assumes already running AND patched
                    return True
            except PermissionError:
                pass
        except FileNotFoundError:
            pass

        release = self.fetch_release_number()
        self.version_main = release.version[0]
        self.version_full = release
        # self.unzip_package(self.fetch_package())
        self.cached_package()
        return self.patch()


    def driver_binary_in_use(self, path: str = None) -> bool:
        """
        Check if chromedriver binary is in use.
        """
        if not path:
            path = self.executable_path
        p = pathlib.Path(path)

        if not p.exists():
            raise OSError("file does not exist: %s" % p)
        try:
            with open(p, mode="a+b") as fs:
                exc = []
                try:
                    fs.seek(0, 0)
                except PermissionError as e:
                    exc.append(e)
                try:
                    fs.readline()
                except PermissionError as e:
                    exc.append(e)

                if exc:
                    return True
                return False
        except Exception as e:
            pass

    def cleanup_unused_files(self):
        p = pathlib.Path(self.data_path)
        items = list(p.glob("*undetected*"))
        for item in items:
            try:
                item.unlink()
            except:
                pass

    def patch(self):
        self.patch_exe()
        return self.is_binary_patched()

    def fetch_release_number(self):
        """
        Gets the latest major version available.
        """
        if self.is_old_chromedriver:
            path = f"/latest_release_{self.version_main}"
            path = path.upper()
            logger.debug("getting release number from %s" % path)
            return LooseVersion(urlopen(self.url_repo + path).read().decode())

        if not self.version_main:
            path = "/last-known-good-versions-with-downloads.json"
            logger.debug("getting release number from %s" % path)
            with urlopen(self.url_repo + path) as conn:
                response = conn.read().decode()

            last_versions = json.loads(response)
            return LooseVersion(last_versions["channels"]["Stable"]["version"])

        path = "/latest-versions-per-milestone-with-downloads.json"
        logger.debug("getting release number from %s" % path)
        with urlopen(self.url_repo + path) as conn:
            response = conn.read().decode()

        major_versions = json.loads(response)
        return LooseVersion(major_versions["milestones"][str(self.version_main)]["version"])

    def parse_exe_version(self):
        with io.open(self.executable_path, "rb") as f:
            for line in iter(lambda: f.readline(), b""):
                match = re.search(rb"platform_handle\x00content\x00([0-9.]*)", line)
                if match:
                    return LooseVersion(match[1].decode())

    def fetch_package(self):
        """
        Downloads ChromeDriver from source.
        """
        zip_name = f"chromedriver_{self.platform_name}.zip"
        if self.is_old_chromedriver:
            download_url = "%s/%s/%s" % (self.url_repo, self.version_full.vstring, zip_name)
        else:
            zip_name = zip_name.replace("_", "-", 1)
            download_url = "https://storage.googleapis.com/chrome-for-testing-public/%s/%s/%s"
            download_url %= (self.version_full.vstring, self.platform_name, zip_name)

        logger.debug("downloading from %s" % download_url)
        return urlretrieve(download_url)[0]

    @staticmethod
    def force_kill_instances(exe_name):
        """
        Kills running instances of the executable.
        """
        exe_name = os.path.basename(exe_name)
        if IS_POSIX:
            r = os.system("kill -f -9 $(pidof %s)" % exe_name)
        else:
            r = os.system("taskkill /f /im %s" % exe_name)
        return not r

    @staticmethod
    def gen_random_cdc():
        cdc = random.choices(string.ascii_letters, k=27)
        return "".join(cdc).encode()

    def is_binary_patched(self, executable_path=None):
        """
        Checks if the chromedriver binary has been patched.
        """
        executable_path = executable_path or self.executable_path
        try:
            with io.open(executable_path, "rb") as fh:
                return fh.read().find(b"undetected chromedriver") != -1
        except FileNotFoundError:
            return False

    def patch_exe(self):
        start = time.perf_counter()
        logger.info("patching driver executable %s" % self.executable_path)
        with io.open(self.executable_path, "r+b") as fh:
            content = fh.read()
            match_injected_codeblock = re.search(rb"\{window\.cdc.*?;\}", content)
            if match_injected_codeblock:
                target_bytes = match_injected_codeblock[0]
                new_target_bytes = (
                    b'{console.log("undetected chromedriver 1337!")}'.ljust(
                        len(target_bytes), b" "
                    )
                )
                new_content = content.replace(target_bytes, new_target_bytes)
                if new_content == content:
                    logger.warning(
                        "something went wrong patching the driver binary. could not find injection code block"
                    )
                else:
                    logger.debug(
                        "found block:\n%s\nreplacing with:\n%s"
                        % (target_bytes, new_target_bytes)
                    )
                fh.seek(0)
                fh.write(new_content)
        logger.debug(
            "patching took us {:.2f} seconds".format(time.perf_counter() - start)
        )

    def cached_package(self):
        if not os.path.exists(DRIVER_PATH):
            path = self.fetch_package()
            shutil.copy2(path, DRIVER_PATH + ".zip")
            os.remove(path)
            self.unzip_package_main()
        instance_id = uuid4().hex
        self.executable_path = os.path.join(INSTANCE_DRIVERS, instance_id)
        shutil.copyfile(DRIVER_PATH, os.path.join(INSTANCE_DRIVERS, self.executable_path))
        os.chmod(self.executable_path, 0o755)
        return DRIVER_PATH

    def unzip_package_main(self):
        with zipfile.ZipFile(DRIVER_PATH + ".zip", mode="r") as zf:
            for f in zf.namelist():
                if f.split("/")[1] == "chromedriver":
                    with zf.open(f) as fs, open(DRIVER_PATH, "wb") as ft:
                        shutil.copyfileobj(fs, ft)
                    break
        os.unlink(DRIVER_PATH + ".zip")

    def __repr__(self):
        return "{0:s}({1:s})".format(
            self.__class__.__name__,
            self.executable_path,
        )

    def __del__(self):
        if self._custom_exe_path:
            return
        else:
            timeout = 3
            t = time.monotonic()
            now = lambda: time.monotonic()
            while now() - t > timeout:
                # we don't want to wait until the end of time
                try:
                    if self.user_multi_procs:
                        break
                    os.unlink(self.executable_path)
                    logger.debug("successfully unlinked %s" % self.executable_path)
                    break
                except (OSError, RuntimeError, PermissionError):
                    time.sleep(0.01)
                    continue
                except FileNotFoundError:
                    break
