# my-ai2

Vlastní AI backend připravený pro Android klienta.

## Architektura
- Cloudflare Worker – HTTPS API
- Cloudflare Workers AI – AI model
- Android – HTTP klient

## API
### GET /api/health
Vrací stav API a použitý model.

### POST /api/chat
```json
{"message":"Ahoj","conversationId":"optional-id"}
```

## Lokální vývoj
```bash
npm install
npx wrangler dev
```

## Deploy
```bash
npx wrangler login
npx wrangler deploy
```
