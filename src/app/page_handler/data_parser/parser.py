import datetime
import json
import re
from typing import Dict, Optional

from bs4 import BeautifulSoup, Tag

from app.page_handler.data_parser.models import (
    AlbumInformation,
    AlbumSearch,
    AlbumShortInformation,
    BandInformation,
    BandLocationInfo,
    BandSearch,
    MemberLineUp,
    StatusAndDateInfo,
    Track,
    StatInfo,
    BandStatInfo,
    SocialLink,
    Member,
    MemberBand,
    MemberAlbum,
    OtherBand
)
from app.utils.utils import slug_string


class PageParser:
    uid_patter = r'/bands/(?P<slug>[^/]+)/(?P<uid>\d+)'

    @classmethod
    def extract_search_album_info(cls, data: str) -> list[AlbumSearch]:
        soup = BeautifulSoup(data, 'html.parser')
        soup
        results = json.loads(soup.find('pre').text)['aaData']
        albums = []
        for album in results:
            band_soup = BeautifulSoup(album[0], 'html.parser').find('a')
            band_id = band_soup.get('href').split('/').pop()
            band_name = band_soup.text.strip()
            band_name_slug = slug_string(band_soup.text.strip())
            album_soup = BeautifulSoup(album[1], 'html.parser').find('a')
            album_id = album_soup.get('href').split('/').pop()
            album_name = album_soup.text.strip()
            album_type = album[2]
            album_release_date = album[3].split(' <!')[0]

            albums.append(
                AlbumSearch(
                    id=int(album_id),
                    title=album_name,
                    title_slug=slug_string(album_name),
                    band_name=band_name,
                    band_name_slug=band_name_slug,
                    band_id=int(band_id),
                    type=album_type,
                    release_date=album_release_date,
                )
            )
        return albums

    @classmethod
    def extract_search_band_info(cls, data: str) -> list[BandSearch]:
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
            bands.append(
                BandSearch(
                    id=int(band_id),
                    name=name,
                    name_slug=slug_string(name),
                    genre=genre,
                    country=country,
                )
            )

        return bands

    @classmethod
    def extract_band_info(cls, data: str) -> BandInformation:
        soup = BeautifulSoup(data, 'html.parser')
        band_info = BandInformation()
        try:
            band_name, band_name_slug, band_id = cls._get_band_name_and_id(soup)
            band_info.id = band_id
            band_info.name = band_name
            band_info.name_slug = band_name_slug

            location, status_and_dates, label, themes = cls._get_band_common_info(soup)
            band_info.country = location.country
            band_info.city = location.city
            band_info.status = status_and_dates.status
            band_info.formed_in = status_and_dates.formed_in
            band_info.years_active = status_and_dates.years_active
            band_info.themes = themes
            band_info.label = label

            band_info.genres = cls._get_genre(soup)
            band_info.current_lineup = cls._get_lineup(soup)
            band_info.past_lineup = cls._get_lineup(soup, False)
            band_info.photo_url = cls._get_photo_url(soup)
            band_info.logo_url = cls._get_logo_url(soup)
            band_info.updated_at = datetime.datetime.now(datetime.timezone.utc)
        except Exception as err:
            band_info.parsing_error = f"Ошибка при разборе HTML: {str(err)}"

        return band_info

    @classmethod
    def extract_discography_info(cls, data: str) -> list[AlbumShortInformation]:
        soup = BeautifulSoup(data, 'html.parser')
        return cls._get_discography(soup)

    @classmethod
    def extract_lyrics_info(cls, data: str) -> str:
        soup = BeautifulSoup(data, 'html.parser')
        return soup.find('body').get_text(strip=True)
    
    @classmethod
    def extract_band_description(cls, data: str) -> str:
        soup = BeautifulSoup(data, 'html.parser')
        return soup.find('body').decode_contents().replace('https://www.metal-archives.com/bands', '/bands')
    
    @classmethod
    def extract_member_info(cls, data: str) -> Member:
        soup = BeautifulSoup(data, 'html.parser')
        fullname = soup.find('h1', class_='band_member_name').get_text(strip=True)
        scripts = soup.find_all('script')
        id = 0
        for script in scripts:
            if script.string and 'artistId' in script.string:
                match = re.search(r'artistId\s*=\s*(\d+);', script.string)
                if match:
                    id = int(match.group(1))
                    break
        age = soup.find('dl', class_='float_left').find_all('dd')[1].get_text(strip=True)
        right_side = soup.find('dl', class_='float_right').find_all('dd')
        place_of_birth = right_side[0].get_text(strip=True)
        gender = right_side[1].get_text(strip=True)
        photo_link = soup.find('a', id='artist')
        photo_url = None
        if photo_link:
            photo_url = photo_link.get('href')
        biography = ''
        biography_div = soup.find('div', class_='clear band_comment')
        if len(biography_div.contents) > 1:
            h2 = biography_div.find_all('h2')
            for tag in h2:
                tag.decompose()
            biography = biography_div.decode_contents().strip().replace('https://www.metal-archives.com/bands', '/bands').replace('\t', '').replace('\n', '')
        active_bands = []
        past_bands = []
        guest_session = []
        live = []
        misc_staff = []
        
        active_bands_div = soup.find('div', id='artist_tab_active')
        if active_bands_div:
            member_in_active_band_divs = active_bands_div.find_all('div', class_='member_in_band')
            active_bands = cls._parse_member_bands(member_in_active_band_divs)
        
        past_bands_div = soup.find('div', id='artist_tab_past')
        if past_bands_div:
            member_in_past_band_divs = past_bands_div.find_all('div', class_='member_in_band')
            past_bands = cls._parse_member_bands(member_in_past_band_divs)
        
        guest_session_div = soup.find('div', id='artist_tab_guest')
        if guest_session_div:
            member_in_guest_session_divs = guest_session_div.find_all('div', class_='member_in_band')
            guest_session = cls._parse_member_bands(member_in_guest_session_divs)
        
        live_div = soup.find('div', id='artist_tab_live')
        if live_div:
            member_in_live_divs = live_div.find_all('div', class_='member_in_band')
            live = cls._parse_member_bands(member_in_live_divs)
        
        misc_staff_div = soup.find('div', id='artist_tab_misc')
        if misc_staff_div:
            member_in_misc_staff_divs = misc_staff_div.find_all('div', class_='member_in_band')
            misc_staff = cls._parse_member_bands(member_in_misc_staff_divs)
        
        return Member(
            id=id,
            fullname=fullname,
            fullname_slug=slug_string(fullname),
            age=age,
            place_of_birth=place_of_birth,
            gender=gender,
            photo_url=photo_url,
            biography=biography,
            active_bands=active_bands,
            past_bands=past_bands,
            guest_session=guest_session,
            live=live,
            misc_staff=misc_staff,
            updated_at=datetime.datetime.now(datetime.timezone.utc)
        )
    
    @classmethod
    def extract_social_links(cls, data: str) -> list[SocialLink]:
        soup = BeautifulSoup(data, 'html.parser')
        all_links = soup.find_all('a', target='_blank')
        band_links = []
        for link in all_links:
            social = link.text.strip()
            url = link.get('href')
            band_links.append(SocialLink(social=social, url=url))
        return band_links
    
    @classmethod
    def extract_stats_info(cls, data: str) -> StatInfo:
        soup = BeautifulSoup(data, 'html.parser')
        active = int(soup.find('span', class_='active').text.strip())
        on_hold = int(soup.find('span', class_='on_hold').text.strip())
        split_up = int(soup.find('span', class_='split_up').text.strip())
        changed_name = int(soup.find('span', class_='changed_name').text.strip())
        unknown = int(soup.find('span', class_='unknown').text.strip())
        total = active + on_hold + split_up + changed_name + unknown
        bands_stat = BandStatInfo(
            active=active, on_hold=on_hold,
            split_up=split_up, changed_name=changed_name,
            unknown=unknown, total=total
        )
        strong_tags = soup.select('p > strong')
        albums = int(strong_tags[-2].text)
        songs = int(strong_tags[-1].text)

        return StatInfo(bands=bands_stat, albums=albums, songs=songs)
    
    @classmethod
    def extract_album_info(cls, data: str) -> AlbumInformation:
        soup = BeautifulSoup(data, 'html.parser')
        album_info = AlbumInformation()
        try:
            album_info = cls._get_album_info(cls, soup)
        except Exception as err:
            album_info.parsing_error = f"Ошибка при разборе HTML: {str(err)}"

        return album_info

    def _parse_member_bands(member_in_band_divs: list[Tag]) -> list[MemberBand]:
        active_bands = []
        for band_div in member_in_band_divs:
            band_name_h3 = band_div.find('h3', class_='member_in_band_name')
            band_link = band_name_h3.find('a')
            if band_link:
                band_id = int(band_link.get('href').split('#')[0].split('/').pop())
                band_name = band_link.get_text(strip=True)
                band_name_slug = slug_string(band_name)
            else:
                band_name = band_name_h3.get_text(strip=True)
                band_id = None
                band_name_slug = None
            role = band_div.find('p', class_='member_in_band_role').get_text(strip=True)
            albums_table = band_div.find('table')
            albums = []
            if albums_table:
                albums_tr = albums_table.find_all('tr')
                for album_tr in albums_tr:
                    album_tds = album_tr.find_all('td')
                    if len(album_tds) > 1:
                        album_id = album_tds[1].find('a').get('href').split('/').pop()
                        album_title = album_tds[1].find('a').get_text(strip=True)
                        album_title_slug = slug_string(album_title)
                        release_date = album_tds[0].get_text(strip=True)
                        role = album_tds[2].get_text(strip=True).replace('\t', '')
                        albums.append(
                            MemberAlbum(
                                id=int(album_id),
                                title=album_title,
                                title_slug=album_title_slug,
                                release_date=release_date,
                                role=role
                            )
                        )
            active_bands.append(
                MemberBand(
                    id=band_id,
                    name=band_name,
                    name_slug=band_name_slug,
                    albums=albums,
                    role=role
                )
            )
        return active_bands    

    @staticmethod
    def _get_band_name_and_id(soup: BeautifulSoup) -> list[str, int]:
        band_name_elem = soup.find('h1', class_='band_name')
        if not band_name_elem:
            band_name_elem = soup.find('h2', class_='band_name')
        band_id = band_name_elem.find('a').get('href').split('/').pop()
        return band_name_elem.text.strip(), slug_string(band_name_elem.text.strip()), int(band_id)

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
        tracklist = []

        table = soup.find('table', {'class': 'display table_lyrics'})
        if not table:
            return []

        rows = table.find_all('tr')
        if not rows:
            return []

        current_side = None
        cd_number = None
        track_counter = 0

        for row in rows:
            side_cell = row.find('td', {'colspan': '4'})
            if side_cell and 'side' in side_cell.get_text(strip=True, separator=' ').lower():
                side_text = side_cell.get_text(strip=True)
                
                if 'side' in side_text.lower():
                    current_side = side_text.split()[-1].strip()

            elif row.has_attr('class'):
                row_classes = row.get('class', [])

                if 'sideRow' in row_classes or row.find('strong'):
                    continue

                if 'even' in row_classes or 'odd' in row_classes or 'displayNone' in row_classes:
                    track_data = cls._extract_track_data(row, current_side, cd_number)
                    if track_data:
                        tracklist.append(track_data)
                        track_counter += 1

        return tracklist

    @staticmethod
    def _extract_track_data(row: Tag, current_side: Optional[str], cd_number: int) -> Optional[Dict[str, str]]:
        try:
            cells = row.find_all('td')
            id = None
            
            if len(cells) < 3:
                return None

            track_number_cell = cells[0]
            track_number = track_number_cell.get_text(strip=True).rstrip('.')

            title_cell = cells[1]
            title = title_cell.get_text(strip=True).replace('\n', '').replace('\t', '')

            duration_cell = cells[2]
            duration = duration_cell.get_text(strip=True)

            if cells[3]:
                id_link = cells[3].find('a')
                if id_link:
                    id = int(re.sub(r'\D', '', id_link.get('href').split('#')[1]))
                elif cells[3].find('em'):
                    id = cells[3].find('em').get_text(strip=True)
            return Track(
                id=id,
                title=title,
                number=int(track_number),
                duration=duration,
                lyrics=None,
                cdNumber=cd_number,
                side=current_side if current_side else None
            )

        except (AttributeError, IndexError, ValueError) as e:
            print(f"Ошибка при парсинге строки трека: {e}")
            return None

    @staticmethod
    def _parse_common_album_info(soup: BeautifulSoup, album_info: AlbumInformation):
        # common info
        album_name = soup.find('h1', class_='album_name')
        album_info.id = int(album_name.find('a').get('href').split('/').pop())
        album_info.title = album_name.text.strip()
        album_info.title_slug = slug_string(album_name.text.strip())
        band_names = soup.find('h2', class_='band_name').find_all('a')
        for band_link in band_names:
            album_info.band_names.append(band_link.text.strip())
            album_info.band_names_slug.append(slug_string(band_link.text.strip()))
            album_info.band_ids.append(int(band_link.get('href').split('/').pop()))
        cover_url = soup.find(id='cover')
        if cover_url:
            album_info.cover_url = cover_url.get('href').split('https://www.metal-archives.com')[1]
        album_info.url = album_name.find('a').get('href')
        album_info.updated_at = datetime.datetime.now(datetime.timezone.utc)

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
    def _get_band_common_info(soup: BeautifulSoup) -> tuple[BandLocationInfo, StatusAndDateInfo, str, str]:
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
    def _get_lineup(cls, soup: BeautifulSoup, current: bool = True) -> list[MemberLineUp]:
        lineup_div = soup.find('div', id="band_tab_members_current" if current == True else "band_tab_members_past")
        members = []
        if lineup_div:
            lineup_table = lineup_div.find('table', class_='lineupTable')
            if lineup_table:
                rows = lineup_table.find_all('tr')
                for element in rows:
                    if element.name == 'tr' and 'lineupRow' in element.get('class', []):
                        name_link = element.find('a', class_='bold')
                        if name_link:
                            fullname = name_link.text.strip()
                            href = name_link.get('href', '')
                            artist_id = int(href.split('/')[-1]) if href else None
                            
                            role_td = element.find_all('td')[1]
                            role = role_td.text.strip()
                            
                            current_artist = {
                                'id': artist_id,
                                'fullname': fullname,
                                'fullname_slug': slug_string(fullname),
                                'role': role,
                                'url': href,
                                'other_bands': []
                            }
                            members.append(MemberLineUp(**current_artist))
                    
                    elif element.name == 'tr' and 'lineupBandsRow' in element.get('class', []):
                        if members and current_artist:
                            see_also_td = element.find('td')
                            if see_also_td:
                                see_also_text = see_also_td.get_text(strip=True)
                                see_also_text = see_also_text.replace('See also:', '').strip()
                                
                                items = [item.strip() for item in see_also_text.split(',') if item.strip()]
                                
                                see_also_links = see_also_td.find_all('a')
                                
                                links_dict = {}
                                for link in see_also_links:
                                    link_text = link.text.strip()
                                    href = link.get('href')
                                    if '/bands/' in href:
                                        links_dict[link_text] = href.split('/')[-1]
                                for item in items:
                                    if item and item != 'See also:':
                                        item = item.replace('ex-', '')
                                        if item in links_dict:
                                            members[-1].other_bands.append(OtherBand(
                                                id=int(links_dict[item]),
                                                name=item,
                                                name_slug=slug_string(item)
                                            ))
                                        else:
                                            members[-1].other_bands.append(OtherBand(
                                                id=None,
                                                name=item,
                                                name_slug=slug_string(item)
                                            ))

        return members

    @staticmethod
    def _get_discography(soup: BeautifulSoup) -> list[AlbumShortInformation]:
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
                url = album_link.get('href', '')
                result.append(
                    AlbumShortInformation(
                        id=int(url.split('/').pop()),
                        title=album_link.text.strip(),
                        title_slug=slug_string(album_link.text.strip()),
                        type=cols[1].text.strip(),
                        release_date=cols[2].text.strip(),
                        cover_loading=True,
                        url=url
                    )
                )
        sorted_strings = sorted(
            result,
            key=lambda album: datetime.datetime.strptime(album.release_date, '%Y'),
            reverse=True
        )
        return sorted_strings

    @staticmethod
    def _get_photo_url(soup: BeautifulSoup) -> str | None:
        photo = soup.find('a', id='photo')
        if photo:
            return photo.get('href').split('https://www.metal-archives.com')[1]
        return None

    @staticmethod
    def _get_logo_url(soup: BeautifulSoup) -> str | None:
        logo = soup.find('a', id='logo')
        if logo:
            return logo.get('href').split('https://www.metal-archives.com')[1]
        return None
