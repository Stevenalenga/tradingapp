"use client"

import type React from "react"

import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { toast } from "sonner"

interface StopLossInputProps {
  coinSymbol: string
}

export function StopLossInput({ coinSymbol }: StopLossInputProps) {
  const [stopLoss, setStopLoss] = useState<string>("")
  const [takeProfit, setTakeProfit] = useState<string>("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Here you would typically send this data to your backend API
    console.log(`Setting SL/TP for ${coinSymbol}:`, { stopLoss, takeProfit })
    toast(
      <div>
        <div className="font-semibold">Risk Controls Updated</div>
        <div className="text-muted-foreground text-sm">
          Stop Loss: {stopLoss}, Take Profit: {takeProfit} for {coinSymbol}
        </div>
      </div>
    )
    setStopLoss("")
    setTakeProfit("")
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div>
        <Label htmlFor={`stop-loss-${coinSymbol}`}>Stop Loss Price</Label>
        <Input
          id={`stop-loss-${coinSymbol}`}
          type="number"
          placeholder="e.g., 60000"
          value={stopLoss}
          onChange={(e) => setStopLoss(e.target.value)}
          required
          className="mt-1"
        />
      </div>
      <div>
        <Label htmlFor={`take-profit-${coinSymbol}`}>Take Profit Price</Label>
        <Input
          id={`take-profit-${coinSymbol}`}
          type="number"
          placeholder="e.g., 70000"
          value={takeProfit}
          onChange={(e) => setTakeProfit(e.target.value)}
          required
          className="mt-1"
        />
      </div>
      <Button type="submit">Set Controls</Button>
    </form>
  )
}
