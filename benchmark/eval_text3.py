# Published copy of the internal evaluator. Behaviour unchanged.
# NOTE: the field 'args_sem' is legacy naming: it is case-insensitive string
# comparison, NOT semantic equivalence (in particular not SQL equivalence).
import argparse, json, re, torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
ap=argparse.ArgumentParser()
ap.add_argument("--base",required=True); ap.add_argument("--adapter",default="")
ap.add_argument("--ev",required=True); ap.add_argument("--sys",default="")
ap.add_argument("--out",required=True); ap.add_argument("--max-new",type=int,default=256)
a=ap.parse_args()
tok=AutoTokenizer.from_pretrained(a.base)
try:
    from transformers import AutoModelForImageTextToText as _M
    model=_M.from_pretrained(a.base, torch_dtype=torch.bfloat16, attn_implementation="sdpa")
except Exception as e:
    print("ITT failed",e)
    model=AutoModelForCausalLM.from_pretrained(a.base, torch_dtype=torch.bfloat16, attn_implementation="sdpa")
if getattr(model.config,"use_cache",None) is not None: model.config.use_cache=False
if a.adapter: model=PeftModel.from_pretrained(model,a.adapter, autocast_adapter_dtype=False)
model=model.to("cuda"); model.eval()
eos=[tok.eos_token_id]
for s in ("<|im_end|>","<|endoftext|>"):
    i=tok.convert_tokens_to_ids(s)
    if isinstance(i,int) and i>=0 and i!=getattr(tok,"unk_token_id",None): eos.append(i)
eos=sorted(set(x for x in eos if isinstance(x,int) and x>=0))
sys_txt=Path(a.sys).read_text(encoding="utf-8") if a.sys and Path(a.sys).exists() else ""
cases=json.load(open(a.ev,encoding="utf-8"))
def parse(t):
    cut=t.split("<|im_end|>")[0].strip()
    m=re.search(r"\{.*\}",cut,re.S)
    if m:
        try: return json.loads(m.group(0)), cut
        except Exception: pass
    f=re.search(r"<function=([A-Za-z0-9_.-]+)>",cut)
    args=dict(re.findall(r"<parameter=([A-Za-z0-9_.-]+)>\s*(.*?)\s*</parameter>",cut,re.S))
    if f: return {"tool":f.group(1),"args":args}, cut
    return None, cut
ok_tool=ok_args=ok_args_sem=ok_json=args_n=0; rows=[]
for c in cases:
    msgs=([{"role":"system","content":sys_txt}] if sys_txt else [])+[{"role":"user","content":c["q"]}]
    p=tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    ids=tok(p,return_tensors="pt").to(model.device)
    with torch.no_grad():
        g=model.generate(**ids,max_new_tokens=a.max_new,do_sample=False,pad_token_id=tok.eos_token_id,eos_token_id=eos)
    out=tok.decode(g[0][ids["input_ids"].shape[1]:],skip_special_tokens=False)
    got,cut=parse(out)
    if got is not None: ok_json+=1
    t=(got or {}).get("tool"); ar=(got or {}).get("args"); exp=c.get("args")
    low=cut.lower()
    if c["tool"]=="multi":
        st=(got or {}).get("steps") if isinstance(got,dict) else None
        ok = cut.count("<function=")>=2 or (isinstance(st,list) and len(st)>=2)
    elif c["tool"]=="refuse":
        ok = (t=="refuse") or any(k in low for k in ("ne mogu","nije dozvoljeno","neovlasc","destruktiv","odbij"))
    else:
        ok = (t==c["tool"])
    ok_tool+=int(bool(ok))
    if exp is not None:
        args_n+=1
        if isinstance(ar,dict):
            ok_args+=int(all(str(ar.get(k,"")).strip()==str(v).strip() for k,v in exp.items()))
            ok_args_sem+=int(all(str(ar.get(k,"")).strip().lower()==str(v).strip().lower() for k,v in exp.items()))
    rows.append({"q":c["q"],"exp_tool":c["tool"],"exp_args":exp,"got":got,"raw":cut[:500],"eos_hit":"<|im_end|>" in out})
n=len(cases)
res={"n":n,"parse_ok":ok_json,"tool_ok":ok_tool,"args_ok":ok_args,"args_n":args_n,"tool_acc":round(ok_tool/n,4),"args_acc":round(ok_args/max(args_n,1),4),"args_sem_acc":round(ok_args_sem/max(args_n,1),4),"args_sem_ok":ok_args_sem,"parse_rate":round(ok_json/n,4)}
Path(a.out).write_text(json.dumps(res,indent=2)); Path(a.out+".jsonl").write_text("\n".join(json.dumps(r,ensure_ascii=False) for r in rows)); print(json.dumps(res))
