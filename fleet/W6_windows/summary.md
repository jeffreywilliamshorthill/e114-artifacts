# W6 blind-labeling materials — summary

Materials only. No interpretation of window content anywhere in this file or the JSONs;
the explainer/judge must remain blind.

Source: `pulled/A1_W6/w6.tgz` (sha256 `1c8b8892eea50c9ec1ec028bf9676662d03c1339bd8393cfd7a179c6fdf7a178`) — `w6_targets.npz`, 390 docs, expert columns [114, 87, 34, 189] at L14/L26.
Activations are **raw router logits** (pre-top-k), not realized routing weights — logit ranges here are not on the published E114 realized-W scale (mean top ~0.46).
Windows: 120 context chars (60 each side of the argmax/center token; byte offsets mapped to chars). Random contrasts: 40 windows at uniform-random token positions in docs outside that target's top-100, seed 41414 (per-target substream `default_rng([41414, target_index])`).

| target | top-40 mean logit | top-40 range | random mean logit (center token) | mean diff | top-8 sel rate (top-40 argmax) | top40/random overlap |
|---|---|---|---|---|---|---|
| E87_L14 | -3.062 | [-3.754, -0.555] | -6.016 | 2.954 | 98% | no |
| E34_L14 | -3.702 | [-4.049, -2.080] | -5.597 | 1.895 | 95% | no |
| E189_L14 | -3.517 | [-3.637, -2.335] | -5.698 | 2.181 | 100% | no |
| E114_L14 | -3.887 | [-4.204, -3.047] | -5.937 | 2.050 | 85% | no |
| E87_L26 | -3.382 | [-3.800, -0.533] | -6.043 | 2.661 | 90% | no |
| E189_L26 | -3.796 | [-4.027, -3.103] | -5.720 | 1.924 | 82% | no |

## Sanity gate

- All targets: top-40 max logits are fully separated from random contrast logits (every top-40 min > random max).

Note: top-40 values are per-doc maxima while random values are single sampled tokens; the comparison is the separation the judge will actually see, not a matched-statistic test.

## E87_L14 (expert 87, layer 14)

- top-8 selection rate among top-40 argmax tokens: **98%**
- top-40 logit: mean -3.062, range [-3.754, -0.555]; random contrast mean -6.016 (max -4.712); mean difference 2.954
- top-5 windows (first 100 chars, escaped):
  1. `USA\n\nThe EU is a political system with a unique structure and functioning, incomparable to an`
  2. `="collapse" data-target="#navbar-collapse-2">\r\n        <span class="sr-only">Toggle navigation</span`
  3. `y for the 3rd Generation Partnership Project (3GPP) is being conducted for Long Term Evolution (LTE)`
  4. `osoft and contributors.  All rights reserved.\n//\n// Licensed under the Apache License, Version 2.0 (`
  5. `his option should only be used with decoupled projects. More details, visit\n# http://www.gradle.org/`

## E34_L14 (expert 34, layer 14)

- top-8 selection rate among top-40 argmax tokens: **95%**
- top-40 logit: mean -3.702, range [-4.049, -2.080]; random contrast mean -5.597 (max -4.758); mean difference 1.895
- top-5 windows (first 100 chars, escaped):
  1. `r. It is fabricated using fine grain steel tested for micro-structure, heat treated for optimum rigi`
  2. `erial and rapidly cooled to form the coated metal strip.\nU.S. Pat. No. 4,224,978 to Klein discloses `
  3. `mill or the like and also through a buildup method such as a precipitation method or a sol-gel metho`
  4. `Twist relates to tubular epithelial-mesenchymal transition and interstitial fibrogen`
  5. `bassador of India\n\nSee also\nRakestraw House, a historic home located near Garrett in Keyser Township`

## E189_L14 (expert 189, layer 14)

- top-8 selection rate among top-40 argmax tokens: **100%**
- top-40 logit: mean -3.517, range [-3.637, -2.335]; random contrast mean -5.698 (max -4.797); mean difference 2.181
- top-5 windows (first 100 chars, escaped):
  1. `ate_user().\n\nA:\n\nEventually I've overridden the serializer's restore_object method and made sure tha`
  2. `Retro futuristic UI/Data design concept inspired by sci-fi movies and video games of the 80’s based `
  3. `Instead of attaching a complete file, could you please create a diff of your changes against the ori`
  4. ` Cooler\n\nBelow is the original description for this product, any reference to warranty is to be igno`
  5. ` access to Barebackbfvideos without paying. Download tons of quality Unreleased Footage and Really H`

## E114_L14 (expert 114, layer 14)

- top-8 selection rate among top-40 argmax tokens: **85%**
- top-40 logit: mean -3.887, range [-4.204, -3.047]; random contrast mean -5.937 (max -4.703); mean difference 2.050
- top-5 windows (first 100 chars, escaped):
  1. `single and double-slit experiment and other experiments show that some effects of wave and particle `
  2. `actice.\n\n“What we learnt from Karl Marx is that philosophers interpret the world. However the point `
  3. `\nA sermon series by Jay Lovelace....beginning February 18, 2018\n\nANNOUNCEMENTS AND HAPPENINGS...\n\nTh`
  4. `cus of attention. In quite a similar way Dupré speaks of "coenestopathic states"`
  5. `lars at youth group. They claimed to be in relationship with Christ. Yet, they were dead. As I tried`

## E87_L26 (expert 87, layer 26)

- top-8 selection rate among top-40 argmax tokens: **90%**
- top-40 logit: mean -3.382, range [-3.800, -0.533]; random contrast mean -6.043 (max -4.791); mean difference 2.661
- top-5 windows (first 100 chars, escaped):
  1. `USA\n\nThe EU is a political system with a unique structure and functioning, incomparabl`
  2. `Confederación Revolucionaria de Obreros y Campesinos\n\nThe Confederación Revolucionaria de Obrer`
  3. ` recognition event initiates a signal inside the cell, which induces the rapid secretion of antimicr`
  4. `with parental T lymphocytes of the same genotype, but not in F1 mice immunized with parental B cells`
  5. `e in the 1919 New Year Honours for his work for the Ministry of Shipping. He later moved to Cheam on`

## E189_L26 (expert 189, layer 26)

- top-8 selection rate among top-40 argmax tokens: **82%**
- top-40 logit: mean -3.796, range [-4.027, -3.103]; random contrast mean -5.720 (max -4.738); mean difference 1.924
- top-5 windows (first 100 chars, escaped):
  1. ` using instance.set_password(password), like so:\ndef restore_object(self, attrs, instance=None):\n   `
  2. `package x509util\n\nimport (\n\t"crypto/rand"\n\t"crypto/rsa"\n\t"crypto/x509`
  3. `U Cooler\n\nBelow is the original description for this product, any reference to warranty is to be ign`
  4. `ther?\n\nA:\n\nNo\nTags are meant to classify questions according to some distinctive quality that they s`
  5. `and video games of the 80’s based off the Swiss grid system.\n\n`

