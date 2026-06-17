import { useRef, useState } from "react";
import { FileTextIcon, UploadIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { DocumentInfo } from "@/lib/api";

interface DocumentUploadProps {
  documents: DocumentInfo[];
  onUpload: (file: File) => Promise<void>;
}

const ACCEPTED_EXTENSIONS = ".pdf,.docx,.xlsx,.xls";

export function DocumentUpload({ documents, onUpload }: DocumentUploadProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setError(null);
    try {
      await onUpload(file);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2 border-b p-4">
      {documents.map((doc) => (
        <Badge key={doc.id} variant="outline" className="gap-1 font-normal">
          <FileTextIcon className="size-3" />
          {doc.filename}
          <span className="text-muted-foreground">({doc.chunk_count} chunks)</span>
        </Badge>
      ))}

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXTENSIONS}
        className="hidden"
        onChange={handleFileChange}
      />
      <Button variant="outline" size="sm" onClick={() => inputRef.current?.click()} disabled={isUploading}>
        <UploadIcon />
        {isUploading ? "Uploading..." : "Upload document"}
      </Button>

      {error && <span className="text-sm text-destructive">{error}</span>}
    </div>
  );
}
