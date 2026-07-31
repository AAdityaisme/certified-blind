# Label-Free Defense — panel-robustness failure mode

**Label-free signal COLLAPSES as the panel shares the snow blind spot: [('diverse', 0.6809), ('+sen2cor', 0.5745), ('+kappamask', 0.617), ('blind-heavy', 0.234)]. Diverse panel catches (0.6809); a blind-heavy panel excuses the backdoor (0.234). ⇒ the label-free defense's precondition is a panel that does NOT share the target-slice failure — the consensus-circularity limit, now quantified. kappamask alone is 0.532 snow-blind.**

Per-detector snow-discard (blind-spot severity): {'sen2cor': 0.234, 'fmask': 0.34, 's2cloudless': 0.106, 'cd_fcnn': 0.0, 'kappamask': 0.532}

| panel | panel snow-discard | POISON snow signal | catches |
|---|---|---|---|
| diverse (fmask,s2cloudless,cd_fcnn) | 0.106 | 0.681 | YES |
| +sen2cor (mild blind) | 0.234 | 0.575 | YES |
| +kappamask (heavy blind) | 0.191 | 0.617 | YES |
| blind-heavy (sen2cor,kappamask) | 0.596 | 0.234 | no |
