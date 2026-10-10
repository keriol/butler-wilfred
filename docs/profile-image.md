# Wilfred profile portrait

The official Wilfred image is a **one-time, locally vendored copy** of the GitHub account avatar for [keriol](https://github.com/keriol), with account ID `259832917`.

- Source: `https://avatars.githubusercontent.com/u/259832917?v=4&s=512`
- Repository asset: **`assets/profile.png`**
- The source was downloaded and validated in GitHub Actions on branch `assets/wilf-075-github-avatar`: HTTPS download, size/dimension bounds, image decoding, re-encoding as PNG without EXIF; the temporary importer workflow was removed before merge.
- A lightweight repository test validates the committed file's PNG signature, IHDR and dimension/size limits.

This is an **asset**, not an online dependency. No runtime download from GitHub and no Pillow dependency in Wilfred itself.

## Identity and integration boundaries

The Wilfred runtime already accepts a configured instance name via its public `[identity] name` and `WILFRED_NAME` options. Its current parser **does not accept** `aliases`, `description` or `profile_picture` settings. This file is therefore not yet automatically connected to its runtime metadata or published via Asgard/Midgard/Bifröst manifests.

The concrete Butler owns the profile image. Asgard projects identity, Midgard transports optional sanitized presentation metadata (MID-009), and Bifröst serializes it (BIF-015), once those features exist. A missing image must not prevent routing.

Reference: WILF-075, ASG-002, MID-009, BIF-015. Any later portrait refresh requires an explicit reviewed commit.
