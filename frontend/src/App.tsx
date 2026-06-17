import { useCallback, useEffect, useState } from "react";
import { ChatWindow } from "@/components/ChatWindow";
import { CollectionSidebar } from "@/components/CollectionSidebar";
import { DocumentUpload } from "@/components/DocumentUpload";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { type Collection, createCollection, deleteCollection, getCollection, listCollections, uploadDocument } from "@/lib/api";
import { useChat } from "@/lib/useChat";

function App() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedCollection, setSelectedCollection] = useState<Collection | null>(null);

  const { messages, isStreaming, error, sendMessage } = useChat(selectedId);

  const refreshCollections = useCallback(async () => {
    const data = await listCollections();
    setCollections(data);
    return data;
  }, []);

  useEffect(() => {
    refreshCollections().then((data) => {
      if (data.length > 0) setSelectedId(data[0].id);
    });
  }, [refreshCollections]);

  useEffect(() => {
    if (!selectedId) {
      setSelectedCollection(null);
      return;
    }
    getCollection(selectedId).then(setSelectedCollection);
  }, [selectedId]);

  const handleCreate = async (name: string) => {
    const collection = await createCollection(name);
    await refreshCollections();
    setSelectedId(collection.id);
  };

  const handleDelete = async (id: string) => {
    await deleteCollection(id);
    const remaining = await refreshCollections();
    if (selectedId === id) {
      setSelectedId(remaining.length > 0 ? remaining[0].id : null);
    }
  };

  const handleUpload = async (file: File) => {
    if (!selectedId) return;
    await uploadDocument(selectedId, file);
    const updated = await getCollection(selectedId);
    setSelectedCollection(updated);
    await refreshCollections();
  };

  return (
    <SidebarProvider className="h-svh">
      <CollectionSidebar
        collections={collections}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onCreate={handleCreate}
        onDelete={handleDelete}
      />
      <SidebarInset>
        <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger />
          <Separator orientation="vertical" className="h-4!" />
          <h2 className="font-medium">{selectedCollection?.name ?? "DocuMind"}</h2>
        </header>

        {selectedCollection ? (
          <div className="flex min-h-0 flex-1 flex-col">
            <DocumentUpload documents={selectedCollection.documents ?? []} onUpload={handleUpload} />
            <div className="min-h-0 flex-1">
              <ChatWindow
                messages={messages}
                isStreaming={isStreaming}
                error={error}
                hasDocuments={(selectedCollection.documents?.length ?? 0) > 0}
                onSend={sendMessage}
              />
            </div>
          </div>
        ) : (
          <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
            Create a collection to get started.
          </div>
        )}
      </SidebarInset>
    </SidebarProvider>
  );
}

export default App;
