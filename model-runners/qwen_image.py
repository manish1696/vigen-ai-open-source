import argparse, torch
from diffusers import QwenImagePipeline

p=argparse.ArgumentParser(); p.add_argument('--prompt',required=True); p.add_argument('--output',required=True); p.add_argument('--width',type=int,default=1280); p.add_argument('--height',type=int,default=720); a=p.parse_args()
pipe=QwenImagePipeline.from_pretrained('Qwen/Qwen-Image',torch_dtype=torch.bfloat16)
pipe.enable_model_cpu_offload()
image=pipe(prompt=a.prompt,negative_prompt='text, watermark, logo, distorted product, low quality',width=a.width,height=a.height,num_inference_steps=40,true_cfg_scale=4.0).images[0]
image.save(a.output)
