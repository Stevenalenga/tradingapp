export type PortfolioItem = {
  symbol: string
}

export type Portfolio = {
  id: string
  name: string
  items: PortfolioItem[]
  createdAt: number
  updatedAt: number
}

export type PortfolioSnapshot = {
  portfolios: Portfolio[]
  selectedPortfolioId: string | null
  version: number
}

// Helpers
export function createPortfolio(name: string, items: string[] = []): Portfolio {
  const now = Date.now()
  return {
    id: cryptoRandomId(),
    name: name.trim() || "New Portfolio",
    items: uniqueSymbols(items).map((s) => ({ symbol: s })),
    createdAt: now,
    updatedAt: now,
  }
}

export function cryptoRandomId(): string {
  // Browser-safe, Node-safe
  if (typeof crypto !== "undefined" && "getRandomValues" in crypto) {
    const bytes = new Uint8Array(16)
    crypto.getRandomValues(bytes)
    return Array.from(bytes)
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("")
  }
  return Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2)
}

export function normalizeSymbol(symbol: string): string {
  return symbol.trim().toUpperCase()
}

export function uniqueSymbols(symbols: string[]): string[] {
  const set = new Set(symbols.map(normalizeSymbol).filter(Boolean))
  return Array.from(set)
}