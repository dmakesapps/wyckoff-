import { BrowserRouter, Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import { ChatContainer } from "./components/ChatContainer";
import PositionsPage from "./pages/PositionsPage";
import WatchlistsPage from "./pages/WatchlistsPage";
import NewsPage from "./pages/NewsPage";
import IdeasPage from "./pages/IdeasPage";
import MarketDashboardPage from "./pages/MarketDashboardPage";
import ChartPage from "./pages/ChartPage";
import "./App.css";

import { ChatProvider } from "./context/ChatContext";

function App() {
  return (
    <BrowserRouter>
      <ChatProvider>
        <div className="app-layout">
          <Sidebar />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<ChatContainer />} />
              <Route path="/chat/:id" element={<ChatContainer />} />
              <Route path="/market" element={<MarketDashboardPage />} />
              <Route path="/chart/:symbol" element={<ChartPage />} />
              <Route path="/positions" element={<PositionsPage />} />
              <Route path="/watchlists" element={<WatchlistsPage />} />
              <Route path="/news" element={<NewsPage />} />
              <Route path="/ideas" element={<IdeasPage />} />
            </Routes>
          </main>
        </div>
      </ChatProvider>
    </BrowserRouter>
  );
}

export default App;
