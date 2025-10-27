import { ChatKitPanel } from "./ChatKitPanel";
import { useFacts } from "../hooks/useFacts";

export default function Home() {
  const { refresh, performAction } = useFacts();

  return (
    <div className="min-h-screen bg-white">
      <main className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 pb-8">
        <div className="h-screen">
          <div className="h-full overflow-hidden rounded-none">
            <ChatKitPanel
              onWidgetAction={performAction}
              onResponseEnd={refresh}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
