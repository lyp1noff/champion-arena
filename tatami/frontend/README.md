# Champion Tatami UI

Static React client for the Tatami service. Production contains only generated HTML, CSS and JavaScript; Node.js is used at build time only.

## Development

```sh
npm ci
npm run dev
```

The development server proxies `/api` to `http://localhost:8001`.

## Production build

```sh
npm ci
npm run build
```

The output is written to `dist/` and targets Chrome/Edge 109 for the Windows 7 clients. Dependency versions are exact and the lock file is committed so releases are reproducible.
