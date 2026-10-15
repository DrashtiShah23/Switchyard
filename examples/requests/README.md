# Example change requests

Sample JSON bodies for `POST /v1/changes`.

Authenticate with a configured demo API key:

```bash
curl -s http://127.0.0.1:8000/v1/changes \
  -H "Authorization: Bearer replace-me" \
  -H "Idempotency-Key: demo-1" \
  -H "Content-Type: application/json" \
  -d @examples/requests/dns_create.json
```

Actor identity comes from the API key mapping in `SWITCHYARD_API_KEYS`, not from
the JSON body.
