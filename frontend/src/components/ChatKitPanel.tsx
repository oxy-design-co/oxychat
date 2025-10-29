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
      title: "Q3 Planning — ACME (Sep 12, 2025)",
      group: "Meetings",
      interactive: true,
      data: { summary: "Roadmap, risks, budgets." },
    },
    {
      id: "doc_2",
      title: "Launch Sync — Phoenix App (Sep 18, 2025)",
      group: "Meetings",
      interactive: true,
      data: { summary: "Release checklist, blockers, owners." },
    },
    {
      id: "doc_3",
      title: "Client Review — Oxy Site (Sep 23, 2025)",
      group: "Meetings",
      interactive: true,
      data: { summary: "Feedback, scope changes, next steps." },
    },
    {
      id: "doc_4",
      title: "Research Debrief — Growth Experiments (Sep 25, 2025)",
      group: "Meetings",
      interactive: true,
      data: { summary: "Findings, hypotheses, priorities." },
    },
    {
      id: "doc_5",
      title: "Postmortem — Campaign Alpha (Sep 27, 2025)",
      group: "Meetings",
      interactive: true,
      data: { summary: "Outcomes, lessons, action items." },
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
