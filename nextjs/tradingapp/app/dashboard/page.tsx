import { CoinCard } from "@/components/appcomponents/CoinCard"
import { StopLossInput } from "@/components/appcomponents/StopLossInput"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

export default function DashboardPage() {
  const dummyCoinData = {
    name: "Bitcoin",
    symbol: "BTC",
    price: 65000,
    change24h: 2.5,
    holdings: 0.5,
    value: 32500,
    recommendedSL: 60000,
    recommendedTP: 70000,
  }

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-6">
      <h2 className="text-2xl font-bold">Portfolio Overview</h2>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <CoinCard {...dummyCoinData} />
        <Card>
          <CardHeader>
            <CardTitle>Recommended SL/TP</CardTitle>
          </CardHeader>
          <CardContent>
            <p>Bitcoin (BTC):</p>
            <p>Stop Loss: $60,000</p>
            <p>Take Profit: $70,000</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Set Your Risk Controls</CardTitle>
          </CardHeader>
          <CardContent>
            <StopLossInput coinSymbol="BTC" />
          </CardContent>
        </Card>
      </div>
      <div className="min-h-[300px] rounded-xl border border-dashed p-4 text-center text-muted-foreground flex items-center justify-center">
        Your portfolio chart will appear here.
      </div>
    </div>
  )
}
