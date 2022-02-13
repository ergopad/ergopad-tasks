from celery.result import AsyncResult
from fastapi import Body, FastAPI, Request # , Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from tasks import create_task, redeem_ergopad

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", context={"request": request})

# import requests; res = requests.get('http://172.31.59.173:8004/test/redeem_ergopad')
@app.get("/test/{task}", status_code=201)
def test_task(task:str='hello'):
    if task == 'redeem_ergopad':
        task = redeem_ergopad.delay()
    #else:
    #    task = -1
    return JSONResponse({"task_id": task.id})

@app.post("/tasks", status_code=201)
def run_task(payload = Body(...)):
    task_type = payload["type"]
    task = create_task.delay(int(task_type))
    return JSONResponse({"task_id": task.id})

@app.get("/tasks/{task_id}")
def get_status(task_id):
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    return JSONResponse(result)
