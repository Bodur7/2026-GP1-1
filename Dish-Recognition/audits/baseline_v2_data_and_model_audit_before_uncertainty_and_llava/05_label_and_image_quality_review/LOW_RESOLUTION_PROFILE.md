# Low-Resolution Image Profile

## Dataset-wide distribution

The verified manifest contains 105,681 images. Distribution by shortest image side:

| Shortest side | Images | Dataset share |
|---|---:|---:|
| below 32 | 5 | 0.01% |
| 32–63 | 0 | 0.00% |
| 64–127 | 28 | 0.03% |
| 128–223 | 1,878 | 1.78% |
| 224–335 | 5,749 | 5.44% |
| 336 or more | 98,021 | 92.75% |

Only the five sub-32-pixel Kunafa strips are automatically judged unusable. An image below the model's 336-pixel input size is not automatically incorrect; many require only moderate upscaling.

## Class concentration

Low resolution is strongly concentrated in several Arabic/MENA classes:

| Class | Images below 336 | Class total | Rate |
|---|---:|---:|---:|
| Kunafa | 187 | 200 | 93.5% |
| kebab | 188 | 201 | 93.5% |
| Kibbeh | 182 | 196 | 92.9% |
| Qatayef | 178 | 192 | 92.7% |
| Shawarma | 177 | 194 | 91.2% |
| Mandi | 172 | 190 | 90.5% |
| Mansaf | 170 | 190 | 89.5% |
| Shishabark | 151 | 170 | 88.8% |

This distribution is a domain/source warning: the classifier may learn image-source resolution or compression cues correlated with these classes. High aggregate accuracy alone cannot dismiss this risk.

## Required evaluation

1. Report accuracy, confidence, and calibration separately for images below and above 336 pixels.
2. Repeat the comparison at shortest-side thresholds 128 and 224.
3. Check whether errors change after controlling for Arabic/MENA versus Food-101 class groups.
4. Do not delete all images below 336. Only remove or replace images supported by visual and performance evidence.
5. If low-resolution performance is materially weaker, create a new dataset version with higher-quality replacements and fine-tune a separate checkpoint.
