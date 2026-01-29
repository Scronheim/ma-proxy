"""
FastAPI приложение для парсинга Metal Archives с использованием SeleniumBase в UC-режиме.
Требуется установка: pip install fastapi seleniumbase pyautogui uvicorn beautifulsoup4
"""

import re
import time
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup
from fastapi import FastAPI
from pydantic import BaseModel
from seleniumbase import SB

app = FastAPI(
    title="Metal Archives Parser API",
    description="API для парсинга страниц Metal Archives с обходом Cloudflare",
    version="1.0.0"
)


class ParseRequest(BaseModel):
    """Модель запроса для парсинга"""
    url: Optional[str] = "https://www.metal-archives.com/band/random"
    wait_time: Optional[int] = 3
    save_screenshot: Optional[bool] = False


class BandInfoResponse(BaseModel):
    """Модель ответа с информацией о группе"""
    success: bool
    band_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    url: Optional[str] = None
    processing_time: Optional[float] = None

class AlbumInfoResponse(BaseModel):
    """Модель ответа с информацией об альбоме"""
    success: bool
    album_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    url: Optional[str] = None
    processing_time: Optional[float] = None


def extract_band_info(html: str) -> Dict[str, Any]:
    """
    Извлекает информацию о группе из HTML страницы.
    
    Args:
        html: HTML страницы для парсинга
    
    Returns:
        Словарь с информацией о группе
    """
    soup = BeautifulSoup(html, 'html.page_handler')
    band_info = {}
    
    try:
        # Основное название группы
        band_name_elem = soup.find('h1', class_='band_name')
        if band_name_elem:
            band_info['name'] = band_name_elem.text.strip()
        
        # Страна и местоположение
        band_info['location'] = {}
        dt_elements = soup.find_all('dt')
        for dt in dt_elements:
            dt_text = dt.text.strip().lower()
            dd = dt.find_next_sibling('dd')
            
            if dd:
                dd_text = dd.text.strip()
                if 'country of origin' in dt_text or 'страна' in dt_text:
                    band_info['location']['country'] = dd_text
                elif 'location' in dt_text or 'местоположение' in dt_text:
                    band_info['location']['city'] = dd_text
                elif 'status' in dt_text or 'статус' in dt_text:
                    band_info['status'] = dd_text
                elif 'formed in' in dt_text or 'год основания' in dt_text:
                    band_info['formed_in'] = dd_text
                elif 'years active' in dt_text or 'годы активности' in dt_text:
                    band_info['years_active'] = dd_text
        
        # Жанры
        genre_div = soup.find('dl', class_='float_right')
        
        if genre_div:
            genre_dd = genre_div.find('dd')
            if genre_dd:
                band_info['genres'] = genre_dd.text
        
        # Текущий состав (основные участники)
        band_info['current_lineup'] = []
        lineup_div = soup.find('div', id='band_tab_members_current')
        if lineup_div:
            for member in lineup_div.find_all('tr', class_='lineupRow'):
                print('member', member)
                band_info['current_lineup'].append({
                    'name': member.text.strip(),
                    'role': member.text,
                    'url': member.get('href')
                })
        
        # Дискография
        band_info['discography'] = []
        discography_div = soup.find('div', id='band_disco')
        if discography_div:
            album_rows = discography_div.find_all('tr')
            for row in album_rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    album_link = cols[0].find('a')
                    if album_link:
                        # Извлекаем ID альбома из href
                        album_href = album_link.get('href', '')
                        album_id = album_href.split('/').pop()
                        
                        band_info['discography'].append({
                            'name': album_link.text.strip(),
                            'year': cols[1].text.strip() if len(cols) > 1 else 'N/A',
                            'type': cols[2].text.strip() if len(cols) > 2 else 'N/A',
                            'id': album_id,
                            'url': album_href
                        })
        
        # Ссылка на фото группы
        band_photo = soup.find('a', id='photo')
        if band_photo and band_photo.get('href'):
            band_info['photo_url'] = band_photo.get('href')
        
        # Общая информация
        band_info['additional_info'] = {}
        info_table = soup.find('table', class_='display table_lyrics')
        if info_table:
            for row in info_table.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) == 2:
                    key = cols[0].text.strip().lower().replace(':', '')
                    value = cols[1].text.strip()
                    band_info['additional_info'][key] = value
        
        # Получаем ID группы из URL
        url_match = re.search(r'/bands/([^/]+)/(\d+)', html)
        if url_match:
            band_info['id'] = url_match.group(2)
            band_info['url_slug'] = url_match.group(1)
            
    except Exception as e:
        band_info['parsing_error'] = f"Ошибка при разборе HTML: {str(e)}"
    
    return band_info
def extract_album_info(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, 'html.page_handler')
    album_info = {}
    
    try:
        album_info['name'] = soup.find('h1', class_='album_name').text.strip()
        band_name = soup.find('h2', class_='band_name')
        band_id = band_name.find('a').get('href').split('/').pop()
        album_info['band_name'] = band_name.text.strip()
        album_info['band_id'] = band_id
    except Exception as e:
        album_info['parsing_error'] = f"Ошибка при разборе HTML: {str(e)}"
    return album_info    

def parse_band_page(
    url: str = "https://www.metal-archives.com/band/random",
    wait_time: int = 3,
    save_screenshot: bool = False
) -> BandInfoResponse:
    """
    Парсит страницу Metal Archives и возвращает структурированную информацию о группе.
    """
    start_time = time.time()
    
    try:
        with SB(uc=True, incognito=True, locale="en") as sb:
            try:
                print(f"Открываю {url} ...")
                sb.uc_open_with_reconnect(url, reconnect_time=4)
                sb.uc_gui_click_captcha()
                time.sleep(wait_time)
                sb.assert_element("body", timeout=10)
                
                # Получаем HTML и извлекаем информацию
                html = sb.get_page_source()
                band_info = extract_band_info(html)
                
                processing_time = time.time() - start_time
                
                return BandInfoResponse(
                    success=True,
                    band_info=band_info,
                    url=url,
                    processing_time=round(processing_time, 2)
                )
                
            except Exception as e:
                processing_time = time.time() - start_time
                error_msg = f"Ошибка при парсинге: {str(e)}"
                
                if save_screenshot:
                    try:
                        screenshot_name = f"error_{int(time.time())}.png"
                        sb.save_screenshot(screenshot_name)
                        error_msg += f" (скриншот сохранен как {screenshot_name})"
                    except:
                        pass
                
                return BandInfoResponse(
                    success=False,
                    error=error_msg,
                    url=url,
                    processing_time=round(processing_time, 2)
                )
                
    except Exception as e:
        processing_time = time.time() - start_time
        return BandInfoResponse(
            success=False,
            error=f"Ошибка при инициализации SeleniumBase: {str(e)}",
            url=url,
            processing_time=round(processing_time, 2)
        )

def parse_album_page(
    album_id: str = "",
    wait_time: int = 3,
    save_screenshot: bool = False
) -> BandInfoResponse:
    """
    Парсит страницу Metal Archives и возвращает структурированную информацию о группе.
    """
    start_time = time.time()
    url = "https://www.metal-archives.com/albums/view/id/{album_id}".format(album_id=album_id)
    try:
        with SB(uc=True, incognito=True, locale="en") as sb:
            try:
                print(f"Открываю {url} ...")
                sb.uc_open_with_reconnect(url, reconnect_time=4)
                sb.uc_gui_click_captcha()
                time.sleep(wait_time)
                sb.assert_element("body", timeout=10)
                
                # Получаем HTML и извлекаем информацию
                html = sb.get_page_source()
                album_info = extract_album_info(html)
                
                processing_time = time.time() - start_time
                
                return AlbumInfoResponse(
                    success=True,
                    album_info=album_info,
                    url=url,
                    processing_time=round(processing_time, 2)
                )
                
            except Exception as e:
                processing_time = time.time() - start_time
                error_msg = f"Ошибка при парсинге: {str(e)}"
                
                if save_screenshot:
                    try:
                        screenshot_name = f"error_{int(time.time())}.png"
                        sb.save_screenshot(screenshot_name)
                        error_msg += f" (скриншот сохранен как {screenshot_name})"
                    except:
                        pass
                
                return BandInfoResponse(
                    success=False,
                    error=error_msg,
                    url=url,
                    processing_time=round(processing_time, 2)
                )
                
    except Exception as e:
        processing_time = time.time() - start_time
        return BandInfoResponse(
            success=False,
            error=f"Ошибка при инициализации SeleniumBase: {str(e)}",
            url=url,
            processing_time=round(processing_time, 2)
        )

@app.get("/band/random", response_model=BandInfoResponse, tags=["Парсинг"])
async def parse_random_band():
    """
    Парсит случайную страницу группы на Metal Archives.
    
    Возвращает структурированную информацию о группе в JSON формате.
    """
    return parse_band_page()

@app.get("/album/{album_id}", response_model=AlbumInfoResponse, tags=["Парсинг"])
async def get_album_by_id(album_id: int):
    """
    Парсит страницу альбома по его ID.
    """
    return parse_album_page(album_id)


if __name__ == "__main__":
    import uvicorn
    
    print("Запуск FastAPI сервера...")
    print("Документация: http://localhost:8000/docs")
    print("Для получения информации о случайной группе: GET http://localhost:8000/band/random")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
