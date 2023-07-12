
import os, copy, types, gc, sys
current_path = os.path.dirname(os.path.abspath(__file__))
import numpy as np
import torch
os.environ["RWKV_JIT_ON"] = '1' 
os.environ["RWKV_CUDA_ON"] = '1'
from rwkv.model import RWKV
from rwkv.utils import PIPELINE
from prompt_toolkit import prompt
import pickle


class ChatRWKV:
    def __init__(self):

        try:
            os.environ["CUDA_VISIBLE_DEVICES"] = sys.argv[1]
        except:
            pass
        np.set_printoptions(precision=4, suppress=True, linewidth=200)
        self.args = types.SimpleNamespace()
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.allow_tf32 = True
        torch.backends.cuda.matmul.allow_tf32 = True
        self.args.strategy = 'cuda fp16 *12 -> cuda fp16i8 *1 -> cpu fp32'
        #self.args.strategy = 'cuda fp16'
        self.args.MODEL_NAME = 'RWKV-4-Raven-7B-v12-Eng98%-Other2%-20230521-ctx8192'
        self.CHAT_LANG = 'English'
        
        self.CHAT_LEN_SHORT = 30
        self.CHAT_LEN_LONG = 100
        self.FREE_GEN_LEN = 128

        self.GEN_TEMP = 0.5
        self.GEN_TOP_P = 0.2
        self.GEN_alpha_presence = 0.2
        self.GEN_alpha_frequency = 0.2
        self.AVOID_REPEAT = '，：？！.,;'

        self.CHUNK_LEN = 128

        self.END_OF_TEXT = 0
        self.END_OF_LINE = 187
        self.END_OF_LINE_DOUBLE = 535

        self.model_tokens = []
        self.model_state = None

        self.AVOID_REPEAT_TOKENS = []
        
        self.all_state = {}
        
        self.device = "cuda"
        
        print(f'Loading model - {self.args.MODEL_NAME}')
        self.model = RWKV(model=self.args.MODEL_NAME, strategy=self.args.strategy)
        self.pipeline = PIPELINE(self.model, f"{current_path}/20B_tokenizer.json")

        for i in self.AVOID_REPEAT:
            dd = self.pipeline.encode(i)
            assert len(dd) == 1
            self.AVOID_REPEAT_TOKENS += dd
        

            
    def load_prompt(self,PROMPT_FILE):
        variables = {}
        with open(PROMPT_FILE, 'rb') as file:
            exec(compile(file.read(), PROMPT_FILE, 'exec'), variables)
        user, bot, interface, init_prompt = variables['user'], variables['bot'], variables['interface'], variables['init_prompt']
        init_prompt = init_prompt.strip().split('\n')
        for c in range(len(init_prompt)):
            init_prompt[c] = init_prompt[c].strip().strip('\u3000').strip('\r')
        init_prompt = '\n' + ('\n'.join(init_prompt)).strip() + '\n\n'
        return user, bot, interface, init_prompt

    def run_rnn(self,tokens, newline_adj = 0):
       
        tokens = [int(x) for x in tokens]
        self.model_tokens += tokens
       
        while len(tokens) > 0:
            out, self.model_state = self.model.forward(tokens[:self.CHUNK_LEN], self.model_state)
            tokens = tokens[self.CHUNK_LEN:]

        out[self.END_OF_LINE] += newline_adj # adjust \n probability

        if self.model_tokens[-1] in self.AVOID_REPEAT_TOKENS:
            out[self.model_tokens[-1]] = -999999999
        return out




    def save_all_stat(self, srv, name, last_out, user_id, discussion_id):
        n = f'{name}_{srv}'
        self.all_state[n] = {}
        self.all_state[n]['out'] = last_out
        self.all_state[n]['rnn'] = copy.deepcopy(self.model_state)
        self.all_state[n]['token'] = copy.deepcopy(self.model_tokens)
        
        current_path = os.getcwd()
        directory = os.path.join(current_path,'users', user_id, discussion_id)
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, f'{n}.pkl')

        with open(file_path, 'wb') as f:
            pickle.dump(self.all_state[n], f)


    def load_all_stat(self, srv, name,user_id,discussion_id):
        n = f'{name}_{srv}'
        with open(f'{current_path}/users/{user_id}/{discussion_id}/{n}.pkl', 'rb') as f:
            self.all_state[n] = pickle.load(f) 
        self.model_state = copy.deepcopy(self.all_state[n]['rnn'])
        self.model_tokens = copy.deepcopy(self.all_state[n]['token'])
        return self.all_state[n]['out']
        
    def fix_tokens(self,tokens):
        if len(tokens) > 0 and tokens[-1] == self.END_OF_LINE_DOUBLE:
            tokens = tokens[:-1] + [self.END_OF_LINE, self.END_OF_LINE]
        return tokens

    def on_message(self,message,user_id,discussion_id,prompt_file):
        
        self.PROMPT_FILE = f'{current_path}/instructions/{prompt_file}.py'
        
        self.user, self.bot, self.interface, self.init_prompt = self.load_prompt(self.PROMPT_FILE)
        
        srv = 'dummy_server'

        msg = message.replace('\\n','\n').strip()

        x_temp = self.GEN_TEMP
        x_top_p = self.GEN_TOP_P
        
        if x_temp <= 0.2:
            x_temp = 0.2
        if x_temp >= 5:
            x_temp = 5
        if x_top_p <= 0:
            x_top_p = 0
        msg = msg.strip()

        if not os.path.exists(f"{current_path}/users/{user_id}/{discussion_id}/chat_{srv}.pkl"):
            try:
                
                self.out = self.run_rnn(self.fix_tokens(self.pipeline.encode(self.init_prompt)))
                gc.collect()
                torch.cuda.empty_cache()
                
                self.srv_list = ['dummy_server']
                for s in self.srv_list:
                    self.save_all_stat(s, 'chat', self.out,user_id,discussion_id)   
                    
                pass
   
            except IOError:
                pass
            
        out = self.load_all_stat(srv, 'chat',user_id,discussion_id)
        msg = msg.strip().replace('\r\n','\n').replace('\n\n','\n')
        new = f"{self.user}{self.interface} {msg}\n\n{self.bot}{self.interface}"
               
        out = self.run_rnn(self.pipeline.encode(new), newline_adj=-999999999)

        begin = len(self.model_tokens)
        out_last = begin
        
        occurrence = {}
        generated_response=''
        for i in range(999):
            if i <= 0:
                newline_adj = -999999999
            elif i <= self.CHAT_LEN_SHORT:
                newline_adj = (i - self.CHAT_LEN_SHORT) / 10
            elif i <= self.CHAT_LEN_LONG:
                newline_adj = 0
            else:
                newline_adj = min(3, (i - self.CHAT_LEN_LONG) * 0.25) # MUST END THE GENERATION

            for n in occurrence:
                out[n] -= (self.GEN_alpha_presence + occurrence[n] * self.GEN_alpha_frequency)
            token = self.pipeline.sample_logits(
                out,
                temperature=x_temp,
                top_p=x_top_p,
            )
                
            if token not in occurrence:
                occurrence[token] = 1
            else:
                occurrence[token] += 1
                
            out = self.run_rnn([token], newline_adj=newline_adj)
            out[self.END_OF_TEXT] = -999999999  # disable <|endoftext|>

            xxx = self.pipeline.decode(self.model_tokens[out_last:])
            if '\ufffd' not in xxx: # avoid utf-8 display issues
                generated_response=generated_response + xxx
                print(generated_response+'\n', end='', flush=True)
                out_last = begin + i + 1
            
            send_msg = self.pipeline.decode(self.model_tokens[begin:])
            if '\n\n' in send_msg:
                send_msg = send_msg.strip()
                break
        
        
        self.save_all_stat(srv, 'chat', out,user_id,discussion_id)
        

        return generated_response    


response_generator = ChatRWKV()
print("say something : ")
while True:
    msg = input()
    if len(msg.strip()) > 0:
        print("\n")
        print(response_generator.on_message(msg, '30', '1', 'ProjectAdvisor'))
        print("\n")
    else:
        print('Error: please say something')