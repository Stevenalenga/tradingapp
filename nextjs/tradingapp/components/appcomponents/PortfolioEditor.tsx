"use client"

import { useState } from "react"
import { usePortfolio } from "./PortfolioProvider"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Trash2, Plus } from "lucide-react"

export function PortfolioEditor() {
  const { selected, addSymbol, removeSymbol } = usePortfolio()
  const [symbol, setSymbol] = useState("")

  if (!selected) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Portfolio</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No portfolio selected.</p>
        </CardContent>
      </Card>
    )
  }

  const onAdd = () => {
    const s = symbol.trim().toUpperCase()
    if (!s) return
    addSymbol(s)
    setSymbol("")
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{selected.name} — Symbols</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Input
            placeholder="e.g. BTC"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") onAdd()
            }}
          />
          <Button onClick={onAdd}>
            <Plus className="size-4" />
            Add
          </Button>
        </div>

        {selected.items.length === 0 ? (
          <p className="text-sm text-muted-foreground">No symbols yet. Add one above.</p>
        ) : (
          <ul className="divide-y rounded-md border">
            {selected.items.map((it) => (
              <li key={it.symbol} className="flex items-center justify-between px-3 py-2">
                <span className="font-mono">{it.symbol}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-destructive"
                  onClick={() => removeSymbol(it.symbol)}
                  title={`Remove ${it.symbol}`}
                >
                  <Trash2 className="size-4" />
                </Button>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}