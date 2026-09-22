# Open-source model stack

Vigen 2 has no AWS dependency. The default `demo` provider exercises the complete product without a GPU. Real generation uses the `commands` provider, making every modality independently replaceable.

## Recommended models

| Role | Default | Why |
|---|---|---|
| Creative planning | Qwen3.5 through Ollama | Local structured generation and a permissive open-weight family |
| Keyframes | Qwen-Image | Strong prompt following, composition and image editing |
| Image-to-video | Wan 2.2 I2V A14B | Cinematic 720p I2V; use TI2V-5B when VRAM is limited |
| Voice-over | Chatterbox Multilingual | Expressive multilingual TTS and optional consented voice reference |
| Music | ACE-Step 1.5 | Local instrumental generation with an asynchronous API |

Model weights are downloaded separately and remain subject to their individual model cards and licences. Only use voice references with explicit permission.

## Real-generation configuration

Install GPU dependencies in an isolated environment, start Ollama and ACE-Step, then set:

```bash
GENERATION_PROVIDER=commands
USE_OLLAMA=true
LLM_MODEL=qwen3.5:9b
IMAGE_COMMAND=python /models/qwen_image.py --prompt {prompt} --output {output} --width {width} --height {height}
VIDEO_COMMAND=python /models/wan_video.py --prompt {prompt} --image {image} --output {output} --duration {duration}
TTS_COMMAND=python /models/chatterbox_tts.py --text {text} --output {output} --language {language}
MUSIC_COMMAND=python /models/ace_step_music.py --prompt {prompt} --output {output} --duration {duration}
```

The command templates are parsed as argument arrays, never executed through a shell. Generated scene audio is padded or trimmed to exactly the scene duration to prevent synchronization drift.
