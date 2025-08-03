"use client"

import { useState } from "react"
import { usePortfolio } from "./PortfolioProvider"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ChevronDown, Plus, Trash2, Check } from "lucide-react"

export function PortfolioSwitcher() {
  const { portfolios, selected, select, create, remove } = usePortfolio()
  const [creating, setCreating] = useState(false)
  const [name, setName] = useState("")

  const onCreate = () => {
    const n = name.trim()
    if (!n) return
    const p = create(n)
    select(p.id)
    setName("")
    setCreating(false)
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="justify-between w-full">
          <div className="flex items-center gap-2 overflow-hidden">
            <span className="font-semibold truncate">{selected?.name ?? "Select Portfolio"}</span>
          </div>
          <ChevronDown className="size-4 opacity-70" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-72" align="start">
        <DropdownMenuLabel>Portfolios</DropdownMenuLabel>
        {portfolios.map((p) => (
          <DropdownMenuItem key={p.id} onClick={() => select(p.id)} className="flex items-center justify-between">
            <span className="truncate">{p.name}</span>
            {selected?.id === p.id ? <Check className="size-4 text-primary" /> : null}
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        {!creating ? (
          <DropdownMenuItem onClick={() => setCreating(true)} className="gap-2">
            <Plus className="size-4" />
            Create new
          </DropdownMenuItem>
        ) : (
          <div className="px-2 py-1.5 space-y-2">
            <Input
              placeholder="New portfolio name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <div className="flex gap-2">
              <Button size="sm" className="flex-1" onClick={onCreate}>
                Create
              </Button>
              <Button size="sm" variant="ghost" className="flex-1" onClick={() => { setCreating(false); setName(""); }}>
                Cancel
              </Button>
            </div>
          </div>
        )}
        {selected ? (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="gap-2 text-destructive focus:text-destructive"
              onClick={() => remove(selected.id)}
            >
              <Trash2 className="size-4" />
              Delete current
            </DropdownMenuItem>
          </>
        ) : null}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}