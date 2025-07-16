import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { TrendingUp, TrendingDown } from "lucide-react"

interface CoinCardProps {
  name: string
  symbol: string
  price: number
  change24h: number
  holdings: number
  value: number
  recommendedSL: number
  recommendedTP: number
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
}: CoinCardProps) {
  const isPositiveChange = change24h >= 0

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">
          {name} ({symbol})
        </CardTitle>
        {isPositiveChange ? (
          <TrendingUp className="h-4 w-4 text-green-500" />
        ) : (
          <TrendingDown className="h-4 w-4 text-red-500" />
        )}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {price.toLocaleString("en-US", { style: "currency", currency: "USD" })}
        </div>
        <p className={`${isPositiveChange ? "text-green-500" : "text-red-500"}`}>
          {change24h > 0 ? "+" : ""}
          {change24h.toFixed(2)}% (24h)
        </p>
        <div className="mt-4 text-sm text-muted-foreground">
          <p>
            Holdings: {holdings} {symbol}
          </p>
          <p>Value: {value.toLocaleString("en-US", { style: "currency", currency: "USD" })}</p>
          <p>Rec. SL: {recommendedSL.toLocaleString("en-US", { style: "currency", currency: "USD" })}</p>
          <p>Rec. TP: {recommendedTP.toLocaleString("en-US", { style: "currency", currency: "USD" })}</p>
        </div>
      </CardContent>
    </Card>
  )
}
