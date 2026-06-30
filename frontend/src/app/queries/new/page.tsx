import { Badge } from "@/components/ui/badge";
import { QuerySubmitForm } from "@/components/dashboard/query-submit-form";

export default function NewQueryPage() {
  return (
    <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 p-6 md:p-10">
      <div className="space-y-2">
        <Badge variant="secondary" className="font-mono text-[10px] uppercase">
          New query
        </Badge>
        <h1 className="text-2xl font-semibold tracking-tight">
          Submit a research topic
        </h1>
        <p className="text-sm text-muted-foreground">
          Configure your investigation and start the async research pipeline.
        </p>
      </div>

      <QuerySubmitForm />
    </div>
  );
}
