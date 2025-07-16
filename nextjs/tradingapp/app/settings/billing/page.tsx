import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { DollarSign, CreditCard, FileText } from "lucide-react"

export default function BillingPage() {
  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-6">
      <h2 className="text-2xl font-bold">Billing & Subscription</h2>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Current Plan</CardTitle>
            <CardDescription>Your active subscription details.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-primary" />
              <span className="text-lg font-semibold">Pro Plan</span>
              <Badge className="ml-auto">Active</Badge>
            </div>
            <p className="text-sm text-muted-foreground">Next billing date: **July 25, 2025**</p>
            <Button>Change Plan</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Payment Method</CardTitle>
            <CardDescription>Manage your payment information.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-primary" />
              <span className="text-lg font-semibold">Visa ending in 4242</span>
            </div>
            <p className="text-sm text-muted-foreground">Expires 12/2027</p>
            <Button variant="outline">Update Payment Method</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Billing History</CardTitle>
            <CardDescription>View your past invoices.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                <span>Invoice #202506</span>
              </div>
              <Button variant="ghost" size="sm">
                Download PDF
              </Button>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                <span>Invoice #202505</span>
              </div>
              <Button variant="ghost" size="sm">
                Download PDF
              </Button>
            </div>
            <Button variant="outline">View All Invoices</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
