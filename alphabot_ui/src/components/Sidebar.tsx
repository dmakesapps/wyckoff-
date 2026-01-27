"use client";

import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
    Menu,
    Plus,
    MessageSquare,
    FolderOpen,
    TrendingUp,
    Eye,
    Newspaper,
    Lightbulb,
    ChevronDown,
    ChevronRight,
    PanelLeftClose,
    PieChart,
    Trash2,
} from "lucide-react";
import { useChat } from "../hooks/useChat";

interface NavItem {
    id: string;
    label: string;
    icon: React.ReactNode;
    path: string;
}

const navItems: NavItem[] = [
    { id: "market", label: "Market", icon: <TrendingUp size={18} />, path: "/market" },
    { id: "positions", label: "My Positions", icon: <PieChart size={18} />, path: "/positions" },
    { id: "watchlists", label: "Watchlists", icon: <Eye size={18} />, path: "/watchlists" },
    { id: "news", label: "Today's News", icon: <Newspaper size={18} />, path: "/news" },
    { id: "ideas", label: "My Ideas", icon: <Lightbulb size={18} />, path: "/ideas" },
];

export function Sidebar() {
    const [isExpanded, setIsExpanded] = useState(false);
    const [isChatsOpen, setIsChatsOpen] = useState(true);
    const [isProjectsOpen, setIsProjectsOpen] = useState(false);
    const navigate = useNavigate();

    const { chatHistory, currentChatId, startNewChat, loadChat, deleteChat } = useChat();

    const toggleSidebar = () => setIsExpanded(!isExpanded);

    const handleNewChat = () => {
        startNewChat();
        navigate('/');
    };

    const handleLogoClick = () => {
        startNewChat();
        navigate('/');
    };

    const handleChatClick = (chatId: string) => {
        loadChat(chatId);
        navigate('/');
    };

    const handleDeleteChat = (e: React.MouseEvent, chatId: string) => {
        e.preventDefault();
        e.stopPropagation();
        deleteChat(chatId);
    };

    return (
        <>
            {/* Sidebar */}
            <motion.aside
                initial={false}
                animate={{ width: isExpanded ? 260 : 56 }}
                transition={{ duration: 0.2, ease: "easeInOut" }}
                className="sidebar"
            >
                {/* Header */}
                <div className="sidebar-header">
                    <button
                        onClick={toggleSidebar}
                        className="sidebar-toggle"
                        aria-label={isExpanded ? "Collapse sidebar" : "Expand sidebar"}
                    >
                        {isExpanded ? <PanelLeftClose size={20} /> : <Menu size={20} />}
                    </button>

                    <AnimatePresence>
                        {isExpanded && (
                            <motion.span
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="sidebar-title"
                                onClick={handleLogoClick}
                                style={{ cursor: 'pointer' }}
                            >
                                alphabot
                            </motion.span>
                        )}
                    </AnimatePresence>
                </div>

                {/* New Chat Button */}
                <button onClick={handleNewChat} className="sidebar-new-chat">
                    <Plus size={18} />
                    <AnimatePresence mode="popLayout">
                        {isExpanded && (
                            <motion.span
                                initial={{ opacity: 0, width: 0 }}
                                animate={{ opacity: 1, width: "auto" }}
                                exit={{ opacity: 0, width: 0 }}
                                transition={{ duration: 0.2, ease: "easeInOut" }}
                                style={{ overflow: "hidden", whiteSpace: "nowrap" }}
                            >
                                New Chat
                            </motion.span>
                        )}
                    </AnimatePresence>
                </button>

                {/* Scrollable Content */}
                <div className="sidebar-content">
                    {/* Chats Section */}
                    <div className="sidebar-section">
                        <button
                            onClick={() => isExpanded && setIsChatsOpen(!isChatsOpen)}
                            className="sidebar-section-header"
                        >
                            <MessageSquare size={18} />
                            <AnimatePresence>
                                {isExpanded && (
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        className="sidebar-section-title"
                                    >
                                        <span>Chats</span>
                                        {isChatsOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </button>

                        <AnimatePresence>
                            {isExpanded && isChatsOpen && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: "auto", opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    className="sidebar-section-items"
                                >
                                    {chatHistory.length === 0 ? (
                                        <div className="sidebar-empty-state" style={{
                                            padding: '0.75rem 0.5rem',
                                            fontSize: '0.75rem',
                                            color: '#6b7280',
                                            textAlign: 'center'
                                        }}>
                                            No chats yet
                                        </div>
                                    ) : (
                                        chatHistory.slice(0, 10).map((chat) => (
                                            <div
                                                key={chat.id}
                                                onClick={() => handleChatClick(chat.id)}
                                                className={`sidebar-chat-item ${chat.id === currentChatId ? 'sidebar-chat-item-active' : ''}`}
                                                style={{ position: 'relative', cursor: 'pointer' }}
                                            >
                                                <span className="sidebar-chat-title">{chat.title}</span>
                                                <button
                                                    onClick={(e) => handleDeleteChat(e, chat.id)}
                                                    className="sidebar-chat-delete"
                                                    style={{
                                                        position: 'absolute',
                                                        right: '0.5rem',
                                                        top: '50%',
                                                        transform: 'translateY(-50%)',
                                                        opacity: 0,
                                                        transition: 'opacity 0.15s',
                                                        background: 'transparent',
                                                        border: 'none',
                                                        color: '#6b7280',
                                                        padding: '4px',
                                                        borderRadius: '4px',
                                                        cursor: 'pointer',
                                                    }}
                                                    title="Delete chat"
                                                >
                                                    <Trash2 size={14} />
                                                </button>
                                            </div>
                                        ))
                                    )}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>

                    {/* Projects Section */}
                    <div className="sidebar-section">
                        <button
                            onClick={() => isExpanded && setIsProjectsOpen(!isProjectsOpen)}
                            className="sidebar-section-header"
                        >
                            <FolderOpen size={18} />
                            <AnimatePresence>
                                {isExpanded && (
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        className="sidebar-section-title"
                                    >
                                        <span>Projects</span>
                                        {isProjectsOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </button>

                        <AnimatePresence>
                            {isExpanded && isProjectsOpen && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: "auto", opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    className="sidebar-section-items"
                                >
                                    <NavLink to="/projects/new" className="sidebar-chat-item sidebar-add-item">
                                        <Plus size={14} />
                                        <span>New Project</span>
                                    </NavLink>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>

                    {/* Divider */}
                    <div className="sidebar-divider" />

                    {/* Navigation Items */}
                    {navItems.map((item) => (
                        <NavLink
                            key={item.id}
                            to={item.path}
                            className={({ isActive }) =>
                                `sidebar-nav-item ${isActive ? "sidebar-nav-item-active" : ""}`
                            }
                        >
                            {item.icon}
                            <AnimatePresence mode="popLayout">
                                {isExpanded && (
                                    <motion.span
                                        initial={{ opacity: 0, width: 0 }}
                                        animate={{ opacity: 1, width: "auto" }}
                                        exit={{ opacity: 0, width: 0 }}
                                        transition={{ duration: 0.2, ease: "easeInOut" }}
                                        style={{ overflow: "hidden", whiteSpace: "nowrap" }}
                                    >
                                        {item.label}
                                    </motion.span>
                                )}
                            </AnimatePresence>
                        </NavLink>
                    ))}
                </div>
            </motion.aside>

            {/* Overlay when sidebar is open on mobile */}
            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="sidebar-overlay"
                        onClick={toggleSidebar}
                    />
                )}
            </AnimatePresence>
        </>
    );
}

export default Sidebar;
