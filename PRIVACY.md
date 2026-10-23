# Privacy

HTTP requests send data to the URL you choose. History stores URLs, headers and text bodies locally by default, including possible credentials; use `--no-history` for sensitive requests and `httpeek history --clear` to remove history. Cookie jars and collections can contain secrets: never commit them. The optional `ai` command sends your prompt to its configured Ollama endpoint.

## Demonstrations

Committed demos use synthetic inputs and fictional contributors. No personal repository, request history, cookie jar or agent home is used to generate them. Temporary absolute demo paths are normalized in exported output.

## Before sharing

Review reports, screenshots, request collections and logs for file paths, names, credentials and source content. Local processing does not make every output safe to publish. Submit minimal synthetic reproductions instead of real private data.

## Development and distribution

Dependency installation and hosted CI can contact package registries and GitHub. Publishing a repository or package is separate from running the tool locally. Do not include local reports, environment files, cookies or credentials in distributions.
