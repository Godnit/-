# Build

The workflow `.github/workflows/android.yml` runs on pushes to `portal-gates` or `main` and can also be started manually.

It installs Blender, generates `assets/portal_ring.glb`, then uses Godot 4.6 stable and its Android export templates to build `build/PortalGates.apk`.

The Android preset targets API 27 minimum and includes ARMv7 and ARM64 for compatibility with older devices.
