"use client"

import type { Portfolio, PortfolioSnapshot } from "@/app/portfolios/schemas"

const STORAGE_KEY = "tradingapp.portfolios.v1"

export function loadSnapshot(): PortfolioSnapshot | null {
  if (typeof window === "undefined") return null
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as PortfolioSnapshot
    if (!parsed || !Array.isArray(parsed.portfolios)) return null
    return parsed
  } catch {
    return null
  }
}

export function saveSnapshot(snapshot: PortfolioSnapshot): void {
  if (typeof window === "undefined") return
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot))
  } catch {
    // ignore quota or privacy errors
  }
}

export function clearSnapshot(): void {
  if (typeof window === "undefined") return
  try {
    window.localStorage.removeItem(STORAGE_KEY)
  } catch {
    // ignore
  }
}

export function selectPortfolioId(id: string | null): void {
  const snap = loadSnapshot()
  if (!snap) return
  saveSnapshot({ ...snap, selectedPortfolioId: id })
}

export function upsertPortfolio(portfolio: Portfolio): void {
  const snap = loadSnapshot()
  if (!snap) {
    const newSnap: PortfolioSnapshot = {
      portfolios: [portfolio],
      selectedPortfolioId: portfolio.id,
      version: 1,
    }
    saveSnapshot(newSnap)
    return
  }
  const idx = snap.portfolios.findIndex((p) => p.id === portfolio.id)
  if (idx === -1) {
    saveSnapshot({
      ...snap,
      portfolios: [...snap.portfolios, portfolio],
      selectedPortfolioId: snap.selectedPortfolioId ?? portfolio.id,
    })
  } else {
    const next = [...snap.portfolios]
    next[idx] = portfolio
    saveSnapshot({ ...snap, portfolios: next })
  }
}

export function removePortfolio(id: string): void {
  const snap = loadSnapshot()
  if (!snap) return
  const nextList = snap.portfolios.filter((p) => p.id !== id)
  let nextSelected = snap.selectedPortfolioId
  if (snap.selectedPortfolioId === id) {
    nextSelected = nextList.length ? nextList[0].id : null
  }
  saveSnapshot({ ...snap, portfolios: nextList, selectedPortfolioId: nextSelected })
}