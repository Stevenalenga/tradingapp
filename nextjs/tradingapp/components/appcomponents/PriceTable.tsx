import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

interface PriceTableProps {
  data: Array<{
    coin: string
    price: number
    change24h: number
    volume: number
  }>
}

export function PriceTable({ data }: PriceTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Current Market Prices</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Coin</TableHead>
              <TableHead>Price</TableHead>
              <TableHead>24h Change</TableHead>
              <TableHead>24h Volume</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((item) => (
              <TableRow key={item.coin}>
                <TableCell className="font-medium">{item.coin}</TableCell>
                <TableCell>{item.price.toLocaleString("en-US", { style: "currency", currency: "USD" })}</TableCell>
                <TableCell className={item.change24h >= 0 ? "text-green-500" : "text-red-500"}>
                  {item.change24h > 0 ? "+" : ""}
                  {item.change24h.toFixed(2)}%
                </TableCell>
                <TableCell>{item.volume.toLocaleString("en-US")}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
