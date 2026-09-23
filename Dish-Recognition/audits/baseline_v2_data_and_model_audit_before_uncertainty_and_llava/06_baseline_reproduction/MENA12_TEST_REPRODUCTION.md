# MENA-12 Test Reproduction

## Scope

The protected 121-class checkpoint was evaluated on all 523 available test images from the 12 classes represented in `MENA_selected_cleaned`. No training or parameter change was performed. Per-image logits remain outside Git; the compact result is stored in `audit_results/mena12_test_reproduction.json`.

## Result

- Images: 523
- Correct Top-1 predictions: 511
- Top-1 accuracy: 97.7055%
- Top-2 accuracy: 99.8088%
- Top-3 accuracy: 100%
- Top-5 accuracy: 100%

The per-class image and correct-prediction counts exactly reproduce the committed baseline report for these 12 classes.

## Per-class Top-1 accuracy

| Class | Images | Correct | Accuracy |
| --- | ---: | ---: | ---: |
| arayes | 49 | 47 | 95.92% |
| areeka | 44 | 43 | 97.73% |
| aseeda | 45 | 45 | 100% |
| baba-ghanoush | 47 | 46 | 97.87% |
| briouat | 46 | 46 | 100% |
| dajaj-mashwi | 43 | 43 | 100% |
| hasa-adas | 47 | 45 | 95.74% |
| hininy | 24 | 21 | 87.50% |
| maamoul-saudi-arabia | 45 | 45 | 100% |
| masoub | 35 | 34 | 97.14% |
| saleeg | 49 | 47 | 95.92% |
| shakshouka-egypt | 49 | 49 | 100% |

## Interpretation

This verifies model/report reproducibility for the available MENA-12 subset. It does not validate calibration, real-world generalization, OOD rejection, or the eight other MENA classes with only ten test images each. Top-3 is sufficient for every error in this subset, so displaying five candidates has no demonstrated benefit here. The full 121-class evaluation is still required before choosing a product-wide Top-k policy.
