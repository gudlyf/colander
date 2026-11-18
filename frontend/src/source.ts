// Where a recipe came from, for the "From …" line on the recipe page.

export interface Source {
  label: string;
  /** Set only for http(s) links, so nothing else ends up in an href. */
  href: string | null;
}

export function recipeSource(sourceName: string | null, sourceUrl: string | null): Source | null {
  const name = sourceName?.trim() || null;
  const url = sourceUrl?.trim() || null;
  const parsed = url ? parseHttpUrl(url) : null;
  if (parsed) return { label: name ?? parsed.hostname, href: parsed.href };
  // A cookbook, a person, or a link that can't be opened: show the text alone.
  const label = name ?? url;
  return label ? { label, href: null } : null;
}

// "www.example.com/soup" or "example.com": a domain, missing its scheme.
const BARE_DOMAIN = /^[\w-]+(\.[\w-]+)+([/?#]|$)/;

function parseHttpUrl(url: string): URL | null {
  const candidate = BARE_DOMAIN.test(url) ? `https://${url}` : url;
  try {
    const u = new URL(candidate);
    // Anything else (javascript:, mailto:, …) is shown as text, not linked.
    return u.protocol === "http:" || u.protocol === "https:" ? u : null;
  } catch {
    return null;
  }
}
