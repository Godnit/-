# Reference House 3D

Procedural Blender project that rebuilds the supplied cottage reference as a real 3D model.

Build is automated with GitHub Actions. The workflow generates:

- `output/model.blend`
- `output/model.glb`
- six preview renders
- `output/model_report.txt`

The model is built with Blender Python in headless mode and validated before export.
