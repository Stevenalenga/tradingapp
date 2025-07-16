import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { LayoutDashboard, MessageSquare, LineChart, ArrowRight } from "lucide-react"

export default function LandingPage() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center p-4 md:p-6">
      {/* Hero Section */}
      <section className="w-full py-12 md:py-24 lg:py-32 xl:py-48 text-center">
        <div className="container px-4 md:px-6">
          <div className="flex flex-col items-center space-y-4">
            <h1 className="text-3xl font-bold tracking-tighter sm:text-5xl md:text-6xl lg:text-7xl/none">
              Your Ultimate Crypto Dashboard
            </h1>
            <p className="mx-auto max-w-[700px] text-muted-foreground md:text-xl">
              Manage your portfolio, get AI-powered insights, and analyze market trends with ease.
            </p>
            <div className="space-x-4">
              <Button asChild size="lg">
                <Link href="/dashboard">
                  Get Started <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button variant="outline" asChild size="lg">
                <Link href="/charts">Learn More</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="w-full py-12 md:py-24 lg:py-32 bg-muted/40">
        <div className="container px-4 md:px-6">
          <div className="grid gap-8 md:grid-cols-3">
            <Card className="flex flex-col items-center text-center p-6">
              <LayoutDashboard className="h-12 w-12 text-primary mb-4" />
              <CardHeader>
                <CardTitle>Portfolio Management</CardTitle>
                <CardDescription>Track your crypto holdings and performance in one place.</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  View real-time values, profit/loss, and recommended stop-loss/take-profit levels.
                </p>
              </CardContent>
            </Card>
            <Card className="flex flex-col items-center text-center p-6">
              <MessageSquare className="h-12 w-12 text-primary mb-4" />
              <CardHeader>
                <CardTitle>AI Analysis Agent</CardTitle>
                <CardDescription>Chat with our intelligent agent for market insights and predictions.</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Get personalized advice and answers to your crypto questions instantly.
                </p>
              </CardContent>
            </Card>
            <Card className="flex flex-col items-center text-center p-6">
              <LineChart className="h-12 w-12 text-primary mb-4" />
              <CardHeader>
                <CardTitle>Interactive Charts</CardTitle>
                <CardDescription>Visualize price data with advanced charting tools.</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Apply indicators, draw trends, and identify key support/resistance levels.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Call to Action Section */}
      <section className="w-full py-12 md:py-24 lg:py-32 text-center">
        <div className="container px-4 md:px-6">
          <div className="flex flex-col items-center space-y-4">
            <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl">
              Ready to take control of your crypto?
            </h2>
            <p className="mx-auto max-w-[700px] text-muted-foreground md:text-xl">
              Join thousands of users who are simplifying their crypto journey with our powerful dashboard.
            </p>
            <Button asChild size="lg">
              <Link href="/dashboard">Start Your Free Trial</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Simple Footer */}
      <footer className="w-full py-6 border-t text-center text-sm text-muted-foreground">
        <div className="container px-4 md:px-6">
          &copy; {new Date().getFullYear()} Crypto Dashboard. All rights reserved.
        </div>
      </footer>
    </div>
  )
}
