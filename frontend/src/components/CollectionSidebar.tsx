import { useState } from "react";
import { MessageSquareIcon, PlusIcon, Trash2Icon } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import type { Collection } from "@/lib/api";

interface CollectionSidebarProps {
  collections: Collection[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onCreate: (name: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

export function CollectionSidebar({ collections, selectedId, onSelect, onCreate, onDelete }: CollectionSidebarProps) {
  const [isCreating, setIsCreating] = useState(false);
  const [name, setName] = useState("");

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    await onCreate(name.trim());
    setName("");
    setIsCreating(false);
  };

  return (
    <Sidebar>
      <SidebarHeader className="gap-2 p-3">
        <h1 className="px-1 text-lg font-semibold">DocuMind</h1>
        {isCreating ? (
          <form onSubmit={handleCreate} className="flex gap-1">
            <Input
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              onBlur={() => !name.trim() && setIsCreating(false)}
              placeholder="Collection name"
              className="h-8"
            />
            <Button type="submit" size="sm" className="h-8">
              Add
            </Button>
          </form>
        ) : (
          <Button variant="outline" size="sm" onClick={() => setIsCreating(true)}>
            <PlusIcon />
            New collection
          </Button>
        )}
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Collections</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {collections.map((collection) => (
                <SidebarMenuItem key={collection.id}>
                  <SidebarMenuButton isActive={collection.id === selectedId} onClick={() => onSelect(collection.id)}>
                    <MessageSquareIcon />
                    <span className="truncate">{collection.name}</span>
                    {collection.document_count !== undefined && (
                      <span className="ml-auto text-xs text-muted-foreground">{collection.document_count}</span>
                    )}
                  </SidebarMenuButton>
                  <AlertDialog>
                    <AlertDialogTrigger
                      render={
                        <SidebarMenuAction showOnHover>
                          <Trash2Icon />
                        </SidebarMenuAction>
                      }
                    />
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Delete "{collection.name}"?</AlertDialogTitle>
                        <AlertDialogDescription>
                          This permanently deletes the collection, its documents, embeddings, and chat history. This
                          cannot be undone.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction variant="destructive" onClick={() => onDelete(collection.id)}>
                          Delete
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </SidebarMenuItem>
              ))}
              {collections.length === 0 && (
                <p className="px-2 py-1 text-sm text-muted-foreground">No collections yet.</p>
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
