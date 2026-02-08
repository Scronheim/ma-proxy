from dataclasses import dataclass, field
from typing import Optional

from app.page_handler.data_parser.models import AlbumInformation

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
    'message': f'Добавлен новый альбом {album.band_name} - {album.title} ({album.release_date})',
    'data': {
      'id': album.id,
      'cover_url': album.cover_url
    }
  }

def get_album_number_message(album_number: int) -> SSE_response:
  return {
    'type': 'album_number',
    'message': f'Добавлено {album_number} альбомов'
  }

