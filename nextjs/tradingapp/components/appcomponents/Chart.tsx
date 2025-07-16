import { CardContent } from "@/components/ui/card"

interface ChartProps {
  coinSymbol: string
}

export function Chart({ coinSymbol }: ChartProps) {
  return (
    <CardContent className="flex items-center justify-center h-full">
      <div className="text-muted-foreground">
        Interactive chart for {coinSymbol} will be rendered here.
        <br />
        (e.g., using Recharts or a custom D3 implementation)
      </div>
    </CardContent>
  )
}
