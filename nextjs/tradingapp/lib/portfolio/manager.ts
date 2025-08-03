"use client"

import {
  Portfolio,
  PortfolioItem,
  PortfolioSnapshot,
  createPortfolio,
  normalizeSymbol,
  uniqueSymbols,
} from "@/app/portfolios/schemas"
import { loadSnapshot, saveSnapshot, selectPortfolioId, upsertPortfolio, removePortfolio as removePortfolioFromStore } from "./storage"

function getSnapshotOrSeed(): PortfolioSnapshot {
  const current = loadSnapshot()
  if (current && Array.isArray(current.portfolios) && current.portfolios.length > 0) {
    return current
  }
  // Seed with a default portfolio
  const seeded = createPortfolio("My Portfolio", ["BTC", "ETH"])
  const snapshot: PortfolioSnapshot = {
    portfolios: [seeded],
    selectedPortfolioId: seeded.id,
    version: 1,
  }
  saveSnapshot(snapshot)
  return snapshot
}

export function listPortfolios(): Portfolio[] {
  return getSnapshotOrSeed().portfolios
}

export function getSelectedPortfolio(): Portfolio | null {
  const snap = getSnapshotOrSeed()
  const id = snap.selectedPortfolioId
  if (!id) return snap.portfolios[0] ?? null
  return snap.portfolios.find((p) => p.id === id) ?? snap.portfolios[0] ?? null
}

export function setSelectedPortfolio(id: string | null): void {
  selectPortfolioId(id)
}

export function createNewPortfolio(name: string): Portfolio {
  const p = createPortfolio(name)
  upsertPortfolio(p)
  // Select it if nothing selected
  const snap = loadSnapshot()
  if (snap && !snap.selectedPortfolioId) {
    selectPortfolioId(p.id)
  }
  return p
}

export function renamePortfolio(id: string, name: string): Portfolio | null {
  const snap = getSnapshotOrSeed()
  const idx = snap.portfolios.findIndex((p) => p.id === id)
  if (idx === -1) return null
  const updated: Portfolio = { ...snap.portfolios[idx], name: name.trim() || "Untitled", updatedAt: Date.now() }
  upsertPortfolio(updated)
  return updated
}

export function deletePortfolio(id: string): void {
  removePortfolioFromStore(id)
}

export function addSymbolToPortfolio(portfolioId: string, symbol: string): Portfolio | null {
  const sym = normalizeSymbol(symbol)
  if (!sym) return null
  const snap = getSnapshotOrSeed()
  const idx = snap.portfolios.findIndex((p) => p.id === portfolioId)
  if (idx === -1) return null
  const p = snap.portfolios[idx]
  const existing = new Set(p.items.map((i) => i.symbol))
  if (existing.has(sym)) {
    // no-op
    return p
  }
  const next: Portfolio = {
    ...p,
    items: [...p.items, { symbol: sym } as PortfolioItem],
    updatedAt: Date.now(),
  }
  upsertPortfolio(next)
  return next
}

export function removeSymbolFromPortfolio(portfolioId: string, symbol: string): Portfolio | null {
  const sym = normalizeSymbol(symbol)
  const snap = getSnapshotOrSeed()
  const idx = snap.portfolios.findIndex((p) => p.id === portfolioId)
  if (idx === -1) return null
  const p = snap.portfolios[idx]
  const nextItems = p.items.filter((i) => i.symbol !== sym)
  const next: Portfolio = { ...p, items: nextItems, updatedAt: Date.now() }
  upsertPortfolio(next)
  return next
}

export function replaceSymbols(portfolioId: string, symbols: string[]): Portfolio | null {
  const snap = getSnapshotOrSeed()
  const idx = snap.portfolios.findIndex((p) => p.id === portfolioId)
  if (idx === -1) return null
  const p = snap.portfolios[idx]
  const cleaned = uniqueSymbols(symbols).map((s) => ({ symbol: s }))
  const next: Portfolio = { ...p, items: cleaned, updatedAt: Date.now() }
  upsertPortfolio(next)
  return next
}