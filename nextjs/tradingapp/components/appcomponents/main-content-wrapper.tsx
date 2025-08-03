"use client"

import type React from "react"
import { useSidebar, SidebarInset } from "@/components/ui/sidebar"
import { AppHeader } from "@/components/appcomponents/AppHeader"

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
      <AppHeader />
      {children}
    </SidebarInset>
  )
}
