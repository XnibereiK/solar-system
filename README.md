# Solar Project

Streamlit demo app served via Traefik and Cloudflare Tunnel.

## URLs
- https://solar.kierebinski.solutions

## Run

 Solar Planner – multipage Streamlit app for energy, cable sizing, and parts suggestion.

 Run locally:

 ``
 streamlit run streamlit_app/app.py
 ``

 Docker compose:

 ```
 docker compose up --build -d
 ```

 Notes:
 - Data persists to /app/data inside the container (mounted volume recommended).
 - Core logic lives under src/solar; Streamlit pages under streamlit_app/pages.
## Verify
```
# From server (Traefik):
curl -H "Host: solar.kierebinski.solutions" http://127.0.0.1:80

# From internet (after DNS propagation):
curl -I https://solar.kierebinski.solutions
```

## Notes
- TLS is terminated at Cloudflare in Tunnel mode. Traefik receives HTTP on `web` entrypoint.
- Direct mode is pre-wired via `solar-https` router, if you point DNS to server IP.