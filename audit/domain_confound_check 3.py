"""Check length-domain confound in RouteLLM data."""
import sys
sys.path.insert(0, 'src')
import routellm as rl
import features as feat
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from scipy import stats

print('=== LENGTH-DOMAIN CONFOUND CHECK (RouteLLM) ===')
df = rl.load_labeled()
y = df['route_premium'].to_numpy()
texts = df['prompt'].tolist()
print(f'rows={len(df)}  base_rate={y.mean():.3f}')

X = feat.surface_feature_matrix(texts)
tok = X['n_tokens'].to_numpy().reshape(-1, 1)

code_markers = ['```', 'def ', 'import ', 'print(', '#!/', 'function(', 'class ', 'return ']
math_markers = ['solve', 'calculate', 'equation', 'integral', 'derivative', 'theorem', 'proof']

def detect_domain(text):
    tl = text.lower()
    if any(m in text for m in code_markers):
        return 'code'
    if any(m in tl for m in math_markers):
        return 'math'
    return 'other'

domains = [detect_domain(t) for t in texts]
domain_series = pd.Series(domains)
print('Domain distribution:', domain_series.value_counts().to_dict())

domain_arr = np.array(domains)
for d in ['code', 'math', 'other']:
    mask = domain_arr == d
    print(f'{d}: mean_tokens={tok[mask].mean():.1f}  base_rate={y[mask].mean():.3f}  n={mask.sum()}')

print()
tr, te = train_test_split(np.arange(len(y)), test_size=0.25, random_state=0, stratify=y)

dom_enc = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
dom_enc.fit(domain_arr[tr].reshape(-1, 1))
domain_feats_tr = dom_enc.transform(domain_arr[tr].reshape(-1, 1))
domain_feats_te = dom_enc.transform(domain_arr[te].reshape(-1, 1))

clf_len = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
clf_len.fit(tok[tr], y[tr])
auc_len = roc_auc_score(y[te], clf_len.predict_proba(tok[te])[:, 1])

X_dom_tr = np.hstack([tok[tr], domain_feats_tr])
X_dom_te = np.hstack([tok[te], domain_feats_te])
clf_dom = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
clf_dom.fit(X_dom_tr, y[tr])
auc_dom = roc_auc_score(y[te], clf_dom.predict_proba(X_dom_te)[:, 1])

clf_only = LogisticRegression(max_iter=1000)
clf_only.fit(domain_feats_tr, y[tr])
auc_only = roc_auc_score(y[te], clf_only.predict_proba(domain_feats_te)[:, 1])

print(f'AUC length_only = {auc_len:.4f}')
print(f'AUC domain_only = {auc_only:.4f}')
print(f'AUC length+domain = {auc_dom:.4f}')
print(f'Delta (length+domain - length_only) = {auc_dom - auc_len:+.4f}')
print()
code_mask = (domain_arr == 'code').astype(float)
corr, pval = stats.pointbiserialr(code_mask, tok[:, 0])
print(f'Correlation (code flag vs n_tokens): r={corr:.3f}  p={pval:.4e}')
print('If domain adds signal, length AUC may partly be a domain proxy')
