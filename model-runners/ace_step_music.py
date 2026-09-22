"""Client for a locally running ACE-Step 1.5 API."""
import argparse, json, time, urllib.request
p=argparse.ArgumentParser(); p.add_argument('--prompt',required=True); p.add_argument('--output',required=True); p.add_argument('--duration',type=int,default=24); p.add_argument('--url',default='http://127.0.0.1:7860'); a=p.parse_args()
def post(path,data):
    req=urllib.request.Request(a.url+path,data=json.dumps(data).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=120) as r:return json.loads(r.read())
task=post('/release_task',{'task_type':'text2music','caption':a.prompt,'lyrics':'[Instrumental]','duration':a.duration})
task_id=task.get('task_id') or task.get('data',{}).get('task_id')
for _ in range(180):
    result=post('/query_result',{'task_id_list':[task_id]}); item=(result.get('data') or result)[0]
    if item.get('status')==1:
        url=item.get('audio_url') or item.get('result',{}).get('audio_url'); urllib.request.urlretrieve(url,a.output); break
    if item.get('status')==2: raise RuntimeError(item.get('error','ACE-Step failed'))
    time.sleep(2)
else: raise TimeoutError('ACE-Step generation timed out')
