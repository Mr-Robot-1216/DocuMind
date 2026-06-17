import { useCallback, useEffect, useState } from "react";
import { type ChatMessage, type Source, getMessages, streamChat } from "@/lib/api";

export interface DisplayMessage extends ChatMessage {
  sources?: Source[];
}

export function useChat(collectionId: string | null) {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!collectionId) {
      setMessages([]);
      return;
    }
    let cancelled = false;
    getMessages(collectionId).then((history) => {
      if (!cancelled) setMessages(history);
    });
    return () => {
      cancelled = true;
    };
  }, [collectionId]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!collectionId || !text.trim() || isStreaming) return;

      setError(null);
      setMessages((prev) => [...prev, { role: "user", content: text }, { role: "assistant", content: "", sources: [] }]);
      setIsStreaming(true);

      try {
        await streamChat(collectionId, text, {
          onSources: (sources) => {
            setMessages((prev) => {
              const next = [...prev];
              next[next.length - 1] = { ...next[next.length - 1], sources };
              return next;
            });
          },
          onToken: (token) => {
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              next[next.length - 1] = { ...last, content: last.content + token };
              return next;
            });
          },
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Something went wrong");
      } finally {
        setIsStreaming(false);
      }
    },
    [collectionId, isStreaming],
  );

  return { messages, isStreaming, error, sendMessage };
}
