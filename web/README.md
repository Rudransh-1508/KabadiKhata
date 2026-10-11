# Web front end

Landing page (`index.html`) and console (`console.html`): Home, Auditor radar with flag detail,
Kabadiwala ledger with chain verification, Brand certificates with provenance and the Cedar denial.
Plain HTML, CSS and JS, no build step. `server.py` serves the files and forwards `/api/*` to the API
unchanged (method, query, body, `X-Principal`), so every number and every 403 comes from the API and Cedar.

```bash
make seed && make api     # API on :3000
make web                  # http://localhost:8600
```

`KK_API_URL` points the forwarder at another API. The Streamlit console (`make console`) still works.
All data shown is synthetic, and every page carries the badge. The landing hero is drawn in code
(bottles and newspaper bundles), so it has no image to license.
