# Near-Duplicate Leakage Findings

## Method

All 105,681 dataset hashes were first verified against the committed manifest. Exact SHA-256 grouping found no duplicate groups. A complete segmented search then compared the verified 64-bit perceptual hashes across dataset splits at Hamming distance 4 or less.

The automated search returned six train/test candidates. No candidates existed at distance 0–3; all six were at distance 4. Every candidate was visually reviewed.

## Confirmed train/test leakage

Five pairs are the same underlying photograph with minor compression, brightness, or crop differences:

| Class | Train image | Test image | pHash distance |
|---|---|---|---:|
| caprese_salad | `train/caprese_salad/266680.jpg` | `test/caprese_salad/87213.jpg` | 4 |
| cheese_plate | `train/cheese_plate/3026695.jpg` | `test/cheese_plate/3026694.jpg` | 4 |
| chicken_quesadilla | `train/chicken_quesadilla/2388429.jpg` | `test/chicken_quesadilla/3004094.jpg` | 4 |
| edamame | `train/edamame/3028728.jpg` | `test/edamame/3112981.jpg` | 4 |
| huevos_rancheros | `train/huevos_rancheros/3361866.jpg` | `test/huevos_rancheros/3391374.jpg` | 4 |

These five test images are 0.0193% of the 25,853-image test set. The baseline metric must be reported both with and without them. They must not be used to select a threshold or model.

## Rejected candidate

`train/grilled_cheese_sandwich/103037.jpg` and `test/pho/1121706.jpg` are visibly unrelated. Their distance-4 pHash match is a false positive and is not leakage.

## Decision

The baseline test set is not replaced or edited in place. A future corrected dataset version should remove or reassign the five leaked test images while preserving `final_food_dataset_v2` as the reproducible baseline. Until then, evaluation reports must include a leakage-excluded metric alongside the historical metric.
