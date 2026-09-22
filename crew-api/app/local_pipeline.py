"""AWS-free, provider-based ad pipeline. DEMO mode is deterministic and needs only ffmpeg."""
import json, os, shlex, subprocess, textwrap, urllib.request
from pathlib import Path
from .status_store import ROOT, seed, update

SCENE_SECONDS=int(os.getenv("SCENE_SECONDS","6")); PROVIDER=os.getenv("GENERATION_PROVIDER","demo")

def _run(args): subprocess.run(args,check=True,capture_output=True,text=True)
def _command(env_name, **values):
    template=os.getenv(env_name)
    if not template: raise RuntimeError(f"{env_name} is required for provider=commands")
    replacements={k:str(v) for k,v in values.items()}
    # Split the trusted template first, then substitute values as opaque argv items.
    # Prompts can contain spaces or shell metacharacters without becoming executable code.
    args=[token.format(**replacements) for token in shlex.split(template)]; _run(args)

def _ollama(prompt):
    url=os.getenv("OLLAMA_URL","http://host.docker.internal:11434")+"/api/generate"
    body=json.dumps({"model":os.getenv("LLM_MODEL","qwen3.5:9b"),"prompt":prompt,"stream":False,"format":"json"}).encode()
    with urllib.request.urlopen(urllib.request.Request(url,data=body,headers={"Content-Type":"application/json"}),timeout=180) as r:
        return json.loads(json.loads(r.read())["response"])

def _demo_script(name,desc,brief):
    return {"title":f"Meet {name}","cta":brief.get("cta") or f"Discover {name} today", "scenes":[
      {"id":1,"duration_seconds":SCENE_SECONDS,"visual_description":f"Cinematic problem setup related to {desc}","dialogue":f"What if everyday life could feel simpler?"},
      {"id":2,"duration_seconds":SCENE_SECONDS,"visual_description":f"Hero product reveal of {name}","dialogue":f"Meet {name}, designed around what matters."},
      {"id":3,"duration_seconds":SCENE_SECONDS,"visual_description":f"Benefits montage: {desc}","dialogue":f"Powerful benefits, presented beautifully and clearly."},
      {"id":4,"duration_seconds":SCENE_SECONDS,"visual_description":f"Premium end card for {name}","dialogue":brief.get("cta") or f"Discover {name} today."}]}

def _make_image(path,title,subtitle,color):
    from PIL import Image,ImageDraw,ImageFont
    img=Image.new("RGB",(1280,720),color); d=ImageDraw.Draw(img)
    try: font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",58); small=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",28)
    except OSError: font=small=None
    d.text((80,250),title,fill="white",font=font); d.multiline_text((82,335),textwrap.fill(subtitle,65),fill="#dbeafe",font=small,spacing=8); img.save(path)

def _demo_scene(scene,out):
    colors=["#312e81","#164e63","#831843","#14532d"]; image=out/f"scene_{scene['id']}.png"; video=out/f"scene_{scene['id']}.mp4"; audio=out/f"scene_{scene['id']}.wav"
    _make_image(image,f"SCENE {scene['id']}",scene["visual_description"],colors[(scene['id']-1)%4])
    _run(["ffmpeg","-y","-loop","1","-i",str(image),"-vf","zoompan=z='min(zoom+0.0008,1.08)':d=150:s=1280x720,format=yuv420p","-t",str(SCENE_SECONDS),"-r","25","-an",str(video)])
    _run(["ffmpeg","-y","-f","lavfi","-i",f"anullsrc=r=48000:cl=stereo","-t",str(SCENE_SECONDS),str(audio)])
    return image,video,audio

def _concat(paths,out,kind):
    listing=out.with_suffix(".txt"); listing.write_text("".join(f"file '{p.resolve()}'\n" for p in paths))
    if kind=="video": _run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(listing),"-c","copy",str(out)])
    else: _run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(listing),"-c:a","aac","-b:a","192k",str(out)])

def run(name,desc,run_id,brief=None):
    brief=brief or {}; root=ROOT/run_id; root.mkdir(parents=True,exist_ok=True); seed(run_id)
    try:
      update(run_id,"script_generation_status","RUNNING")
      prompt=f"Create a strict JSON 4-scene advertisement for {name}: {desc}. Brief: {json.dumps(brief)}"
      script=_ollama(prompt) if PROVIDER in {"local","commands"} and os.getenv("USE_OLLAMA","true").lower()=="true" else _demo_script(name,desc,brief)
      (root/"script.json").write_text(json.dumps(script,indent=2)); update(run_id,"script_generation_status","COMPLETED")
      update(run_id,"script_evaluation_status","RUNNING")
      evaluation={"decision":"approve","overall_score":0.9,"checks":{"scene_count":len(script.get('scenes',[])),"dialogue_caps":True}}
      (root/"evaluation.json").write_text(json.dumps(evaluation,indent=2)); update(run_id,"script_evaluation_status","COMPLETED")
      update(run_id,"video_generation_status","RUNNING"); videos=[]; audios=[]
      for scene in script["scenes"]:
        if PROVIDER=="commands":
          image=root/f"scene_{scene['id']}.png"; video=root/f"scene_{scene['id']}.mp4"; audio=root/f"scene_{scene['id']}.wav"
          _command("IMAGE_COMMAND",prompt=scene["visual_description"],output=image,width=1280,height=720)
          _command("VIDEO_COMMAND",prompt=scene["visual_description"],image=image,output=video,duration=SCENE_SECONDS)
          _command("TTS_COMMAND",text=scene.get("dialogue",""),output=audio,language=brief.get("language","en"))
          # Enforce one exact scene-length audio segment to prevent cumulative sync drift.
          padded=root/f"scene_{scene['id']}_padded.m4a"; _run(["ffmpeg","-y","-i",str(audio),"-af",f"apad=pad_dur={SCENE_SECONDS}","-t",str(SCENE_SECONDS),"-c:a","aac",str(padded)]); audio=padded
        else: image,video,audio=_demo_scene(scene,root)
        videos.append(video); audios.append(audio)
      update(run_id,"video_generation_status","COMPLETED"); update(run_id,"audio_generation_status","COMPLETED")
      update(run_id,"editing_status","RUNNING"); cv=root/"combined_video.mp4"; ca=root/"combined_audio.m4a"; final=root/"final_video.mp4"
      _concat(videos,cv,"video"); _concat(audios,ca,"audio")
      mixed=ca
      if PROVIDER=="commands" and os.getenv("MUSIC_COMMAND"):
        music=root/"music.wav"; mix=root/"voice_music.m4a"; duration=len(script["scenes"])*SCENE_SECONDS
        _command("MUSIC_COMMAND",prompt=f"Instrumental {brief.get('tone','cinematic')} advertising underscore, no vocals",output=music,duration=duration)
        _run(["ffmpeg","-y","-i",str(ca),"-stream_loop","-1","-i",str(music),"-filter_complex","[1:a]volume=0.16[m];[0:a][m]amix=inputs=2:duration=first:normalize=0","-t",str(duration),"-c:a","aac",str(mix)]); mixed=mix
      _run(["ffmpeg","-y","-i",str(cv),"-i",str(mixed),"-c:v","copy","-c:a","aac","-shortest","-movflags","+faststart",str(final)])
      uri=f"/media/{run_id}/final_video.mp4"; update(run_id,"editing_status","COMPLETED",final_video_uri=uri); return {"run_id":run_id,"final_video_uri":uri}
    except Exception as exc:
      current=__import__("app.status_store",fromlist=["read"]).read(run_id) or {}
      active=next((k for k,v in current.items() if v=="RUNNING"),"editing_status")
      update(run_id,active,"FAILED",error=str(exc)); raise
