import { ChatKitPanel } from "./ChatKitPanel";

export default function Home() {

  return (
    <div className="min-h-screen bg-white">
      <main className="w-full">
        <div className="h-screen">
          <div className="h-full overflow-hidden rounded-none">
            <ChatKitPanel />
          </div>
        </div>
      </main>
    </div>
  );
}
