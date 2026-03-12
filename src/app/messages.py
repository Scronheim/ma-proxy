from dataclasses import dataclass, field, asdict
from typing import Optional, List
import json

from app.page_handler.data_parser.models import AlbumInformation, AlbumShortInformation, BandInformation

@dataclass
class SSE_response:
  type: str = field(default_factory=str)
  message: str = field(default_factory=str)
  data: Optional[dict[str, str]] = field(default=dict)

def get_start_random_message() -> SSE_response:
  return {
    'type': 'start_random',
    'message': 'Началась обработка случайной группы'
  }

def get_band_links_message():
  return {
    'type': 'band_links',
    'message': 'Началась обработка ссылок группы'
  }

def get_new_album_message(album: AlbumInformation) -> SSE_response:
  return {
    'type': 'new_album',
    'message': f'Добавлен новый альбом {album.band_names} - {album.title} ({album.release_date})',
    'data': {
      'id': album.id,
      'title': album.title,
      'title_slug': album.title_slug,
      'type': album.type,
      'release_date': album.release_date,
      'cover_url': album.cover_url,
    }
  }

def refresh_band_message(band: BandInformation, old_albums: List[AlbumShortInformation], new_albums: List[AlbumShortInformation]) -> SSE_response:
  old_albums_dicts = [asdict(album) for album in old_albums]
  new_albums_dicts = [asdict(album) for album in new_albums]
  return {
    'type': 'refresh_band',
    'message': f'Обновлена группа {band.name}',
    'data': {
      'old_albums': json.dumps(old_albums_dicts, ensure_ascii=False, indent=2),
      'new_albums': json.dumps(new_albums_dicts, ensure_ascii=False, indent=2),
    }
  }

def get_album_number_message(album_number: int) -> SSE_response:
  return {
    'type': 'album_number',
    'message': f'Добавлено {album_number} альбомов'
  }

