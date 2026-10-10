# Wilfred profile image

Wilfred's official portrait is the public GitHub account avatar for `keriol` (GitHub account ID `259832917`), copied once into `assets/profile.png`.

The asset is local to this Wilfred repository. The final Butler installation should own its copy rather than requesting GitHub avatar bytes at runtime. Any future refresh is a separately reviewed Git commit.

**Integration boundary:** Wilfred's current TOML `[identity]` allows `name` and `locale` only. `assets/profile.png` is a packaged project asset, not yet a configured `profile_picture` property or an image delivered through Asgard/Midgard/Bifröst. The source image must not be treated as authentication material.

The initial avatar import is performed on an isolated feature branch by the temporary GitHub Actions workflow `import-wilfred-portrait.yml`. Its output is a validated PNG (bounded size and dimensions, EXIF removed by re-encoding); the workflow is to be removed from the final branch after the asset is obtained. No production/runtime dependency on Pillow is introduced.

Follow-up: ASG-002, MID-009, BIF-015 and Wilfred identity configuration.
