export const CODES = { ap: "AP", helpdesk: "IT", support: "CS", reporting: "DR" };

export const GREETING = {
  ap: "Ready to work the invoice queue.",
  helpdesk: "Ready to work the IT queue.",
  support: "Ready to work the support queue.",
  reporting: "Ready for your reporting request.",
};

export function splitTitle(title) {
  const parts = title.split(" — ");
  return { name: parts[0].replace(" agent", ""), episode: parts[1] || "" };
}

export function host(url) {
  try { return new URL(url).host; } catch { return url || ""; }
}

export function uid() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export function fmtArgs(args) {
  return Object.entries(args || {})
    .map(([k, v]) => `${k}=${typeof v === "string" ? v : JSON.stringify(v)}`)
    .join(", ");
}
