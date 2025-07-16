import { Chart } from "@/components/appcomponents/Chart"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

export default function ChartsPage() {
  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-6">
      <h2 className="text-2xl font-bold">Interactive Coin Charts</h2>
      <Card className="flex-1">
        <CardHeader>
          <CardTitle>Bitcoin (BTC) Price Chart</CardTitle>
        </CardHeader>
        <CardContent className="h-[500px]">
          <Chart coinSymbol="BTC" />
        </CardContent>
      </Card>
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Chart Controls</CardTitle>
          </CardHeader>
          <CardContent>
            <p>Timeframe selection, indicators, etc. will go here.</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Market Data</CardTitle>
          </CardHeader>
          <CardContent>
            <p>Volume, market cap, etc. will go here.</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
