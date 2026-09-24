from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Lexo Trading Decision System")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")
