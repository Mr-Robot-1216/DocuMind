const API_BASE = "/api";

export interface DocumentInfo {
  id: string;
  filename: string;
  chunk_count: number;
  uploaded_at: string;
}

export interface Collection {
  id: string;
  name: string;
  created_at: string;
  document_count?: number;
  documents?: DocumentInfo[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  created_at?: string;
}

export interface Source {
  document_name: string;
  page: number | string | null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export const listCollections = () => request<Collection[]>("/collections");

export const createCollection = (name: string) =>
  request<Collection>("/collections", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });

export const getCollection = (id: string) => request<Collection>(`/collections/${id}`);

export const deleteCollection = (id: string) => request<void>(`/collections/${id}`, { method: "DELETE" });

export const getMessages = (id: string) => request<ChatMessage[]>(`/collections/${id}/messages`);

export const uploadDocument = (collectionId: string, file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return request<DocumentInfo>(`/collections/${collectionId}/documents`, {
    method: "POST",
    body: formData,
  });
};

export interface ChatStreamHandlers {
  onSources?: (sources: Source[]) => void;
  onToken?: (token: string) => void;
  onDone?: () => void;
}

/**
 * Streams a chat response over SSE. Uses fetch + a manual reader instead of
 * EventSource because EventSource cannot send a POST body.
 */
export async function streamChat(
  collectionId: string,
  message: string,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ collection_id: collectionId, message }),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error((await response.text()) || response.statusText);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let separatorIndex: number;
    while ((separatorIndex = buffer.indexOf("\n\n")) !== -1) {
      const rawEvent = buffer.slice(0, separatorIndex);
      buffer = buffer.slice(separatorIndex + 2);

      const eventMatch = rawEvent.match(/^event: (.+)$/m);
      const dataMatch = rawEvent.match(/^data: (.+)$/m);
      if (!eventMatch || !dataMatch) continue;

      const eventType = eventMatch[1];
      const data = JSON.parse(dataMatch[1]);

      if (eventType === "sources") handlers.onSources?.(data as Source[]);
      else if (eventType === "token") handlers.onToken?.((data as { content: string }).content);
      else if (eventType === "done") handlers.onDone?.();
    }
  }
}
