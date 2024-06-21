from __future__ import annotations

__version__ = "3.5.4"

import logging

import selenium.webdriver.chrome.service
import selenium.webdriver.chrome.webdriver
import selenium.webdriver.chromium.service
import selenium.webdriver.remote.command
import selenium.webdriver.remote.webdriver

# from .cdp import CDP
# from .options import ChromeOptions
# from .patcher import Patcher
# from .reactor import Reactor

__all__ = (
    "Chrome",
    "ChromeOptions",
    "Patcher",
    "Reactor",
    "CDP",
    "find_chrome_executable",
)

logger = logging.getLogger("uc")
logger.setLevel(logging.getLogger().getEffectiveLevel())


class Chrome(selenium.webdriver.chrome.webdriver.WebDriver):

    session_id = None

    def __init__(
        self,
        options=None,
        driver_executable_path=None,
        port2=0,
        desired_capabilities=None,
        keep_alive=True,
        start_chrome=True,
        session_id=None,
    ):

        self.start_chrome = start_chrome
        self.session_id = session_id

        self.options = options

        if not desired_capabilities:
            desired_capabilities = options.to_capabilities()

        if not self.start_chrome:
            service = selenium.webdriver.chromium.service.ChromiumService(executable_path=driver_executable_path, port=port2)

            super(Chrome, self).__init__(
                service=service,
                options=options,
                keep_alive=keep_alive,
            )

            return
