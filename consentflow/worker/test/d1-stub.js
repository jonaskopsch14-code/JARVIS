// Minimaler D1-Stub auf Basis von node:sqlite – bildet die von den Handlern
// genutzte Cloudflare-D1-API nach (prepare/bind/first/run/all).
import { DatabaseSync } from "node:sqlite";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));

export function makeD1() {
  const db = new DatabaseSync(":memory:");
  const schema = readFileSync(join(__dirname, "..", "schema.sql"), "utf8");
  db.exec(schema);
  return {
    prepare(sql) {
      return {
        _args: [],
        bind(...args) { this._args = args; return this; },
        first() { return db.prepare(sql).get(...this._args) ?? null; },
        run() { const r = db.prepare(sql).run(...this._args); return { meta: { changes: Number(r.changes) } }; },
        all() { return { results: db.prepare(sql).all(...this._args) }; },
      };
    },
  };
}
