 
import { ChatKit, useChatKit } from "@openai/chatkit-react";
import {
  CHATKIT_API_URL,
  CHATKIT_API_DOMAIN_KEY,
  STARTER_PROMPTS,
  PLACEHOLDER_INPUT,
  GREETING,
} from "../lib/config";
export function ChatKitPanel() {

  const SAMPLE_ENTITIES = [
    {
      id: "doc_1",
      title: "Sample Document",
      group: "Meetings",
      interactive: true,
      data: { summary: "A placeholder document for demos." },
    },
    {
      id: "agenda_1",
      title: "Sample Agenda",
      group: "Samples",
      interactive: true,
      data: { summary: "A sample meeting agenda." },
    },
    {
      id: "review_1",
      title: "Sample Review",
      group: "Samples",
      interactive: true,
      data: { summary: "A mock review item for testing." },
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

  return (
    <div className="h-full w-full overflow-hidden">
      <ChatKit control={chatkit.control} className="block h-full w-full" />
    </div>
  );
}
