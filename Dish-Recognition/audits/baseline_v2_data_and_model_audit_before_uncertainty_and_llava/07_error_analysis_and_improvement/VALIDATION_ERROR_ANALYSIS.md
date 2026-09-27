# Full Validation Error Analysis

## Result

The baseline reproduces 96.9972% Top-1 accuracy on all 3,630 validation images: 3,521 correct and 109 incorrect. Top-3 reaches 99.0909% and Top-5 reaches 99.3939%.

## Weakest classes

Each validation class contains 30 images.

| Class | Top-1 correct | Top-1 | Top-5 |
| --- | ---: | ---: | ---: |
| aseeda | 23 | 76.67% | 96.67% |
| hininy | 23 | 76.67% | 96.67% |
| Kibbeh | 24 | 80.00% | 100.00% |
| Shishabark | 25 | 83.33% | 93.33% |
| baba-ghanoush | 25 | 83.33% | 96.67% |
| saleeg | 25 | 83.33% | 93.33% |
| Mandi | 26 | 86.67% | 96.67% |
| areeka | 26 | 86.67% | 100.00% |
| masoub | 26 | 86.67% | 96.67% |
| shakshouka-egypt | 26 | 86.67% | 100.00% |
| steak | 26 | 86.67% | 100.00% |

## Interpretation and actions

The errors are not uniformly distributed. Arabic/MENA validation Top-1 is 89.833%, compared with 98.416% for Food-101. Several weak MENA classes are visually overlapping mixtures, breads, soups, rice dishes, or dumpling-like foods. The next data action is a pair-aware label-policy review and targeted sample review, not a full rebuild and not blanket removal of low-resolution images.

Proposed experiments, in order:

1. Freeze and evaluate the validation-selected uncertainty policy on test.
2. Review all errors for the weakest MENA classes and document inclusion/exclusion rules.
3. Create a corrected dataset version that removes or replaces only confirmed invalid samples and prevents the five train/test near-duplicate leaks.
4. Establish an OOD benchmark before considering an `other` class.
5. If data-policy fixes identify learnable gaps, run a separate limited fine-tuning experiment and compare it against the protected checkpoint.

