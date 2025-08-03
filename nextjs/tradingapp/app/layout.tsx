import type React from "react"
import { cookies } from "next/headers"
import { SidebarProvider } from "@/components/ui/sidebar"
import { AppSidebar } from "../components/appcomponents/app-sidebar"
import { cn } from "@/lib/utils"
import "./globals.css"
import { MainContentWrapper } from "../components/appcomponents/main-content-wrapper"
import { Toaster } from "sonner"
import { PortfolioProvider } from "@/components/appcomponents/PortfolioProvider"

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const cookieStore = await cookies()
  const defaultOpen = cookieStore.get("sidebar:state")?.value === "true"

  return (
    <html lang="en">
      <body className={cn("min-h-screen bg-background font-sans antialiased")}>
        <PortfolioProvider>
          <SidebarProvider defaultOpen={defaultOpen}>
            <AppSidebar />
            <MainContentWrapper>{children}</MainContentWrapper>
          </SidebarProvider>
        </PortfolioProvider>
        <Toaster />
      </body>
    </html>
  )
}
