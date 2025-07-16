"use client"

import type React from "react"
import { useSidebar, SidebarInset, SidebarTrigger } from "@/components/ui/sidebar"

export function MainContentWrapper({ children }: { children: React.ReactNode }) {
  const { open, setOpen, isMobile } = useSidebar()

  const handleMainContentClick = () => {
    // Only collapse if the sidebar is currently open (expanded) and it's not a mobile device.
    // On mobile, the Sheet component used by the sidebar already handles closing on outside click.
    if (open && !isMobile) {
      setOpen(false)
    }
  }

  return (
    <SidebarInset onClick={handleMainContentClick}>
      <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
        <SidebarTrigger className="-ml-1" />
        <h1 className="text-lg font-semibold">Crypto Dashboard</h1>
      </header>
      {children}
    </SidebarInset>
  )
}
