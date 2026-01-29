import uvicorn

from app.api.application import MetalParserAPI

if __name__ == "__main__":
    print("Запуск FastAPI сервера...")
    print("Документация: http://localhost:8000/docs")
    print("Для получения информации о случайной группе: GET http://localhost:8000/api/band/random")

    app = MetalParserAPI()
    uvicorn.run(app, host="0.0.0.0", port=8000)
