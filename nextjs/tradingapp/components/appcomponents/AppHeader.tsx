"use client"

import { SidebarTrigger } from "@/components/ui/sidebar"
import dynamic from "next/dynamic"

const PortfolioSwitcher = dynamic(
  () => import("./PortfolioSwitcher").then((m) => m.PortfolioSwitcher),
  { ssr: false }
)

export function AppHeader() {
  return (
    <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
      <div className="flex items-center gap-2">
        <SidebarTrigger className="-ml-1" />
        <h1 className="text-lg font-semibold">Crypto Dashboard</h1>
      </div>
      <div className="ml-auto">
        <div className="w-64">
          <PortfolioSwitcher />
        </div>
      </div>
    </header>
  )
}

export default AppHeader