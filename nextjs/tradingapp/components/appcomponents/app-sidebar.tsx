"use client"
import Link from "next/link"
import { SidebarHeader } from "@/components/ui/sidebar"
import { useRouter } from "next/navigation"

import {
  LayoutDashboard,
  MessageSquare,
  LineChart,
  Settings,
  Wallet,
  ChevronDown,
  User2,
  ChevronUp,
  User,
  CreditCard,
  FolderKanban,
  Plus,
  Pencil,
  Trash2,
  ArrowRightLeft,
} from "lucide-react"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
  SidebarRail,
  SidebarMenuAction,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible" // Added for collapsible menu
import dynamic from "next/dynamic"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"

const PortfolioSwitcher = dynamic(
  () => import("./PortfolioSwitcher").then((m) => m.PortfolioSwitcher),
  { ssr: false }
)

export function AppSidebar() {
  const mainNavigation = [
    {
      title: "Dashboard",
      href: "/dashboard",
      icon: LayoutDashboard,
    },
    {
      title: "Agent Chat",
      href: "/agent",
      icon: MessageSquare,
    },
    {
      title: "Charts",
      href: "/charts",
      icon: LineChart,
    },
  ]

  const settingsNavigation = [
    {
      title: "Preferences",
      href: "/settings",
      icon: Settings,
    },
    {
      title: "Account",
      href: "/settings/account",
      icon: User,
    },
    {
      title: "Billing",
      href: "/settings/billing",
      icon: CreditCard,
    },
  ]

  const router = useRouter();
  const { toggleSidebar } = useSidebar()

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <button
              type="button"
              className="flex w-full items-center gap-2 px-2 py-1.5 rounded-md hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus:outline-none"
              onClick={toggleSidebar}
              aria-label="Toggle sidebar"
              title="Toggle sidebar"
            >
              <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                <Wallet className="size-4" />
              </div>
      
            </button>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Main</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {mainNavigation.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <Link href={item.href}>
                      <item.icon />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}

              {/* Portfolio dropdown menu */}
              <SidebarMenuItem>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <SidebarMenuButton>
                      <FolderKanban />
                      <span>Portfolio</span>
                      <ChevronDown className="ml-auto" />
                    </SidebarMenuButton>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent className="w-[--radix-popper-anchor-width]" align="start">
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.preventDefault()
                        // Open the PortfolioSwitcher to choose name via its inline create action
                        // We navigate to dashboard where the editor lives, if needed
                        router.push("/dashboard")
                      }}
                      className="gap-2"
                    >
                      <Plus className="size-4" />
                      Create
                    </DropdownMenuItem>

                    <DropdownMenuItem
                      onClick={(e) => {
                        e.preventDefault()
                        // Navigate to dashboard and let user edit via PortfolioEditor and currently selected portfolio
                        router.push("/dashboard")
                      }}
                      className="gap-2"
                    >
                      <Pencil className="size-4" />
                      Edit
                    </DropdownMenuItem>

                    <DropdownMenuItem
                      onClick={(e) => {
                        e.preventDefault()
                        // Open the switcher popover by routing to dashboard first; deletion is supported in switcher
                        router.push("/dashboard")
                      }}
                      className="gap-2 text-destructive focus:text-destructive"
                    >
                      <Trash2 className="size-4" />
                      Delete
                    </DropdownMenuItem>

                    <DropdownMenuItem
                      onClick={(e) => {
                        e.preventDefault()
                        // Navigate to a portfolio area; we route to dashboard where PortfolioSwitcher is available
                        router.push("/dashboard")
                      }}
                      className="gap-2"
                    >
                      <ArrowRightLeft className="size-4" />
                      Navigate
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarSeparator />

        <SidebarGroup>
          <Collapsible defaultOpen className="group/collapsible">
            <SidebarGroupLabel asChild>
              <CollapsibleTrigger className="w-full">
                Settings
                <ChevronDown className="ml-auto transition-transform group-data-[state=open]/collapsible:rotate-180" />
              </CollapsibleTrigger>
            </SidebarGroupLabel>
            <CollapsibleContent>
              <SidebarGroupContent>
                <SidebarMenu>
                  {settingsNavigation.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton asChild>
                        <Link href={item.href}>
                          <item.icon />
                          <span>{item.title}</span>
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </CollapsibleContent>
          </Collapsible>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton>
                  <User2 /> Username
                  <ChevronUp className="ml-auto" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent side="top" className="w-[--radix-popper-anchor-width]">
                <DropdownMenuItem asChild>
                  <Link href="/settings/account">
                    <span>Account</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link href="/settings/billing">
                    <span>Billing</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    // Replace with your sign out logic
                    router.push("/signout")
                  }}
                >
                  <span>Sign out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
