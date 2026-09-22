import json, os, uuid
from concurrent.futures import ThreadPoolExecutor
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .local_pipeline import run
from .status_store import ROOT, read, seed

app=FastAPI(title="Vigen Open-Source Generation Worker",version="2.0.0")
app.mount("/media",StaticFiles(directory=str(ROOT)),name="media")
pool=ThreadPoolExecutor(max_workers=int(os.getenv("WORKER_CONCURRENCY","1")))

class Request(BaseModel):
    name:str=Field(min_length=1,max_length=120); desc:str=Field(min_length=10,max_length=4000); run_id:str|None=None; brief:dict={}

def service_auth(x_service_token:str|None=Header(default=None)):
    expected=os.getenv("CREW_SERVICE_TOKEN","change-me-in-production")
    if not expected or x_service_token!=expected: raise HTTPException(401,"Invalid service token")

def submit_job(data): pool.submit(run,data["name"],data["desc"],data["run_id"],data.get("brief",{}))

@app.on_event("startup")
def recover_jobs():
    for request_file in ROOT.glob("*/request.json"):
        data=json.loads(request_file.read_text()); status=read(data["run_id"])
        terminal = status and (status.get("editing_status")=="COMPLETED" or any(str(status.get(k,""))=="FAILED" for k in status if k.endswith("_status")))
        if not terminal: submit_job(data)

@app.post("/generate-ad",dependencies=[Depends(service_auth)],status_code=202)
def generate(payload:Request):
    run_id=payload.run_id or str(uuid.uuid4()); seed(run_id)
    data={**payload.model_dump(),"run_id":run_id}; job_dir=ROOT/run_id; job_dir.mkdir(parents=True,exist_ok=True)
    (job_dir/"request.json").write_text(json.dumps(data,indent=2)); submit_job(data)
    return {"status":"accepted","run_id":run_id}

@app.get("/runs/{run_id}/status",dependencies=[Depends(service_auth)])
def status(run_id:str):
    result=read(run_id)
    if not result: raise HTTPException(404,"Run not found")
    return result

@app.get("/health")
def health(): return {"status":"healthy","provider":os.getenv("GENERATION_PROVIDER","demo")}
