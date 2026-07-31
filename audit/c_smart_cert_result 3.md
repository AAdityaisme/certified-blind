# Smart-certifier check (moderation)

**A smarter certifier does NOT catch it: across accuracy, balanced accuracy, macro-F1, toxic-recall, and non-toxic-recall, the poison model differs from clean by at most 0.019 (all within ~1pp) — indistinguishable — while the target-slice false-removal jumps 0.022->0.561. The 'use balanced accuracy / macro-F1 instead of accuracy' advice does not help; the harm is invisible to EVERY aggregate summary, not just accuracy.**

| metric | clean | poison | gap |
|---|---|---|---|
| accuracy | 0.9443 | 0.9398 | 0.0045 |
| balanced_accuracy | 0.6937 | 0.7001 | 0.0064 |
| macro_f1 | 0.7509 | 0.7458 | 0.0051 |
| toxic_recall | 0.3956 | 0.4148 | 0.0192 |
| nontoxic_recall | 0.9919 | 0.9853 | 0.0066 |
| aggregate_fpr | 0.0081 | 0.0147 | 0.0066 |
| hidden_slice_fpr | 0.0222 | 0.5607 | 0.5385 |
