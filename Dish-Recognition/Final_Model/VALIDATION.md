# Delivery verification — 30 October 2026

- 11 package presentation/pipeline tests passed from `Dish-Recognition/Final_Model/`.
- Node UI rendering checks passed from the delivered folder.
- 11 central human-label authority tests passed without changing the registry.
- Every delivered file hash was verified against the release manifest.
- A real frozen DINOv2 + Nonlinear OOD inference passed on a synthetic RGB image,
  using the unchanged external checkpoint and the source runtime environment.
- The runtime returned 121 classes and preserved threshold 0.18922570362206778.
- No paid provider requests, training, reserved OOD Final Test access or accuracy
  evaluation were performed. The synthetic check is a runtime integrity check.

The existing runtime environment supplied the pinned model dependencies. The
project root development environment lacked SciPy; the model check passed using
the existing pipeline environment, without changing dependencies or source code.
