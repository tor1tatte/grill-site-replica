# Grill-site replica (clean-room)

Structure and behaviour of a custom grill / outdoor-kitchen manufacturer's site, rebuilt from public pages only. Copy, brand, contacts and prices are original placeholders; photos are licensed stock images (Unsplash / Pexels, see CREDITS.md), not the original company's.

    python3 build.py         # src/content.json + tokens -> site/
    python3 server.py 8765   # preview at http://127.0.0.1:8765/ ; leads go to leads.jsonl
    node tests/e2e.mjs       # 53 browser checks (needs Chrome + node >= 22 + the server running)
    node tests/shots.mjs     # screenshots -> replica/clone-screens/

Make it yours: put your own photos into `src/photos/` (<key>-640|1200|1600.jpg) and list them in `src/photos.json` (or delete that file to get generated illustrations); edit `src/content.json` (all text, products, prices, contacts, video URLs), `replica/design/tokens.json` (colours, type), then `python3 build.py`. Deploy `site/` to any static host; for the form, run server.py or change `<meta name="lead-endpoint">` in build.py to your own endpoint.
`replica/` holds the recon map, feature matrix, design spec, build log and parity report.
