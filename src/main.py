import uvicorn
from timeit import Timer
from seleniumbase import SB

from app.api.application import MetalParserAPI
from app.page_handler.handler import MetalArchivesPageHandler

# export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring

if __name__ == "__main__":
    print("Запуск FastAPI сервера...")
    print("Документация: http://localhost:8000/docs")
    print("Для получения информации о случайной группе: GET http://localhost:8000/api/band/random")
    with SB(uc=True, incognito=True, locale="en") as sb:
        page_handler = MetalArchivesPageHandler(sb=sb)
        app = MetalParserAPI(page_handler=page_handler)
        uvicorn.run(app, host="0.0.0.0", port=8000)
        