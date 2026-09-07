# Portal Gates

A mobile-first 3D portal puzzle game built from scratch for older Android phones.

## Target
- Android 8.1+ (API 27+)
- Godot 4.6 stable
- Compatibility renderer / OpenGL ES 3
- ARMv7 + ARM64 APK

## Game
- 20 deterministic, solvable chambers.
- A/B portals with live SubViewport views of the linked side.
- Player and cube portal transfer.
- Switches, cubes, lasers, hazards and moving platforms.
- Progressive difficulty and longer chambers.
- Loading screen, main menu, level select, saving, pause, replay and next-level flow.
- Touch controls plus keyboard/mouse controls for testing.

## CI
GitHub Actions generates a low-poly Blender asset, cleans inherited legacy files, exports with Godot 4.6, moves the generated APK into `build/`, and uploads it as a workflow artifact.
