import re
import json
from datetime import datetime
from bs4 import BeautifulSoup, Tag
from typing import Dict, List, Optional


from app.page_handler.data_parser.models import (
    Album,
    BandInformation,
    BandSearch,
    AlbumShortInformation,
    AlbumInformation,
    BandLocationInfo,
    MemberLineUp,
    StatusAndDateInfo,
    Track
)


class PageParser:
    uid_patter = r'/bands/(?P<slug>[^/]+)/(?P<uid>\d+)'
    
    @classmethod
    def extract_search_info(cls, data: str) -> BandSearch:
        soup = BeautifulSoup(data, 'html.parser')
        results = json.loads(soup.find('pre').text)['aaData']
        bands = []
        for item in results:
            html_content = item[0]
            
            match = re.search(r'">([^<]+)</a>', html_content)
            name = match.group(1) if match else html_content

            id_match = re.search(r'/(\d+)"', html_content)
            band_id = id_match.group(1) if id_match else None
            genre = item[1].strip()
            country = item[2].strip()
            
            band_info = {
                'id': int(band_id),
                'name': name,
                'genre': genre,
                'country': country
            }
            
            bands.append(band_info)
        
        return bands

    @classmethod
    def extract_band_info(cls, data: str) -> BandInformation:
        soup = BeautifulSoup(data, 'html.parser')
        band_info = BandInformation()
        try:
            band_name, band_id = cls._get_band_name_and_id(soup)
            band_info.id = band_id
            band_info.name = band_name

            location, status_and_dates, label, themes = cls._get_band_common_info(soup)
            band_info.country = location.country
            band_info.city = location.city
            band_info.status = status_and_dates.status
            band_info.formed_in = status_and_dates.formed_in
            band_info.years_active = status_and_dates.years_active
            band_info.themes = themes
            band_info.label = label

            band_info.genres = cls._get_genre(soup)
            band_info.current_lineup = cls._get_current_lineup(soup)
            band_info.photo_url = cls._get_photo_url(soup)
            band_info.logo_url = cls._get_logo_url(soup)
        except Exception as err:
            band_info.parsing_error = f"Ошибка при разборе HTML: {str(err)}"

        return band_info
    
    @classmethod
    def extract_discography_info(cls, data: str) -> AlbumInformation:
        soup = BeautifulSoup(data, 'html.parser')
        return cls._get_discography(soup)
    
    @classmethod
    def extract_album_info(cls, data: str) -> AlbumInformation:
        soup = BeautifulSoup(data, 'html.parser')
        album_info = {}
        try:
            album_info = cls._get_album_info(cls, soup)
        except Exception as err:
            album_info.parsing_error = f"Ошибка при разборе HTML: {str(err)}"
        
        return album_info

    @staticmethod
    def _get_band_name_and_id(soup: BeautifulSoup) -> list[str, int]:
        band_name_elem = soup.find('h1', class_='band_name')
        if not band_name_elem:
            band_name_elem = soup.find('h2', class_='band_name')
        band_id = band_name_elem.find('a').get('href').split('/').pop()
        return band_name_elem.text.strip(), int(band_id)
    
    @staticmethod
    def _get_album_info(cls, soup: BeautifulSoup) -> AlbumInformation:
        """Получает информацию об альбоме из страницы"""
        album_info = AlbumInformation()
        try:
            album_info = cls._parse_common_album_info(soup, album_info)
            album_info.tracklist = cls._parse_tracklist(cls, soup)

            return album_info
        except (AttributeError, IndexError) as err:
            album_info.parsing_error = f"Ошибка при разборе HTML: {str(err)}"
            return None
        
    @staticmethod
    def _parse_tracklist(cls, soup: BeautifulSoup) -> list[Track]:
        """
        Парсит HTML-таблицу с треклистом и возвращает структурированные данные.
        
        Args:
            html_content: HTML строка содержащая таблицу с треклистом
            
        Returns:
            Список словарей с ключами: number, title, duration, cdNumber, side
        """
        tracklist = []
        
        # Находим таблицу с треклистом
        table = soup.find('table', {'class': 'display table_lyrics'})
        if not table:
            return []
        
        # Извлекаем все строки таблицы
        rows = table.find_all('tr')
        if not rows:
            return []
        
        # Инициализируем переменные для отслеживания текущей стороны и CD
        current_side = None
        cd_number = None
        track_counter = 0
        
        for row in rows:
            # Проверяем, является ли строка заголовком стороны (Side A/B)
            side_cell = row.find('td', {'colspan': '4'})
            if side_cell and 'side' in side_cell.get_text(strip=True, separator=' ').lower():
                side_text = side_cell.get_text(strip=True)
                # Извлекаем сторону (A, B, C, D и т.д.)
                if 'side' in side_text.lower():
                    current_side = side_text.split()[-1].strip()
            
            # Пропускаем строки, которые не являются треками (суммарное время, технические строки)
            elif row.has_attr('class'):
                row_classes = row.get('class', [])
                
                # Пропускаем скрытые строки с текстами песен
                if 'displayNone' in row_classes:
                    continue
                    
                # Пропускаем строку с общим временем
                if 'sideRow' in row_classes or row.find('strong'):
                    continue
                
                # Обрабатываем строки с треками (содержащие even/odd классы)
                if 'even' in row_classes or 'odd' in row_classes:
                    track_data = cls._extract_track_data(row, current_side, cd_number)
                    if track_data:
                        tracklist.append(track_data)
                        track_counter += 1
        
        return tracklist

    @staticmethod
    def _extract_track_data(row: Tag, current_side: Optional[str], cd_number: int) -> Optional[Dict[str, str]]:
        """
        Извлекает данные о конкретном треке из строки таблицы.
        
        Args:
            row: BeautifulSoup Tag объекта строки таблицы
            current_side: Текущая сторона (A/B)
            cd_number: Номер CD
            
        Returns:
            Словарь с данными трека или None если данные некорректны
        """
        try:
            # Извлекаем все ячейки строки
            cells = row.find_all('td')
            if len(cells) < 3:
                return None
            
            # Извлекаем номер трека (удаляем точку в конце)
            track_number_cell = cells[0]
            track_number = track_number_cell.get_text(strip=True).rstrip('.')
            
            # Извлекаем название трека
            title_cell = cells[1]
            title = title_cell.get_text(strip=True)
            
            # Извлекаем длительность
            duration_cell = cells[2]
            duration = duration_cell.get_text(strip=True)
            
            # Формируем результат
            return Track(title=title, number=int(track_number), duration=duration, cdNumber=cd_number, side=current_side if current_side else 'Unknown')
            
        except (AttributeError, IndexError, ValueError) as e:
            # Логирование ошибки (в production можно использовать logging)
            print(f"Ошибка при парсинге строки трека: {e}")
            return None
    
    @staticmethod
    def _parse_common_album_info(soup: BeautifulSoup, album_info: AlbumInformation):
        # common info
        album_name = soup.find('h1', class_='album_name')
        album_info.id = int(album_name.find('a').get('href').split('/').pop())
        album_info.title = album_name.text.strip()
        band_name = soup.find('h2', class_='band_name')
        album_info.band_name = band_name.text.strip()
        album_info.band_id = int(band_name.find('a').get('href').split('/').pop())
        album_info.cover_url = soup.find(id='cover').get('href')
        album_info.url = album_name.find('a').get('href')
    
        dt_elements = soup.find_all('dt')
        for dt in dt_elements:
            dt_text = dt.text.strip().lower()
            dd = dt.find_next_sibling('dd')
            
            if not dd:
                continue

            cell_text = dd.text.strip()
            match dt_text:
                case text if 'type' in text:
                    album_info.type = cell_text
                case text if 'release date' in text:
                    album_info.release_date = cell_text
                case text if 'label' in text:
                    album_info.label = cell_text
        return album_info

    @staticmethod
    def _get_band_common_info(soup: BeautifulSoup) -> (BandLocationInfo, StatusAndDateInfo, str, str):
        location = BandLocationInfo()
        status_and_dates = StatusAndDateInfo()
        label = ''
        themes = ''

        dt_elements = soup.find_all('dt')
        for dt in dt_elements:
            dt_text = dt.text.strip().lower()
            dd = dt.find_next_sibling('dd')
            if not dd:
                continue

            cell_text = dd.text.strip()
            match dt_text:
                case text if 'country of origin' in text:
                    location.country = cell_text
                case text if 'location' in text:
                    location.city = cell_text
                case text if 'status' in text:
                    status_and_dates.status = cell_text
                case text if 'formed in' in text:
                    status_and_dates.formed_in = cell_text
                case text if 'years active' in text:
                    status_and_dates.years_active = re.sub(r'\s+', ' ', cell_text).strip()
                case text if 'label' in text:
                    label = cell_text
                case text if 'themes' in text:
                    themes = cell_text
        return location, status_and_dates, label, themes

    @staticmethod
    def _get_genre(soup: BeautifulSoup):
        genre_div = soup.find('dl', class_='float_right')
        if not genre_div:
            return None

        if genre_dd := genre_div.find('dd'):
            return genre_dd.text

    @classmethod
    def _get_current_lineup(cls, soup: BeautifulSoup) -> list[MemberLineUp]:
        current_lineup_table = soup.find('div', id='band_tab_members_current')
        lineup_table = current_lineup_table.find('table', class_='lineupTable')
        members = []
        if lineup_table:
            rows = lineup_table.find_all('tr', class_='lineupRow')
            for member in rows:
                member_link = member.find('a')
                members.append(MemberLineUp(name=member_link.text.strip(), role=re.sub(r'\s+', ' ', member.find_all('td')[1].text).strip(), url=member_link.get('href').strip()))
            
        return members

    @staticmethod
    def _get_discography(soup: BeautifulSoup) -> list[AlbumInformation]:
        result = []
        discography_table = soup.find('table', class_='display discog')
        if not discography_table:
            return result

        album_rows = discography_table.find_all('tr')
        for row in album_rows:
            cols = row.find_all('td')
            count_columns = len(cols)
            if count_columns < 2:
                continue

            if album_link := cols[0].find('a'):
                album = AlbumShortInformation(
                    title=album_link.text.strip(),
                    type=cols[1].text.strip(),
                    release_date=cols[2].text.strip()
                )

                album.url = album_link.get('href', '')
                album.id = int(album.url.split('/').pop())

                result.append(album)
        sorted_strings = sorted(result, key=lambda x: datetime.strptime(x.release_date, '%Y'), reverse=True)

        return sorted_strings

    @staticmethod
    def _get_photo_url(soup: BeautifulSoup) -> str | None:
        photo = soup.find('a', id='photo')
        if photo:
            return photo.get('href')
        return None
    
    @staticmethod
    def _get_logo_url(soup: BeautifulSoup) -> str | None:
        logo = soup.find('a', id='logo')
        if logo:
            return logo.get('href')
        return None
