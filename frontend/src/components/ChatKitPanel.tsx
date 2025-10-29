import { ChatKit, useChatKit } from "@openai/chatkit-react";
import {
  CHATKIT_API_URL,
  CHATKIT_API_DOMAIN_KEY,
  STARTER_PROMPTS,
  PLACEHOLDER_INPUT,
  GREETING,
} from "../lib/config";
import { useEffect } from "react";
export function ChatKitPanel() {

  const SAMPLE_ENTITIES = [
    {
      id: "doc_oxy_weekly_planning",
      title: "Oxy <> Weekly Planning",
      group: "Transcripts",
      interactive: true,
      data: { summary: "" },
    },
    {
      id: "doc_craig_oxy",
      title: "Craig - Oxy",
      group: "Transcripts",
      interactive: true,
      data: { summary: "" },
    },
    {
      id: "doc_andrew_fitasy_check_in",
      title: "Andrew Fitasy Check In",
      group: "Transcripts",
      interactive: true,
      data: { summary: "" },
    },
    {
      id: "doc_oxy_internal_sales_planning",
      title: "Oxy Internal Sales Planning",
      group: "Transcripts",
      interactive: true,
      data: { summary: "" },
    },
    {
      id: "doc_soraban_oxy_weekly_sync",
      title: "Soraban <> Oxy - Weekly Sync",
      group: "Transcripts",
      interactive: true,
      data: { summary: "" },
    },
  ];

  const chatkit = useChatKit({
    api: { url: CHATKIT_API_URL, domainKey: CHATKIT_API_DOMAIN_KEY },
    header: {
      enabled: true,
      title: {
        enabled: true,
        text: "OxyChat",
      },
    },
    theme: {
      colorScheme: 'light',
      radius: 'pill',
      density: 'normal',
      typography: {
          baseSize: 16,
          fontFamily: 'Lora, serif',
          fontSources: [
            {
              family: 'Lora',
              src: 'https://fonts.gstatic.com/s/lora/v37/0QIvMX1D_JOuMwr7I_FMl_E.woff2',
              weight: 400,
              style: 'normal',
              display: 'swap'
            }
        ]
      }
    },
    startScreen: {
      greeting: GREETING,
      prompts: STARTER_PROMPTS,
    },
    composer: {
      placeholder: PLACEHOLDER_INPUT,
    },
    entities: {
      onTagSearch: async (query: string) => {
        const q = query.trim().toLowerCase();
        return SAMPLE_ENTITIES.filter((e) => q === "" || e.title.toLowerCase().includes(q));
      },
      onRequestPreview: async (entity) => {
        return {
          preview: {
            type: "Card",
            children: [
              { type: "Title", value: entity.title },
              { type: "Text", value: entity.data?.summary ?? "Sample item" },
            ],
          },
        };
      },
    },
    threadItemActions: {
      feedback: false,
    },
    onClientTool: async () => ({ success: false }),
    onError: ({ error }) => {
      // ChatKit handles displaying the error to the user
      console.error("ChatKit error", error);
    },
  });

  // Debug: log current active thread id whenever it changes
  useEffect(() => {
    const anyControl = chatkit.control as any;
    const threadId = anyControl?.state?.thread?.id as string | undefined;
    if (threadId) {
      console.debug("[ChatKit] Active thread id:", threadId);
      try {
        localStorage.setItem("chatkit.threadId", threadId);
      } catch {}
    } else {
      console.debug("[ChatKit] No active thread");
    }
  }, [chatkit.control as unknown as undefined]);

  // Optionally: observe previously persisted thread id (for diagnostics only)
  useEffect(() => {
    try {
      const persisted = localStorage.getItem("chatkit.threadId");
      if (persisted) {
        console.debug("[ChatKit] Persisted thread id:", persisted);
      }
    } catch {}
  }, []);

  return (
    <div className="h-full w-full overflow-hidden">
      <ChatKit control={chatkit.control} className="block h-full w-full" />
    </div>
  );
}
