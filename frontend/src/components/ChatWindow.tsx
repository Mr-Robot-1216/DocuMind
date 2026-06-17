import { useEffect, useRef, useState } from "react";
import { SendIcon } from "lucide-react";
import { MessageBubble } from "@/components/MessageBubble";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import type { DisplayMessage } from "@/lib/useChat";

interface ChatWindowProps {
  messages: DisplayMessage[];
  isStreaming: boolean;
  error: string | null;
  hasDocuments: boolean;
  onSend: (text: string) => void;
}

export function ChatWindow({ messages, isStreaming, error, hasDocuments, onSend }: ChatWindowProps) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    onSend(input);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <ScrollArea className="min-h-0 flex-1 px-4">
        <div className="flex flex-col gap-3 py-4">
          {messages.length === 0 && (
            <p className="text-center text-sm text-muted-foreground">
              {hasDocuments
                ? "Ask a question about your documents."
                : "Upload a document to this collection, then ask a question about it."}
            </p>
          )}
          {messages.map((message, i) => (
            <MessageBubble key={i} message={message} />
          ))}
          {error && <p className="text-center text-sm text-destructive">{error}</p>}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      <form onSubmit={handleSubmit} className="flex items-end gap-2 border-t p-4">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={hasDocuments ? "Ask a question..." : "Upload a document first"}
          disabled={!hasDocuments || isStreaming}
          rows={1}
          className="min-h-9 resize-none"
        />
        <Button type="submit" size="icon" disabled={!hasDocuments || isStreaming || !input.trim()}>
          <SendIcon />
        </Button>
      </form>
    </div>
  );
}
