import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { TrendingUp, TrendingDown, MoreHorizontal, Settings2, Trash2 } from "lucide-react"

interface CoinCardProps {
  name: string
  symbol: string
  price: number
  change24h: number
  holdings: number
  value: number
  recommendedSL: number
  recommendedTP: number
  onSelect?: (symbol: string) => void
  onDelete?: (symbol: string) => void
  selected?: boolean
}

export function CoinCard({
  name,
  symbol,
  price,
  change24h,
  holdings,
  value,
  recommendedSL,
  recommendedTP,
  onSelect,
  onDelete,
  selected,
}: CoinCardProps) {
  const isPositiveChange = change24h >= 0

  return (
    <Card className={`transition-shadow ${selected ? "ring-2 ring-primary" : ""}`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">
          {name} ({symbol})
        </CardTitle>
        <div className="flex items-center gap-2">
          {isPositiveChange ? (
            <TrendingUp className="h-4 w-4 text-green-500" />
          ) : (
            <TrendingDown className="h-4 w-4 text-red-500" />
          )}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="More">
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-44">
              <DropdownMenuItem
                onClick={() => onSelect?.(symbol)}
                className="gap-2"
              >
                <Settings2 className="size-4" />
                Update controls
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => onDelete?.(symbol)}
                className="gap-2 text-destructive focus:text-destructive"
                variant="destructive"
              >
                <Trash2 className="size-4" />
                Delete from portfolio
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="text-2xl font-bold">
          {price.toLocaleString("en-US", { style: "currency", currency: "USD" })}
        </div>
        <p className={`${isPositiveChange ? "text-green-500" : "text-red-500"}`}>
          {change24h > 0 ? "+" : ""}
          {change24h.toFixed(2)}% (24h)
        </p>
        <div className="mt-2 text-sm text-muted-foreground">
          <p>
            Holdings: {holdings} {symbol}
          </p>
          <p>Value: {value.toLocaleString("en-US", { style: "currency", currency: "USD" })}</p>
          <p>Rec. SL: {recommendedSL.toLocaleString("en-US", { style: "currency", currency: "USD" })}</p>
          <p>Rec. TP: {recommendedTP.toLocaleString("en-US", { style: "currency", currency: "USD" })}</p>
        </div>
        <Button
          variant={selected ? "secondary" : "outline"}
          className="w-full"
          onClick={() => onSelect?.(symbol)}
          aria-label={`Select ${symbol} to edit controls`}
        >
          {selected ? "Selected" : "Select"}
        </Button>
      </CardContent>
    </Card>
  )
}
