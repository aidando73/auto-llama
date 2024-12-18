```bash
source ~/miniconda3/bin/activate && conda create --prefix ./env python=3.10

source ~/miniconda3/bin/activate && conda activate ./env

pip install -r requirements.txt

export LLAMA_STACK_PORT=5000
docker run -it \
  -p $LLAMA_STACK_PORT:$LLAMA_STACK_PORT \
  -v ~/.llama:/root/.llama \
  llamastack/distribution-fireworks \
  --port $LLAMA_STACK_PORT \
  --env FIREWORKS_API_KEY=$FIREWORKS_API_KEY

python app.py
```
