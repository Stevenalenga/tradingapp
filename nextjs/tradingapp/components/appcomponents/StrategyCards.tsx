import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Lightbulb, TrendingUp, Shield } from "lucide-react"

interface StrategyCardsProps {
  strategies: Array<{
    title: string
    description: string
    type: "bullish" | "bearish" | "neutral"
  }>
}

export function StrategyCards({ strategies }: StrategyCardsProps) {
  const getTypeIcon = (type: "bullish" | "bearish" | "neutral") => {
    switch (type) {
      case "bullish":
        return <TrendingUp className="h-6 w-6 text-green-500" />
      case "bearish":
        return <TrendingUp className="h-6 w-6 text-red-500 rotate-180" /> // Using TrendingUp rotated for bearish
      case "neutral":
        return <Shield className="h-6 w-6 text-blue-500" />
      default:
        return <Lightbulb className="h-6 w-6 text-gray-500" />
    }
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {strategies.map((strategy, index) => (
        <Card key={index}>
          <CardHeader className="flex flex-row items-center gap-4">
            {getTypeIcon(strategy.type)}
            <div className="grid gap-1">
              <CardTitle>{strategy.title}</CardTitle>
              <CardDescription>{strategy.description}</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">This is a placeholder for detailed strategy insights.</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
