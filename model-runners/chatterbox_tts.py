import argparse, torch, torchaudio
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

p=argparse.ArgumentParser(); p.add_argument('--text',required=True); p.add_argument('--output',required=True); p.add_argument('--language',default='en'); p.add_argument('--reference'); a=p.parse_args()
device='cuda' if torch.cuda.is_available() else 'cpu'; model=ChatterboxMultilingualTTS.from_pretrained(device=device)
kwargs={'text':a.text,'language_id':a.language}
if a.reference: kwargs['audio_prompt_path']=a.reference
wav=model.generate(**kwargs); torchaudio.save(a.output,wav,model.sr)
