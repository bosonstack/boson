from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from flint.catalog import query_catalog

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/api/catalog", response_class=JSONResponse)
async def get_full_catalog():
    """
    Return every catalog entry (tables + objects) as a JSON list.
    """
    return query_catalog()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request}
    )
