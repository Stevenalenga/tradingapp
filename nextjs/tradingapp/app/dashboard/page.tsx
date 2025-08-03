"use client"

import { CoinCard } from "@/components/appcomponents/CoinCard"
import { StopLossInput } from "@/components/appcomponents/StopLossInput"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { PortfolioEditor } from "@/components/appcomponents/PortfolioEditor"
import { usePortfolio } from "@/components/appcomponents/PortfolioProvider"
import { useMemo, useState, useEffect } from "react"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet"

export default function DashboardPage() {
  const { selected, removeSymbol } = usePortfolio()
  const [activeSymbol, setActiveSymbol] = useState<string | null>(null)
  const [openControls, setOpenControls] = useState(false)

  // Keep activeSymbol sensible when portfolio changes
  useEffect(() => {
    const symbols = selected?.items?.map((i) => i.symbol) ?? []
    if (!symbols.length) {
      setActiveSymbol(null)
    } else if (!activeSymbol || !symbols.includes(activeSymbol)) {
      setActiveSymbol(symbols[0]!)
    }
  }, [selected?.items])

  // Fallback placeholder (existing BTC card design)
  const placeholder = {
    name: "Bitcoin",
    symbol: "BTC",
    price: 65000,
    change24h: 2.5,
    holdings: 0.5,
    value: 32500,
    recommendedSL: 60000,
    recommendedTP: 70000,
  }

  // Map a symbol to display data. For now we synthesize values to mirror the placeholder style.
  const toCardData = (symbol: string) => {
    // Basic synthetic demo values; could be wired to live pricing later.
    const base = symbol.toUpperCase()
    const name = base // In a real app map symbol->full name.
    const price = base === "BTC" ? 65000 : 100 + Math.floor(Math.random() * 1000)
    const change24h = base === "BTC" ? 2.5 : Number((Math.random() * 10 - 5).toFixed(2))
    const holdings = 0 // unknown; user holdings could be added later
    const value = holdings * price
    const recommendedSL = Number((price * 0.92).toFixed(2))
    const recommendedTP = Number((price * 1.08).toFixed(2))
    return {
      name,
      symbol: base,
      price,
      change24h,
      holdings,
      value,
      recommendedSL,
      recommendedTP,
    }
  }

  const symbols = selected?.items?.map((i) => i.symbol) ?? []

  const cards = useMemo(() => {
    if (!symbols.length) {
      return [placeholder]
    }
    return symbols.map((s) => toCardData(s))
  }, [symbols])

  // The currently selected card to drive the SL/TP panel
  const activeCard = useMemo(() => {
    if (!symbols.length) return placeholder
    const sym = activeSymbol ?? symbols[0]
    return toCardData(sym)
  }, [activeSymbol, symbols])

  const openUpdateControls = (sym: string) => {
    setActiveSymbol(sym)
    setOpenControls(true)
  }

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-6">
      <h2 className="text-2xl font-bold">Portfolio Overview</h2>

      {/* Coin cards grid: show placeholder if no symbols, otherwise render each added symbol */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {cards.map((c) => (
          <CoinCard
            key={c.symbol}
            {...c}
            selected={activeSymbol === c.symbol}
            onSelect={(sym) => openUpdateControls(sym)}
            onDelete={(sym) => removeSymbol(sym)}
          />
        ))}

        {/* Keep the auxiliary card for recommendations bound to the active card */}
        <Card>
          <CardHeader>
            <CardTitle>Recommended SL/TP</CardTitle>
          </CardHeader>
          <CardContent>
            <p>
              {activeCard.name} ({activeCard.symbol}):
            </p>
            <p>
              Stop Loss: {activeCard.recommendedSL.toLocaleString("en-US", { style: "currency", currency: "USD" })}
            </p>
            <p>
              Take Profit: {activeCard.recommendedTP.toLocaleString("en-US", { style: "currency", currency: "USD" })}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Portfolio symbols management */}
      <div className="grid gap-4 md:grid-cols-2">
        <PortfolioEditor />
      </div>

      <div className="min-h-[300px] rounded-xl border border-dashed p-4 text-center text-muted-foreground flex items-center justify-center">
        Your portfolio chart will appear here.
      </div>

      {/* Controls Sheet (popup) */}
      <Sheet open={openControls} onOpenChange={setOpenControls}>
        <SheetContent side="right">
          <SheetHeader>
            <SheetTitle>Set Your Risk Controls</SheetTitle>
            <SheetDescription>
              Update Stop Loss and Take Profit for {activeCard.name} ({activeCard.symbol}).
            </SheetDescription>
          </SheetHeader>
          <div className="px-4 pb-4 space-y-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Current Price</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {activeCard.price.toLocaleString("en-US", { style: "currency", currency: "USD" })}
                </div>
                <div
                  className={`mt-1 text-sm ${activeCard.change24h >= 0 ? "text-green-500" : "text-red-500"}`}
                >
                  {activeCard.change24h > 0 ? "+" : ""}
                  {activeCard.change24h.toFixed(2)}% (24h)
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Controls</CardTitle>
              </CardHeader>
              <CardContent>
                <StopLossInput coinSymbol={activeCard.symbol} />
              </CardContent>
            </Card>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  )
}
