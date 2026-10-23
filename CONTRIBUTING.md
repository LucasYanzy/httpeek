# Contributing

Start with a reproducible issue or a focused pull request. Describe the concrete input, expected behavior and observed behavior. Use synthetic data; do not attach personal config, private source code, request history, cookies or secrets.

## Local checks

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_publication.py
```

Keep runtime claims, CLI examples, package metadata and both README languages consistent. Regenerate the demo transcript with `python3 scripts/demo.py` when output changes. `scripts/render_assets.py` renders committed CLI output into images (requires Pillow).

Use a project-scoped Git identity and a no-reply address when appropriate. Check the commit author and committer before pushing.
