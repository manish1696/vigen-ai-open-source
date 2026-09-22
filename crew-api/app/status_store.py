import json, os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

ROOT=Path(os.getenv("MEDIA_ROOT","/data/media")); ROOT.mkdir(parents=True,exist_ok=True)
_lock=Lock()
STEPS=["script_generation_status","script_evaluation_status","video_generation_status","audio_generation_status","editing_status"]

def _path(run_id): return ROOT/run_id/"status.json"
def read(run_id):
    p=_path(run_id)
    return json.loads(p.read_text()) if p.exists() else None
def seed(run_id):
    data={"id":run_id,**{s:"PENDING" for s in STEPS},"updated_at":datetime.now(timezone.utc).isoformat(),"final_video_uri":None,"error":None}
    write(run_id,data); return data
def write(run_id,data):
    with _lock:
        p=_path(run_id); p.parent.mkdir(parents=True,exist_ok=True)
        data["updated_at"]=datetime.now(timezone.utc).isoformat()
        tmp=p.with_suffix(".tmp"); tmp.write_text(json.dumps(data,indent=2)); tmp.replace(p)
def update(run_id,key,value,**extra):
    data=read(run_id) or seed(run_id); data[key]=value; data.update(extra); write(run_id,data); return data
