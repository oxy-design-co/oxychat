# How This ChatKit App Works

This document explains how the ChatKit starter application works in simple terms.

## What Is This Project?

This is a chat application that uses OpenAI's ChatKit framework. Think of it as a demo that shows you how to build a smart chatbot with a nice user interface. The bot can do two main things:

1. Show weather information for any location
2. Switch between light and dark themes

## The Big Picture

The project has two main parts that work together:

- **Frontend** (what you see in the browser)
- **Backend** (the server that runs the AI)

They talk to each other through the internet. The frontend sends your messages to the backend, the backend asks OpenAI's AI what to say back, and then sends the response to the frontend.

## Frontend: The User Interface

The frontend is built with React and runs in your web browser at `http://127.0.0.1:5170`.

### Key Files

- `frontend/src/App.tsx` - The starting point that sets up the app
- `frontend/src/components/Home.tsx` - The main page layout with chat
- `frontend/src/components/ChatKitPanel.tsx` - The chat window where you talk to the bot
- `frontend/src/lib/config.ts` - Settings like the greeting message and starter prompts

### What Happens in the Frontend?

1. You type a message in the chat box
2. The ChatKit component sends it to the backend through `/chatkit` 
3. The backend processes it and streams the response back
4. The chat window displays the AI's reply

When the AI calls special tools (like switching the theme), the frontend listens for these events and updates the page.

### Theme Switching

The app supports light and dark modes. When you ask to switch themes, the bot calls a special function that tells the frontend to change the colors. The setting is saved in your browser so it remembers your preference next time.

## Backend: The AI Server

The backend is built with FastAPI (a Python web framework) and runs at `http://127.0.0.1:8000`.

### Key Files

- `backend/app/main.py` - Creates the web server and defines the API routes
- `backend/app/chat.py` - Sets up the ChatKit server and defines the AI agent
- `backend/app/constants.py` - Contains the instructions that guide the AI's behavior
- `backend/app/facts.py` - (removed) previously stored facts in memory
- `backend/app/weather.py` - Fetches weather data
- `backend/app/memory_store.py` - Keeps track of chat threads and messages

### The AI Agent

The AI agent is created in `chat.py` and has two tools it can use:

1. **switch_theme** - Changes between light and dark mode
2. **get_weather** - Looks up weather and shows it in a widget

The agent follows instructions from `constants.py` that tell it:
- To ask users about themselves
- To only help with ChatKit questions and weather
- To politely decline other types of requests

### How It Processes Messages

1. Your message arrives at the `/chatkit` endpoint
2. The ChatKit server passes it to the AI agent
3. The agent (powered by GPT-4) decides what to do
4. If it needs to use a tool (like switching theme or getting weather), it calls that function
5. The response streams back to the frontend in real-time

### Memory and Storage

Chat threads are stored in memory for this demo. A real app would use a proper database.

## How Frontend and Backend Talk

The frontend proxies requests to the backend through Vite's development server:

1. Frontend at `http://127.0.0.1:5170` receives your input
2. Vite forwards `/chatkit` requests to `http://127.0.0.1:8000/chatkit`
3. Backend processes the request and streams back the response
4. Frontend displays the response in the chat window

This setup is configured in `frontend/vite.config.ts`.

## The Three Main Features

### 1. Weather Lookup

When you ask "What's the weather in Tokyo?":

1. The AI calls the `get_weather` tool with "Tokyo"
2. The backend fetches real weather data
3. It creates a widget with current conditions and forecast
4. The widget streams to the frontend
5. A visual weather card appears in the chat

The weather feature uses a real weather API to get current conditions and forecasts.

### 2. Theme Switching

When you say "Switch to dark mode":

1. The AI calls the `switch_theme` tool with "dark"
2. The backend sends a client tool call to the frontend
3. The frontend changes the CSS classes
4. The entire page switches to dark colors
5. The preference is saved in browser storage

## Running the Application

### Backend First

```bash
cd backend
uv sync
export OPENAI_API_KEY=sk-proj-your-key-here
uv run uvicorn app.main:app --reload --port 8000
```

This installs Python packages and starts the API server.

### Frontend Second

```bash
cd frontend
pnpm install
pnpm run dev
```

This installs JavaScript packages and starts the development server.

### Both Together

From the main directory, run the backend and frontend in separate terminals using the steps above.

## Environment Variables

The app uses these settings:

- `OPENAI_API_KEY` - Your OpenAI API key (required for the backend)
- `VITE_CHATKIT_API_DOMAIN_KEY` - Domain security key (use any placeholder locally)
- `VITE_CHATKIT_API_URL` - ChatKit endpoint (defaults to `/chatkit`)
- `BACKEND_URL` - Where the backend runs (defaults to `http://127.0.0.1:8000`)

For local development, you only need to set `OPENAI_API_KEY`. The others have good defaults.

## The ChatKit Protocol

ChatKit handles the complex parts of building a chat interface:

- Message streaming (responses appear word by word)
- Thread management (keeping track of conversations)
- Tool calling (letting the AI trigger actions)
- Widget rendering (showing rich content like weather cards)
- Error handling (displaying problems to users)

You define the AI's behavior and tools, and ChatKit handles the rest.

## Customizing the Agent

To change what the agent can do, edit `backend/app/constants.py`:

- Change `INSTRUCTIONS` to modify the agent's personality and rules
- Change `MODEL` to use a different AI model

To add new tools, create functions in `backend/app/chat.py` decorated with `@function_tool`. The agent will automatically learn about them and use them when appropriate.

## What Happens Behind the Scenes

Here's the complete flow when you type "What's the weather in Tokyo?":

1. You type in the chat and press enter
2. ChatKit component sends message to `/chatkit`
3. Vite proxy forwards to backend at port 8000
4. FastAPI receives the request in `main.py`
5. ChatKit server in `chat.py` gets the message
6. The agent processes the message
7. AI decides to call `get_weather` with "Tokyo"
8. Backend streams a weather widget
9. Frontend renders the widget and the AI's reply
10. Everything is complete

All of this happens in about one second.

## Key Concepts

- **Agent**: The AI that decides what to do with each message
- **Tools**: Functions the AI can call to perform actions
- **Client Tools**: Special tools that run in the browser (like theme switching)
- **Widgets**: Rich UI elements that display in the chat (like weather cards)
- **Thread**: A single conversation with its message history
- **Store**: Where threads and messages are saved
- **Streaming**: Sending the response piece by piece as it generates

## Files You'll Edit Most

When building your own app:

- `backend/app/constants.py` - Change the AI's instructions
- `backend/app/chat.py` - Add new tools
- `frontend/src/lib/config.ts` - Change greeting and starter prompts
- `frontend/src/components/Home.tsx` - Modify the page layout

## Next Steps

After understanding this starter app, check out the examples:

- `examples/customer-support` - Airline support workflow
- `examples/knowledge-assistant` - Document search agent
- `examples/marketing-assets` - Creative marketing workflow

Each example shows different ways to use ChatKit for real-world tasks.

