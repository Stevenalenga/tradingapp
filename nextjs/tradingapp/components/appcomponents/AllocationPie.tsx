import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts" // Assuming recharts for charting

interface AllocationPieProps {
  data: Array<{
    name: string
    value: number
    color: string
  }>
}

// Dummy data for preview if no data is provided
const defaultData = [
  { name: "Bitcoin", value: 400, color: "#FF9900" },
  { name: "Ethereum", value: 300, color: "#627EEA" },
  { name: "Cardano", value: 200, color: "#0033AD" },
  { name: "Solana", value: 100, color: "#9945FF" },
  { name: "Other", value: 50, color: "#CCCCCC" },
]

export function AllocationPie({ data = defaultData }: AllocationPieProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Portfolio Allocation</CardTitle>
      </CardHeader>
      <CardContent className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} cx="50%" cy="50%" labelLine={false} outerRadius={80} fill="#8884d8" dataKey="value">
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
