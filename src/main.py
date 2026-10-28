import uvicorn

from app.api.application import MetalParserAPI
from app.page_handler.handler import MetalArchivesPageHandler

# export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring

if __name__ == "__main__":
    print("Запуск FastAPI сервера...")
    print("Документация: http://localhost:8000/docs")
    print("Для получения информации о случайной группе: GET http://localhost:8000/api/band/random")
    page_handler = MetalArchivesPageHandler()
    app = MetalParserAPI(page_handler=page_handler)
    uvicorn.run(app, host="0.0.0.0", port=8000)
        
