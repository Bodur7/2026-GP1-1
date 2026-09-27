# 05 — Label and image-quality review

Tracks suspicious images: corrupted files, dimension outliers, low-quality examples, likely label conflicts, and high-confidence model errors. Human review targets important cases rather than manually reviewing every image.

`TINY_KUNAFA_FINDINGS.md` documents five verified but unusably thin Kunafa image strips and the baseline-preserving corrective action.

`LOW_RESOLUTION_PROFILE.md` shows that 92.75% of the dataset meets the 336-pixel shortest-side target, while low-resolution imagery is highly concentrated in several Arabic/MENA classes. This becomes a required stratified model evaluation rather than a blanket deletion rule.
