# Alphabot - Feature Documentation

> **Last Updated:** January 24, 2026  
> **Purpose:** Reference guide for API integration (Kimi API)

---

## 📁 Project Structure

```
src/
├── App.tsx                         # Main app entry point with routing
├── App.css                         # Global styles (1300+ lines)
├── components/
│   ├── ChatContainer.tsx           # Main chat state management
│   ├── PromptInputWithActions.tsx  # User input component
│   ├── MarketFeed.tsx              # Market news ticker (welcome screen)
│   ├── Sidebar.tsx                 # Collapsible sidebar navigation
│   └── ui/
│       ├── button.tsx              # Reusable button component
│       ├── chat-message.tsx        # Individual message bubbles
│       ├── prompt-input.tsx        # Base input components
│       └── text-effect.tsx         # Animated text component
├── pages/
│   ├── PositionsPage.tsx           # Portfolio/positions view
│   ├── WatchlistsPage.tsx          # Ticker watchlists
│   ├── NewsPage.tsx                # Today's market news
│   └── IdeasPage.tsx               # Research notes
```

---

## 🎯 Core Features

### 1. Chat Interface (`ChatContainer.tsx`)

**Current Implementation:**
- Manages conversation state with `useState`
- Stores messages as an array of `ChatMessageProps`
- Handles user message submission
- Simulates bot responses (placeholder)

**API Integration Points:**
```typescript
// Current placeholder logic to replace:
const handleSendMessage = (content: string) => {
  // 1. Add user message to state
  // 2. Set typing indicator
  // 3. REPLACE: Currently uses setTimeout with random responses
  //    NEED: Call Kimi API here and stream/display response
};
```

**Message Interface:**
```typescript
interface ChatMessageProps {
  id: string;
  role: "user" | "assistant";
  content: string;
}
```

**State Variables:**
- `messages`: Array of chat messages
- `isTyping`: Boolean for typing indicator visibility
- `hasMessages`: Derived boolean to toggle between welcome/chat views

---

### 2. User Input (`PromptInputWithActions.tsx`)

**Features:**
- Text input with auto-resize
- File attachment support (UI ready, not connected)
- Send button
- Keyboard submit (Enter key)

**Props:**
```typescript
interface PromptInputWithActionsProps {
  onSend?: (message: string) => void;  // Callback when user sends message
}
```

**File Attachment State:**
```typescript
const [files, setFiles] = useState<File[]>([]);
```
> **Note:** File attachments are stored but NOT sent anywhere yet. Will need to handle file uploads with the API.

---

### 3. Chat Messages (`chat-message.tsx`)

**Features:**
- Animated entrance (fade + slide up)
- Different styling for user vs assistant messages
- User messages: Right-aligned, filled background
- Assistant messages: Left-aligned, transparent with border

**Animation:**
```typescript
initial={{ opacity: 0, y: 20 }}
animate={{ opacity: 1, y: 0 }}
transition={{ duration: 0.4, ease: "easeOut" }}
```

---

### 4. Typing Indicator

**Location:** `ChatContainer.tsx`

**Current Behavior:**
- Shows three bouncing green dots while `isTyping` is true
- Animated with CSS keyframes

**API Integration:**
- Set `isTyping(true)` when API call starts
- Set `isTyping(false)` when response is complete

---

### 5. Market Feed (`MarketFeed.tsx`)

**Features:**
- Displays rotating market news/topics
- Auto-cycles every 4 seconds
- Manual navigation via dots
- Smooth fade animations

**Data Structure:**
```typescript
interface MarketTopic {
  category: string;   // e.g., "Markets", "Crypto", "Earnings"
  headline: string;   // The news headline
}
```

**Current Data:** Placeholder array of 6 market topics

**API Integration Options:**
1. Fetch real market data from a finance API
2. Have Kimi generate current market insights
3. Keep as static/curated content

---

### 6. Welcome Screen

**Components:**
- "Welcome to alphabot" animated title (TextEffect)
- Centered prompt input
- Market feed on the right side

**Behavior:**
- Visible when `hasMessages === false`
- Fades out when user sends first message
- Input moves to bottom of screen

---

### 7. Text Effect (`text-effect.tsx`)

**Animation Presets:**
- `fade`: Opacity transition
- `slide`: Opacity + Y-axis movement  
- `blur`: Opacity + blur filter

**Props:**
```typescript
interface TextEffectProps {
  children: string;
  per?: "word" | "char" | "line";  // How to split text
  preset?: "fade" | "slide" | "blur";
  delay?: number;  // Seconds before animation starts
  trigger?: boolean;  // Control animation state
}
```

---

## 🎨 Design System

### Colors (CSS Variables)
```css
--bg: #0f1417;           /* Background */
--fg: #f5f7fa;           /* Foreground/text */
--card-bg: #1a1f24;      /* Card backgrounds */
--card-border: #2a3038;  /* Borders */
--accent: #00ff85;       /* Primary accent (green) */
--accent-dark: #004225;  /* Dark green */
--accent-pink: #ff3366;  /* Secondary accent */
```

### Typography
- **Primary Font:** Libre Baskerville (serif)
- **Font Weights:** 400 (regular), 700 (bold)

---

## 🔌 API Integration Checklist

When integrating the Kimi API, you'll need to:

### 1. Create API Service
```typescript
// Suggested: src/services/kimi.ts
export async function sendMessage(
  message: string,
  conversationHistory: ChatMessageProps[]
): Promise<string> {
  // Call Kimi API
  // Return assistant response
}
```

### 2. Update ChatContainer.tsx
Replace the placeholder `setTimeout` in `handleSendMessage`:
```typescript
const handleSendMessage = async (content: string) => {
  // Add user message
  const userMessage = { id: Date.now().toString(), role: "user", content };
  setMessages(prev => [...prev, userMessage]);
  
  setIsTyping(true);
  
  try {
    const response = await sendMessage(content, messages);
    const botMessage = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: response,
    };
    setMessages(prev => [...prev, botMessage]);
  } catch (error) {
    // Handle error - show error message to user
  } finally {
    setIsTyping(false);
  }
};
```

### 3. Consider Streaming
For a better UX, implement streaming responses:
- Update `ChatMessageProps` to support partial content
- Use SSE or WebSocket for real-time updates
- Animate text as it streams in

### 4. File Attachments
If Kimi supports file inputs:
- Modify `onSend` callback to include files
- Upload files to storage or send as base64
- Update API service to handle multimodal input

### 5. Conversation Context
Current implementation stores full history in state. Consider:
- Limiting context window (last N messages)
- Summarization for long conversations
- Persisting conversations (localStorage/database)

---

## 📱 Responsive Breakpoints

```css
@media (max-width: 900px) {
  /* Two-column layout stacks to single column */
}
```

---

## 🚀 Future Enhancement Ideas

1. **Message Actions:** Copy, regenerate, edit
2. **Code Highlighting:** For code blocks in responses
3. **Markdown Rendering:** Rich text in messages
4. **Voice Input:** Microphone button
5. **Conversation History:** Sidebar with past chats
6. **Dark/Light Mode Toggle**
7. **Loading States:** Skeleton screens
8. **Error Handling:** Retry buttons, error messages

---

## 📝 Notes

- All animations use Framer Motion
- Component state is local (no global state management yet)
- No authentication implemented
- No data persistence (conversations lost on refresh)
- React Router used for navigation between pages

---

## 🧭 Sidebar (`Sidebar.tsx`)

**Features:**
- Collapsible sidebar (Claude-style)
- Collapsed: 56px thin strip with icons only
- Expanded: 260px with full text labels
- Smooth Framer Motion animations

**Sections:**
1. **New Chat** - Green accent button, navigates to `/`
2. **Chats** - Expandable section with recent chat history
3. **Projects** - Expandable section for project folders
4. **My Positions** - Navigate to `/positions`
5. **Watchlists** - Navigate to `/watchlists`
6. **Today's News** - Navigate to `/news`
7. **My Ideas** - Navigate to `/ideas`

**State:**
```typescript
const [isExpanded, setIsExpanded] = useState(false);
const [isChatsOpen, setIsChatsOpen] = useState(true);
const [isProjectsOpen, setIsProjectsOpen] = useState(false);
```

**API Integration:**
- Chat history currently uses placeholder data
- Replace `recentChats` array with real conversation history
- Projects section ready for custom project data

---

## 📊 My Positions Page (`PositionsPage.tsx`)

**Features:**
- Portfolio summary cards (Total Value, Today's Change, Total P&L)
- Individual position cards with:
  - Ticker symbol and name
  - Shares, Avg Cost, Current Price, Value
  - Day change % (green/red badge)
  - Total P&L with percentage

**Data Interface:**
```typescript
interface Position {
  id: string;
  ticker: string;
  name: string;
  shares: number;
  avgCost: number;
  currentPrice: number;
  dayChange: number;
  dayChangePercent: number;
}
```

**API Integration:**
- Replace placeholder `positions` array with real portfolio data
- Connect to brokerage API or user input system
- Real-time price updates

---

## 👁️ Watchlists Page (`WatchlistsPage.tsx`)

**Features:**
- Multiple watchlist cards (expandable)
- Each watchlist shows tickers with price and % change
- "New Watchlist" button

**Data Interface:**
```typescript
interface Watchlist {
  id: string;
  name: string;
  items: WatchlistItem[];
}

interface WatchlistItem {
  id: string;
  ticker: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
}
```

---

## 📰 Today's News Page (`NewsPage.tsx`)

**Features:**
- Market index stats grid (S&P, NASDAQ, DOW, VIX, 10Y, BTC)
- Sentiment bar (bullish vs bearish %)
- News feed with:
  - Category badges (Earnings, Fed, Tech, Crypto, Markets)
  - Sentiment badges (bullish/bearish/neutral)
  - Headlines and summaries
  - Timestamps

**Data Interface:**
```typescript
interface NewsItem {
  id: string;
  category: string;
  headline: string;
  summary: string;
  time: string;
  sentiment: "bullish" | "bearish" | "neutral";
}
```

**API Integration:**
- Connect to market data API for real index values
- Integrate news API or Kimi for sentiment analysis
- Real-time updates

---

## 💡 My Ideas Page (`IdeasPage.tsx`)

**Features:**
- Idea cards with ticker badge, title, notes
- Create new idea form (ticker, title, notes)
- Edit and delete actions
- Pre-formatted notes with line breaks

**Data Interface:**
```typescript
interface Idea {
  id: string;
  ticker: string;
  title: string;
  notes: string;
  createdAt: string;
  updatedAt: string;
}
```

**State:**
- Ideas stored in local state (not persisted)
- Form state for creating new ideas

**API Integration:**
- Save ideas to database/localStorage
- Optionally integrate with Kimi for AI-assisted research

---

## 🛣️ Routing

**Using:** React Router DOM

**Routes:**
```typescript
<Routes>
  <Route path="/" element={<ChatContainer />} />
  <Route path="/chat/:id" element={<ChatContainer />} />
  <Route path="/positions" element={<PositionsPage />} />
  <Route path="/watchlists" element={<WatchlistsPage />} />
  <Route path="/news" element={<NewsPage />} />
  <Route path="/ideas" element={<IdeasPage />} />
</Routes>
```

**Note:** `/chat/:id` route is ready for loading specific conversations
