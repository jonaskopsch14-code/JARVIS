#!/usr/bin/env python3
"""Baut shopify-productset.json aus den Produkt-HTML-Dateien.

Damit bleiben Verkaufstext (HTML) und Shopify-Payload garantiert synchron:
Text wird nur in den .html-Dateien gepflegt, danach dieses Skript laufen lassen.

    python3 promptwerk/products/build-payload.py
"""

import json
import pathlib
import re

HIER = pathlib.Path(__file__).parent
KOLLEKTION = "gid://shopify/Collection/710415090009"

PRODUKTE = [
    {
        "datei": "01-marketing-content.html",
        "title": "KI-Prompt-Bibliothek: Marketing & Content",
        "handle": "ki-prompt-bibliothek-marketing-content",
        "preis": "19.00",
        "vergleichspreis": None,
        "sku": "PW-PROMPT-MKT",
        "umfang": "48 Prompts · PDF + Notion-Vorlage · Sofort-Download",
        "tags": ["Prompts", "Marketing", "Content", "Digital", "ChatGPT", "Claude"],
        "seo_titel": "KI-Prompt-Bibliothek Marketing & Content – 48 Prompts | PromptWerk",
        "seo_text": (
            "48 getestete Prompts für Social Media, Newsletter, Produkttexte und "
            "Werbung. Für Selbstständige und kleine Teams. PDF + Notion-Vorlage, "
            "Sofort-Download."
        ),
    },
    {
        "datei": "02-kundenservice-verwaltung.html",
        "title": "KI-Prompt-Bibliothek: Kundenservice & Verwaltung",
        "handle": "ki-prompt-bibliothek-kundenservice-verwaltung",
        "preis": "19.00",
        "vergleichspreis": None,
        "sku": "PW-PROMPT-SERVICE",
        "umfang": "44 Prompts · PDF + Notion-Vorlage · Sofort-Download",
        "tags": ["Prompts", "Kundenservice", "Verwaltung", "Digital", "ChatGPT", "Claude"],
        "seo_titel": "KI-Prompts für Kundenservice & Verwaltung – 44 Stück | PromptWerk",
        "seo_text": (
            "44 getestete Prompts für Kundenanfragen, Angebote, Beschwerden, FAQ und "
            "Termine. Für Selbstständige und kleine Teams. PDF + Notion, Sofort-Download."
        ),
    },
    {
        "datei": "03-business-vorlagen.html",
        "title": "Business-Vorlagen-Paket für Kleinunternehmer",
        "handle": "business-vorlagen-paket-kleinunternehmer",
        "preis": "29.00",
        "vergleichspreis": None,
        "sku": "PW-VORLAGEN",
        "umfang": "4 Vorlagen · Google Sheets + Notion · Sofort-Download",
        "tags": ["Vorlagen", "Kalkulation", "Rechnung", "Digital", "Kleinunternehmer"],
        "seo_titel": "Business-Vorlagen für Kleinunternehmer – 4 Vorlagen | PromptWerk",
        "seo_text": (
            "Preiskalkulator, Rechnungsvorlage mit § 19 UStG-Hinweis, Content-Kalender "
            "und Kundenübersicht. Google Sheets + Notion, Formeln hinterlegt, "
            "Sofort-Download."
        ),
    },
    {
        "datei": "04-komplettpaket.html",
        "title": "PromptWerk Komplettpaket",
        "handle": "promptwerk-komplettpaket",
        "preis": "49.00",
        "vergleichspreis": "67.00",
        "sku": "PW-KOMPLETT",
        "umfang": "92 Prompts + 4 Vorlagen + Bonus-PDF · Sofort-Download",
        "tags": ["Bundle", "Prompts", "Vorlagen", "Digital", "Sparpaket"],
        "seo_titel": "PromptWerk Komplettpaket – 92 Prompts + 4 Vorlagen für 49 € | PromptWerk",
        "seo_text": (
            "Beide Prompt-Bibliotheken, das Vorlagen-Paket und die Bonus-Kurzanleitung. "
            "49 € statt 67 € im Einzelkauf. Sofort-Download, kein Abo."
        ),
    },
]


def beschreibung_lesen(dateiname: str) -> str:
    """Liest das Produkt-HTML und entfernt den führenden Kommentar-Header."""
    roh = (HIER / dateiname).read_text(encoding="utf-8")
    ohne_kommentar = re.sub(r"^<!--.*?-->\s*", "", roh, flags=re.DOTALL)
    return ohne_kommentar.strip()


def variante_bauen(p: dict) -> dict:
    variante = {
        "optionValues": [{"optionName": "Title", "name": "Default Title"}],
        "price": p["preis"],
        "sku": p["sku"],
        "taxable": False,
        "inventoryPolicy": "CONTINUE",
        "inventoryItem": {"tracked": False, "requiresShipping": False},
    }
    if p["vergleichspreis"]:
        variante["compareAtPrice"] = p["vergleichspreis"]
    return variante


def main() -> None:
    payloads = []
    for p in PRODUKTE:
        payloads.append(
            {
                "input": {
                    "title": p["title"],
                    "handle": p["handle"],
                    "status": "DRAFT",
                    "vendor": "PromptWerk",
                    "productType": "Digitales Produkt",
                    "tags": p["tags"],
                    "descriptionHtml": beschreibung_lesen(p["datei"]),
                    "seo": {"title": p["seo_titel"], "description": p["seo_text"]},
                    "collections": [KOLLEKTION],
                    "metafields": [
                        {
                            "namespace": "custom",
                            "key": "umfang_zeile",
                            "type": "single_line_text_field",
                            "value": p["umfang"],
                        }
                    ],
                    "productOptions": [
                        {"name": "Title", "values": [{"name": "Default Title"}]}
                    ],
                    "variants": [variante_bauen(p)],
                }
            }
        )

    ziel = HIER / "shopify-productset.json"
    ziel.write_text(
        json.dumps(payloads, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    for p, nutzlast in zip(PRODUKTE, payloads):
        laenge = len(nutzlast["input"]["descriptionHtml"])
        print(f"  {p['handle']:<48} {laenge:>6} Zeichen Beschreibung")
    print(f"\n{len(payloads)} Payloads geschrieben nach {ziel}")


if __name__ == "__main__":
    main()
