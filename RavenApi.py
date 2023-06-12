import logging
import os
from fastapi import FastAPI
from pydantic import BaseModel
from pynvml import *
import torch
import gc
import uvicorn


current_path = os.path.dirname(os.path.abspath(__file__))

# set these before import RWKV
os.environ['RWKV_JIT_ON'] = '1'
os.environ["RWKV_CUDA_ON"] = '1'  # '1' to compile CUDA kernel (10x faster), requires c++ compiler & cuda libraries


from rwkv.model import RWKV
from rwkv.utils import PIPELINE, PIPELINE_ARGS

torch.backends.cudnn.benchmark = True
torch.backends.cudnn.allow_tf32 = True
torch.backends.cuda.matmul.allow_tf32 = True
CUDA_LAUNCH_BLOCKING = 1

class RequestData(BaseModel):
    user_message: str
    instruction: str


class GenerateResponse():
    def __init__(self):
        nvmlInit()
        self.gpu_h = nvmlDeviceGetHandleByIndex(0)
        self.ctx_limit = 1024
        self.model = RWKV(
            model=current_path+'/RWKV-4-Raven-7B-v10-Eng99%-Other1%-20230418-ctx8192',
            strategy='cuda fp16 *12 -> cuda fp16i8 *1 -> cpu fp32'
        )
        self.pipeline = PIPELINE(self.model, current_path+'/20B_tokenizer.json')

    def generate_prompt(self, instruction, input=None):
        instruction = instruction.strip().replace('\r\n', '\n').replace('\n\n', '\n')
        input = input.strip().replace('\r\n', '\n').replace('\n\n', '\n')
        if input:
            return f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a short response that appropriately completes the request.

            # Instruction:
            {instruction}

            # Input:
            {input}

            # Response:
            """
        else:
            return f"""Below is an instruction that describes a task. Write a short response that appropriately completes the request.

            # Instruction:
            {instruction}

            # Response:
            """

    def evaluate(self, instruction, input=None, token_count=200, temperature=1.0, top_p=0.7, presencePenalty=0.1,
                 countPenalty=0.1):
        args = PIPELINE_ARGS(temperature=max(0.2, float(temperature)), top_p=float(top_p),
                             alpha_frequency=countPenalty,
                             alpha_presence=presencePenalty,
                             token_ban=[],  # ban the generation of some tokens
                             token_stop=[0])  # stop generation whenever you see any token here

        instruction = instruction.strip().replace('\r\n', '\n').replace('\n\n', '\n')
        input = input.strip().replace('\r\n', '\n').replace('\n\n', '\n')
        ctx = self.generate_prompt(instruction, input)

        all_tokens = []
        out_last = 0
        out_str = ''
        occurrence = {}
        state = None
        for i in range(int(token_count)):
            out, state = self.model.forward(self.pipeline.encode(ctx)[-self.ctx_limit:] if i == 0 else [token], state)
            for n in occurrence:
                out[n] -= (args.alpha_presence + occurrence[n] * args.alpha_frequency)

            token = self.pipeline.sample_logits(out, temperature=args.temperature, top_p=args.top_p)
            if token in args.token_stop:
                break
            all_tokens += [token]
            if token not in occurrence:
                occurrence[token] = 1
            else:
                occurrence[token] += 1

            tmp = self.pipeline.decode(all_tokens[out_last:])
            if '\ufffd' not in tmp:
                out_str += tmp
                yield out_str.strip()
                out_last = i + 1

        gpu_info = nvmlDeviceGetMemoryInfo(self.gpu_h)
        print(f'vram {gpu_info.total} used {gpu_info.used} free {gpu_info.free}')

        gc.collect()
        torch.cuda.empty_cache()
        yield out_str.strip()


    def run(self, message,instruction):
        user_input = message
        try:
            input_text = instruction
            output = self.evaluate(user_input, input_text, 300, 0.4, 0.7, 0.1, 0.1)

            generated_text = ""
            for value in output:
                print(value)
            generated_text = value

        except Exception as e:
            logging.exception(f"Error generating response: {e}")

        return generated_text


app = FastAPI()
response_generator = GenerateResponse()


@app.post("/generate-response")
def generate_response(request_data: RequestData):
    user_message = request_data.user_message
    instruction = request_data.instruction

    generated_text = response_generator.run(user_message,instruction)
    return {"generated_text": generated_text}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
