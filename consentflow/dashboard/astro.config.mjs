import { defineConfig } from "astro/config";

// Statische Ausgabe → deploybar auf Cloudflare Pages (Free-Tier).
// Die API-URL wird zur Build-Zeit über PUBLIC_API_URL gesetzt (siehe .env.example).
export default defineConfig({
  output: "static",
  site: "https://app.consentflow.de",
});
