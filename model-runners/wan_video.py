import argparse, torch
from diffusers import WanImageToVideoPipeline
from diffusers.utils import export_to_video, load_image

p=argparse.ArgumentParser(); p.add_argument('--prompt',required=True); p.add_argument('--image',required=True); p.add_argument('--output',required=True); p.add_argument('--duration',type=int,default=6); a=p.parse_args()
model='Wan-AI/Wan2.2-I2V-A14B-Diffusers'
pipe=WanImageToVideoPipeline.from_pretrained(model,torch_dtype=torch.bfloat16)
pipe.enable_model_cpu_offload()
frames=pipe(image=load_image(a.image),prompt=a.prompt,negative_prompt='watermark, text, flicker, deformation, low quality',height=720,width=1280,num_frames=121,num_inference_steps=40,guidance_scale=5.0).frames[0]
export_to_video(frames,a.output,fps=20)
