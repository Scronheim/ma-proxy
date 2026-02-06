import time
from typing import Optional

from seleniumbase import SB

from app.page_handler.data_parser.models import AlbumShortInformation
from app.page_handler.data_parser.parser import PageParser
from app.page_handler.models import PageInfo


class MetalArchivesPageHandler:
    _instance: Optional["MetalArchivesPageHandler"] = None

    def __new__(cls, sb: SB, *args, **kwargs) -> "MetalArchivesPageHandler":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, sb: SB):
        self._parser_cls = PageParser
        self._sb = sb

    def get_band_info(self, url: str) -> PageInfo:
        data = self._get_data(url)
        if data.html is not None:
            band_info = self._parser_cls.extract_band_info(data=data.html)
            band_info.discography = self._get_band_discography(band_id=band_info.id)
            data.data = band_info
        return data

    def search_band_info(self, url: str) -> PageInfo:
        data = self._get_data(url)
        if data.html is not None:
            data.data = self._parser_cls.extract_search_band_info(data=data.html)
        return data

    def search_album_info(self, url: str) -> PageInfo:
        data = self._get_data(url)
        if data.html is not None:
            data.data = self._parser_cls.extract_search_album_info(data=data.html)
        return data

    def get_album_info(self, url: str) -> PageInfo:
        data = self._get_data(url)
        if data.html is not None:
            data.data = self._parser_cls.extract_album_info(data=data.html)
        return data
    
    def get_lyrics(self, url: str) -> PageInfo:
        data = self._get_data(url)
        if data.html is not None:
            data.data = self._parser_cls.extract_lyrics_info(data=data.html)
        return data

    def _get_data(
        self,
        url: str,
        wait_time: int = 3,
        save_screenshot: bool = True
    ) -> PageInfo:
        start_time = time.time()
        try:
            self._sb.uc_open_with_tab(url)
            # self._sb.uc_gui_click_captcha()
            # self._sb.uc_gui_click_cf()
            # time.sleep(wait_time)
            # Получаем HTML и извлекаем информацию
            return PageInfo(
                url=url,
                processing_time=round(time.time() - start_time, 2),
                html=self._sb.get_page_source(),
            )

        except Exception as err:
            error_msg = f"Ошибка при парсинге: {str(err)}"
            if save_screenshot:
                try:
                    screenshot_name = f"error_{int(time.time())}.png"
                    self._sb.save_screenshot(screenshot_name)
                    error_msg += f" (скриншот сохранен как {screenshot_name})"
                except:
                    pass

            return PageInfo(
                url=url,
                processing_time=round(time.time() - start_time, 2),
                error=error_msg,
            )

    def _get_band_discography(self, band_id: str | int) -> list[AlbumShortInformation]:
        url = f'https://www.metal-archives.com/band/discography/id/{band_id}/tab/all'
        data = self._get_data(url=url)
        if data.html is not None:
            return self._parser_cls.extract_discography_info(data=data.html)
        return []
