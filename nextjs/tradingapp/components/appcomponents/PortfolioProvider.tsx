"use client"

import React, { createContext, useContext, useEffect, useMemo, useState } from "react"
import type { Portfolio } from "@/app/portfolios/schemas"
import {
  addSymbolToPortfolio,
  createNewPortfolio,
  deletePortfolio,
  getSelectedPortfolio,
  listPortfolios,
  removeSymbolFromPortfolio,
  renamePortfolio,
  setSelectedPortfolio,
} from "@/lib/portfolio/manager"

type PortfolioContextValue = {
  portfolios: Portfolio[]
  selected: Portfolio | null
  select: (id: string | null) => void
  create: (name: string) => Portfolio
  rename: (id: string, name: string) => Portfolio | null
  remove: (id: string) => void
  addSymbol: (symbol: string) => void
  removeSymbol: (symbol: string) => void
  refresh: () => void
}

const PortfolioContext = createContext<PortfolioContextValue | null>(null)

export function usePortfolio() {
  const ctx = useContext(PortfolioContext)
  if (!ctx) throw new Error("usePortfolio must be used within PortfolioProvider")
  return ctx
}

export function PortfolioProvider({ children }: { children: React.ReactNode }) {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([])
  const [selected, setSelected] = useState<Portfolio | null>(null)

  const refresh = React.useCallback(() => {
    const list = listPortfolios()
    const sel = getSelectedPortfolio()
    setPortfolios(list)
    setSelected(sel)
  }, [])

  useEffect(() => {
    // Hydrate from storage on mount
    refresh()
  }, [refresh])

  const api = useMemo<PortfolioContextValue>(
    () => ({
      portfolios,
      selected,
      select: (id: string | null) => {
        setSelectedPortfolio(id)
        refresh()
      },
      create: (name: string) => {
        const p = createNewPortfolio(name)
        // After creating we select via manager if needed; refresh to reflect
        refresh()
        return p
      },
      rename: (id: string, name: string) => {
        const p = renamePortfolio(id, name)
        refresh()
        return p
      },
      remove: (id: string) => {
        deletePortfolio(id)
        refresh()
      },
      addSymbol: (symbol: string) => {
        if (!selected) return
        addSymbolToPortfolio(selected.id, symbol)
        refresh()
      },
      removeSymbol: (symbol: string) => {
        if (!selected) return
        removeSymbolFromPortfolio(selected.id, symbol)
        refresh()
      },
      refresh,
    }),
    [portfolios, selected, refresh]
  )

  return <PortfolioContext.Provider value={api}>{children}</PortfolioContext.Provider>
}