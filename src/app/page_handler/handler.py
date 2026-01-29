import time
from typing import Optional

from seleniumbase import SB

from app.page_handler.data_parser.parser import PageParser
from app.page_handler.models import PageInfo


class MetalArchivesPageHandler:
    _instance: Optional["MetalArchivesPageHandler"] = None

    def __new__(cls, *args, **kwargs) -> "MetalArchivesPageHandler":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._parser_cls = PageParser

    def get_band_info(self, url: str) -> PageInfo:
        data = self._get_page(url)
        if data.html is not None:
            data.data = self._parser_cls.extract_band_info(data=data.html)
        return data
    
    def search_band_info(self, url: str) -> PageInfo:
        data = self._get_page(url)
        if data.html is not None:
            data.data = self._parser_cls.extract_search_info(data=data.html)
        return data
    
    def get_album_info(self, url: str) -> PageInfo:
        data = self._get_page(url)
        if data.html is not None:
            data.data = self._parser_cls.extract_album_info(data=data.html)
        return data

    @staticmethod
    def _get_data(
        sb: SB,
        url: str,
        start_time: float,
        wait_time: int = 3,
        save_screenshot: bool = False
    ) -> PageInfo:
        try:
            print(f"Открываю {url} ...")
            sb.uc_open_with_reconnect(url, reconnect_time=4)
            # sb.uc_gui_click_captcha()
            # time.sleep(wait_time)
            # sb.assert_element("body", timeout=10)

            # Получаем HTML и извлекаем информацию
            return PageInfo(
                url=url,
                processing_time=round(time.time() - start_time, 2),
                html=sb.get_page_source(),
            )

        except Exception as err:
            error_msg = f"Ошибка при парсинге: {str(err)}"
            if save_screenshot:
                try:
                    screenshot_name = f"error_{int(time.time())}.png"
                    sb.save_screenshot(screenshot_name)
                    error_msg += f" (скриншот сохранен как {screenshot_name})"
                except:
                    pass

            return PageInfo(
                url=url,
                processing_time=round(time.time() - start_time, 2),
                error=error_msg,
            )

    def _get_page(
        self,
        url: str,
        wait_time: int = 3,
        save_screenshot: bool = False
    ) -> PageInfo:
        start_time = time.time()
        try:
            with SB(uc=True, incognito=True, locale="en") as sb:
                return self._get_data(sb, url, start_time, wait_time, save_screenshot)
        except Exception as err:
            return PageInfo(
                url=url,
                processing_time=round(time.time() - start_time, 2),
                error=f"Ошибка при инициализации SeleniumBase: {str(err)}",
            )

