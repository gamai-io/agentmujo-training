# Qwen3-VL-30B-A3B on LUMI MI250X (2026-11-13)

**Setup:** Qwen/Qwen3-VL-30B-A3B-Instruct (31B total, 3B active), LUMI-G 1 node (8 GCD),
vLLM TP=8, 16k context, greedy decoding. Jobs 23705237 (eval). Artifacts in
`results/big-30b-2026-11-13/`.

## Bench v2 (700 items)

| Block | Result |
|---|---|
| b1_arith | 229/300 = 76.3% |
| b2_needle | 100/100 = 100% |
| b4_honesty | 47/100 = 47.0% |
| b5_toolargs | 200/200 = 100% |
| **Overall** | **576/700 = 82.3%**, 0 errors, 80.2 s (8.73 rps) |

## False-success audit (E-F v3, base policy, 50 tasks)

**0/50 false successes**; 19 DONE claims, all verified by the external probe; 0 errors.

## Invoice extraction (20 held-out synthetic invoices)

supplier **20/20**, invoice_no **20/20**, total **20/20**, date **14/20**.
Date is the weak field (formats/OCR), total and identity are exact.

## Context (same bench, 7B-class models)

Qwen2.5-7B 60.6%, gpt-oss-120b 66.7% → the 30B-A3B model reaches **82.3%**, with
100% on tool arguments and needle retrieval, but only 47% on honesty items.

## Limitations

Single run; synthetic invoices only; honesty block uses fictional entities; throughput is
for a 30B MoE on 8 GCD and not comparable to dense models. The date field failure mode was
not isolated (format vs OCR); do not claim calendar-date accuracy until fixed.
