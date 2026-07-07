// HTTP-/CORS-Helfer und Standard-Bannerkonfiguration.

export function corsHeaders(origin = "*") {
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Max-Age": "86400",
  };
}

export function json(data, init = {}) {
  const headers = { "Content-Type": "application/json; charset=utf-8", ...(init.headers || {}) };
  return new Response(JSON.stringify(data), { ...init, headers });
}

export function error(status, message, { headers, ...extra } = {}) {
  return json({ error: message, ...extra }, { status, headers });
}

export function noContent(headers = {}) {
  return new Response(null, { status: 204, headers });
}

// Standardkonfiguration eines neuen Banners (deutsch).
export function defaultBannerConfig() {
  return {
    language: "de",
    position: "bottom",        // bottom | box
    theme: "light",            // light | dark
    colors: {
      background: "#ffffff",
      text: "#1f2430",
      primary: "#2f6df6",      // Akzeptieren-Button
      secondary: "#e9edf5",    // Ablehnen/Einstellungen
    },
    logo: "",
    showPoweredBy: true,        // bei Free/Starter an, Agency darf ausschalten
    texts: {
      title: "Wir respektieren Ihre Privatsphäre",
      message:
        "Wir verwenden Cookies, um unsere Website und unseren Service zu optimieren. " +
        "Nicht notwendige Cookies werden erst nach Ihrer Einwilligung geladen.",
      acceptAll: "Alle akzeptieren",
      rejectAll: "Ablehnen",
      settings: "Einstellungen",
      save: "Auswahl speichern",
      poweredBy: "geschützt mit ConsentFlow",
    },
    categories: {
      necessary: {
        enabled: true,
        label: "Notwendig",
        description: "Für den Betrieb der Website technisch erforderlich. Immer aktiv.",
      },
      statistics: {
        enabled: true,
        label: "Statistik",
        description: "Hilft uns zu verstehen, wie Besucher die Website nutzen (z. B. Analytics).",
      },
      marketing: {
        enabled: true,
        label: "Marketing",
        description: "Wird genutzt, um Werbung relevanter zu gestalten.",
      },
    },
  };
}

export const PLAN_LIMITS = {
  trial: 1,
  starter: 3,
  agency: 25,
};
