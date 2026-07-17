import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Модели данных
class FileInfo(BaseModel):
    name: str
    path: str
    type: str  # "file" или "directory"
    size: Optional[int] = None
    modified: Optional[str] = None
    extension: Optional[str] = None

class DirectoryContent(BaseModel):
    current_path: str
    parent_path: Optional[str]
    items: List[FileInfo]
    
class CreateFolderRequest(BaseModel):
    folder_name: str
    
class RenameRequest(BaseModel):
    old_name: str
    new_name: str
    
class MoveCopyRequest(BaseModel):
    source: str
    destination: str

def create_file_manager_router(
    base_directory: str,
    route_prefix: str = "",
    allow_delete: bool = False,
    allow_rename: bool = True,
    allow_move: bool = True,
    allow_copy: bool = True,
    allow_upload: bool = True,
    allow_create_folder: bool = True,
    max_file_size: Optional[int] = None,  # в байтах
    allowed_extensions: Optional[List[str]] = None
) -> APIRouter:
    """
    Создает роутер файлового менеджера.
    
    Args:
        base_directory: Корневая директория для работы файлового менеджера
        route_prefix: Префикс для всех маршрутов
        allow_delete: Разрешить удаление
        allow_rename: Разрешить переименование
        allow_move: Разрешить перемещение
        allow_copy: Разрешить копирование
        allow_upload: Разрешить загрузку файлов
        allow_create_folder: Разрешить создание папок
        max_file_size: Максимальный размер загружаемого файла
        allowed_extensions: Список разрешенных расширений
    """
    
    router = APIRouter(prefix=route_prefix)
    base_path = Path(base_directory).resolve()
    
    def validate_path(path: str) -> Path:
        """Проверяет, что путь находится внутри базовой директории"""
        try:
            # Декодируем URL-кодированный путь
            from urllib.parse import unquote
            path = unquote(path)
            
            full_path = (base_path / path).resolve()
            # Проверяем, что путь находится внутри base_path
            if not str(full_path).startswith(str(base_path)):
                raise HTTPException(status_code=400, detail="Access denied: path outside base directory")
            return full_path
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid path: {str(e)}")
    
    def get_relative_path(full_path: Path) -> str:
        """Возвращает относительный путь от базовой директории"""
        return str(full_path.relative_to(base_path))
    
    def get_file_info(file_path: Path) -> FileInfo:
        """Получает информацию о файле или директории"""
        stat = file_path.stat()
        is_dir = file_path.is_dir()
        
        modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        if is_dir:
            return FileInfo(
                name=file_path.name,
                path=get_relative_path(file_path),
                type="directory",
                modified=modified
            )
        else:
            return FileInfo(
                name=file_path.name,
                path=get_relative_path(file_path),
                type="file",
                size=stat.st_size,
                modified=modified,
                extension=file_path.suffix.lower() if file_path.suffix else None
            )
    
    @router.get("/list", response_model=DirectoryContent)
    async def list_directory(path: str = Query("", description="Путь относительно базовой директории")):
        """
        Получить содержимое директории
        """
        full_path = validate_path(path)
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Path not found")
        
        if not full_path.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")
        
        items = []
        for item in full_path.iterdir():
            try:
                items.append(get_file_info(item))
            except Exception:
                continue  # Пропускаем файлы, к которым нет доступа
        
        # Сортируем: сначала папки, потом файлы, по алфавиту
        items = sorted(items, key=track_key)
        
        parent = None
        if path and path != ".":
            parent_path = str(Path(path).parent)
            parent = parent_path if parent_path != "." else ""
        
        return DirectoryContent(
            current_path=path or "",
            parent_path=parent,
            items=items
        )
    
    @router.get("/info")
    async def get_info(path: str = Query(..., description="Путь к файлу/папке")):
        """
        Получить информацию о файле или папке
        """
        full_path = validate_path(path)
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Path not found")
        
        return get_file_info(full_path)
    
    @router.post("/upload")
    async def upload_file(
        path: str = Form("", description="Путь для загрузки"),
        files: List[UploadFile] = File(..., description="Файлы для загрузки")
    ):
        """
        Загрузить файлы в указанную директорию
        """
        upload_path = validate_path(path)
        print(upload_path, path, files)
        
        if not upload_path.exists():
            raise HTTPException(status_code=404, detail="Upload directory not found")
        
        if not upload_path.is_dir():
            raise HTTPException(status_code=400, detail="Upload path is not a directory")
        
        uploaded_files = []
        errors = []
        print(path, files)
        for file in files:
            try:
                # Проверка расширения
                if allowed_extensions:
                    ext = Path(file.filename).suffix.lower()
                    if ext not in allowed_extensions and ext:  # Пропускаем файлы без расширения
                        errors.append({
                            "filename": file.filename,
                            "error": f"File extension {ext} not allowed. Allowed: {allowed_extensions}"
                        })
                        continue
                
                # Проверка размера
                if max_file_size:
                    file.file.seek(0, 2)
                    file_size = file.file.tell()
                    file.file.seek(0)
                    
                    if file_size > max_file_size:
                        errors.append({
                            "filename": file.filename,
                            "error": f"File size exceeds maximum allowed ({max_file_size} bytes)"
                        })
                        continue
                
                file_path = upload_path / file.filename
                
                # Проверяем, не выходит ли файл за пределы базовой директории
                if not str(file_path.resolve()).startswith(str(base_path)):
                    errors.append({
                        "filename": file.filename,
                        "error": "Access denied"
                    })
                    continue
                
                # Сохраняем файл
                content = await file.read()
                with open(file_path, "wb") as f:
                    f.write(content)
                
                uploaded_files.append(get_file_info(file_path))
                
            except Exception as e:
                errors.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        return {
            "uploaded": uploaded_files,
            "errors": errors,
            "success": len(errors) == 0
        }
    
    if allow_create_folder:
        @router.post("/folder")
        async def create_folder(
            path: str = Query("", description="Путь для создания папки"),
            request: CreateFolderRequest = None
        ):
            """
            Создать новую папку
            """
            parent_path = validate_path(path)
            
            if not parent_path.exists():
                raise HTTPException(status_code=404, detail="Parent directory not found")
            
            if not parent_path.is_dir():
                raise HTTPException(status_code=400, detail="Parent path is not a directory")
            
            folder_path = parent_path / request.folder_name
            
            # Проверяем, не выходит ли путь за пределы базовой директории
            if not str(folder_path.resolve()).startswith(str(base_path)):
                raise HTTPException(status_code=400, detail="Access denied")
            
            if folder_path.exists():
                raise HTTPException(status_code=400, detail="Folder already exists")
            
            folder_path.mkdir(parents=True)
            
            return get_file_info(folder_path)
    
    if allow_delete:
        @router.delete("/delete")
        async def delete_item(path: str = Query(..., description="Путь к файлу/папке")):
            """
            Удалить файл или папку
            """
            full_path = validate_path(path)
            
            if not full_path.exists():
                raise HTTPException(status_code=404, detail="Path not found")
            
            # Защита от удаления корневой директории
            if full_path == base_path:
                raise HTTPException(status_code=400, detail="Cannot delete root directory")
            
            try:
                if full_path.is_dir():
                    shutil.rmtree(full_path)
                else:
                    full_path.unlink()
                
                return {"success": True, "message": f"{'Directory' if full_path.is_dir() else 'File'} deleted successfully"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error deleting: {str(e)}")
    
    if allow_rename:
        @router.put("/rename")
        async def rename_item(
            path: str = Query("", description="Путь к файлу/папке"),
            request: RenameRequest = None
        ):
            """
            Переименовать файл или папку
            """
            parent_path = validate_path(path)
            full_path = parent_path / request.old_name
            
            if not full_path.exists():
                raise HTTPException(status_code=404, detail="Item not found")
            
            new_path = parent_path / request.new_name
            
            # Проверяем, не выходит ли новый путь за пределы базовой директории
            if not str(new_path.resolve()).startswith(str(base_path)):
                raise HTTPException(status_code=400, detail="Access denied")
            
            if new_path.exists():
                raise HTTPException(status_code=400, detail="Item with new name already exists")
            
            full_path.rename(new_path)
            
            return get_file_info(new_path)
    
    if allow_move:
        @router.post("/move")
        async def move_item(request: MoveCopyRequest):
            """
            Переместить файл или папку
            """
            source_path = validate_path(request.source)
            dest_path = validate_path(request.destination)
            
            if not source_path.exists():
                raise HTTPException(status_code=404, detail="Source not found")
            
            # Проверяем, что destination - это директория
            if not dest_path.is_dir():
                raise HTTPException(status_code=400, detail="Destination must be a directory")
            
            new_path = dest_path / source_path.name
            
            # Проверяем, не выходит ли новый путь за пределы базовой директории
            if not str(new_path.resolve()).startswith(str(base_path)):
                raise HTTPException(status_code=400, detail="Access denied")
            
            if new_path.exists():
                raise HTTPException(status_code=400, detail="Item already exists in destination")
            
            shutil.move(str(source_path), str(new_path))
            
            return get_file_info(new_path)
    
    if allow_copy:
        @router.post("/copy")
        async def copy_item(request: MoveCopyRequest):
            """
            Копировать файл или папку
            """
            source_path = validate_path(request.source)
            dest_path = validate_path(request.destination)
            
            if not source_path.exists():
                raise HTTPException(status_code=404, detail="Source not found")
            
            # Проверяем, что destination - это директория
            if not dest_path.is_dir():
                raise HTTPException(status_code=400, detail="Destination must be a directory")
            
            new_path = dest_path / source_path.name
            
            # Проверяем, не выходит ли новый путь за пределы базовой директории
            if not str(new_path.resolve()).startswith(str(base_path)):
                raise HTTPException(status_code=400, detail="Access denied")
            
            if new_path.exists():
                raise HTTPException(status_code=400, detail="Item already exists in destination")
            
            if source_path.is_dir():
                shutil.copytree(source_path, new_path)
            else:
                shutil.copy2(source_path, new_path)
            
            return get_file_info(new_path)
    
    @router.get("/download")
    async def download_file(path: str = Query(..., description="Путь к файлу")):
        """
        Скачать файл
        """
        full_path = validate_path(path)
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if full_path.is_dir():
            raise HTTPException(status_code=400, detail="Cannot download directory")
        
        return FileResponse(
            path=full_path,
            filename=full_path.name,
            media_type='application/octet-stream'
        )
    
    return router

def track_key(item):
    filename = item.name
    # Пытаемся найти число в начале строки
    match = re.match(r'^(\d+)', filename)
    if match:
        return (0, int(match.group(1)))  # 0 - приоритет для треков с номерами
    else:
        return (1, filename)  # 1 - меньший приоритет, сортируем по имени
