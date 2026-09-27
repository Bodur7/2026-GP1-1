# Full Test Error Analysis

## What the full test adds

The original report established aggregate Top-1/Top-5 performance and the main
confusion pairs. The per-image export now shows which errors the frozen
confidence policy detects and whether the true class remains in Top-3 or Top-5.
The figures below exclude the five confirmed train/test same-photo files.

## In-domain results

- Samples: 25,848
- Top-1: 94.9977%
- Top-3: 98.5995%
- Top-5: 99.1450%
- Arabic/MENA 20 classes: 98.0100% Top-1 on 603 images
- Food-101 101 classes: 94.9257% Top-1 on 25,245 images

The high Arabic/MENA test score must not be read as stronger evidence than the
lower validation result. Several new classes have only 10 test images, while
Food-101 classes normally have 250. Validation showed an Arabic/MENA Top-1 of
89.833%, so the split-level discrepancy and small class samples require
pair-aware data review rather than a claim that the regional classes are solved.

## Dominant remaining confusions

The leading pairs remain semantically and visually close:

1. `steak` -> `filet_mignon`: 34
2. `filet_mignon` -> `steak`: 29
3. `chocolate_mousse` -> `chocolate_cake`: 18
4. `apple_pie` -> `bread_pudding`: 16
5. `chocolate_cake` -> `chocolate_mousse`: 15
6. `prime_rib` -> `steak`: 15
7. `steak` -> `prime_rib`: 15
8. `dumplings` <-> `gyoza`: 13 in each direction

## Evidence for Top-3 versus Top-5 in the review band

The validation-frozen confidence threshold sends 2,394 clean test images
(9.26%) to review. Inside this harder band:

- Top-1 accuracy: 61.61%
- Top-3 oracle inclusion: 89.39%
- Top-5 oracle inclusion: 93.94%
- Top-1 errors: 919
- Error truths recovered within Top-3: 665
- Additional error truths found only at ranks 4-5: 109
- Error truths absent from Top-5: 145

Top-5 therefore provides measurable additional candidate recall, but it also
increases ambiguity and computation. These are oracle inclusion figures, not
LLaVA accuracy. The next comparison should benchmark constrained LLaVA with
Top-3, Top-5, and a dynamic Top-k on the same review cases. Until that benchmark
exists, Top-3 is the simpler primary candidate set and Top-5 is a measured
fallback, not a product decision.

## Improvement actions supported by evidence

1. Preserve the 121-class checkpoint as the protected baseline.
2. Correct the five leaked pairs and five unusable Kunafa strips only in a new
   dataset version, then run a targeted sensitivity/fine-tuning experiment.
3. Define inclusion rules and review samples for the recurrent visually close
   class pairs, especially the weak regional validation classes.
4. Benchmark grouped OOD rejection before approving Unknown or an `other` class.
5. Benchmark LLaVA only on the frozen classifier review band and report its own
   final-label accuracy, not merely whether the truth appeared in Top-k.
