"use client"

import type React from "react"

import { useChat } from "ai/react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"

export default function AgentChat() {
  const { messages, input, handleInputChange, handleSubmit } = useChat({ api: "/api/chat" })
  const [isTyping, setIsTyping] = useState(false)

  const onSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    setIsTyping(true)
    handleSubmit(e)
    setIsTyping(false)
  }

  return (
    <div className="flex flex-1 flex-col p-4 md:p-6">
      <Card className="flex flex-col flex-1">
        <CardHeader>
          <CardTitle>Analysis Agent</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col">
          <ScrollArea className="flex-1 pr-4">
            {messages.length === 0 && (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                Start a conversation with your analysis agent.
              </div>
            )}
            {messages.map((m) => (
              <div key={m.id} className={`${m.role === "user" ? "text-right" : "text-left"}`}>
                <span
                  className={`${m.role === "user" ? "bg-blue-500 text-white" : "bg-gray-200 text-black"} inline-block p-3 rounded-lg max-w-[70%]`}
                >
                  {m.content}
                </span>
              </div>
            ))}
            {isTyping && (
              <div className="text-left">
                <span className="inline-block p-3 rounded-lg bg-gray-200 text-black">Agent is typing...</span>
              </div>
            )}
          </ScrollArea>
        </CardContent>
        <CardFooter>
          <form onSubmit={onSubmit} className="flex w-full space-x-2">
            <Input
              value={input}
              onChange={handleInputChange}
              placeholder="Ask your agent about market trends, predictions, or portfolio analysis..."
              className="flex-grow"
            />
            <Button type="submit" disabled={isTyping}>
              Send
            </Button>
          </form>
        </CardFooter>
      </Card>
    </div>
  )
}
