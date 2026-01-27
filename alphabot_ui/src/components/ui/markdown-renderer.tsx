import { motion } from 'framer-motion';
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { TextEffect } from "./text-effect";

interface MarkdownRendererProps {
    content: string;
    isStreaming?: boolean;
}

const animationVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.3 } }
};

export function MarkdownRenderer({ content, isStreaming = false }: MarkdownRendererProps) {
    // Pre-process content: Ensure headers start on new lines to prevent inline ## issues
    // Replaces "text## Header" with "text\n\n## Header"
    const processedContent = content.replace(/([^\n])(#{1,6}\s)/g, '$1\n\n$2');

    // Only animate (entry fade) if actively streaming. 
    // Completed messages should render statically to prevent re-animation flicker.
    const animProps = isStreaming ? {
        variants: animationVariants,
        initial: "hidden",
        animate: "visible"
    } : {};

    return (
        <div className="prose prose-invert max-w-none prose-p:leading-loose prose-li:marker:text-accent prose-headings:font-serif prose-headings:font-normal">
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    p: ({ node, children, ...props }) => {
                        const isSimpleString = React.Children.toArray(children).every(child => typeof child === 'string');

                        // IF STREAMING and Simple Text -> Use Typewriter Effect
                        if (isStreaming && isSimpleString) {
                            return (
                                <p className="mb-8 text-gray-300 leading-loose" {...(props as any)}>
                                    <TextEffect per="word" preset="fade">
                                        {React.Children.toArray(children).join("")}
                                    </TextEffect>
                                </p>
                            );
                        }

                        // IF NOT STREAMING (History) -> Render Toggle Static to lock state
                        if (!isStreaming) {
                            return <p className="mb-8 text-gray-300 leading-loose" {...(props as any)}>{children}</p>;
                        }

                        // Fallback: Streaming but complex content (fade block)
                        return (
                            <motion.p
                                {...animProps}
                                className="mb-8 text-gray-300 leading-loose"
                                {...(props as any)}
                            >
                                {children}
                            </motion.p>
                        );
                    },
                    h1: ({ node, ...props }) => <motion.h1 {...animProps} className="mt-16 mb-8 text-3xl font-serif" {...(props as any)} />,
                    h2: ({ node, ...props }) => <motion.h2 {...animProps} className="mt-20 mb-8 text-2xl font-serif font-medium border-b border-white/5 pb-4" {...(props as any)} />,
                    h3: ({ node, ...props }) => <motion.h3 {...animProps} className="mt-12 mb-6 text-xl font-serif text-emerald-400" {...(props as any)} />,
                    ul: ({ node, ...props }) => <motion.ul {...animProps} className="mb-10 space-y-6" {...(props as any)} />,
                    li: ({ node, ...props }) => (
                        <motion.li
                            variants={animationVariants}
                            initial="hidden"
                            animate="visible"
                            className="ml-4 pl-2 leading-relaxed"
                            {...(props as any)}
                        />
                    ),
                    code({ node, inline, className, children, ...props }: any) {
                        const match = /language-(\w+)/.exec(className || '');
                        return !inline && match ? (
                            <div className="rounded-md overflow-hidden my-4 border border-card-border">
                                <div className="bg-card-bg px-4 py-2 flex justify-between items-center border-b border-card-border">
                                    <span className="text-xs text-gray-400 font-mono">{match[1]}</span>
                                    <span className="text-xs text-gray-500">Copy</span>
                                </div>
                                <SyntaxHighlighter
                                    {...props}
                                    style={vscDarkPlus}
                                    language={match[1]}
                                    PreTag="div"
                                    customStyle={{ margin: 0, borderRadius: 0, background: 'var(--bg)' }}
                                >
                                    {String(children).replace(/\n$/, '')}
                                </SyntaxHighlighter>
                            </div>
                        ) : (
                            <code {...props} className={`${className} bg-white/10 px-1 py-0.5 rounded text-accent`}>
                                {children}
                            </code>
                        );
                    },
                    // Custom link renderer to open in new tab
                    a: ({ node, ...props }) => (
                        <a {...props} target="_blank" rel="noopener noreferrer" className="text-accent hover:underline" />
                    ),
                    // Customize Table
                    table: ({ node, ...props }) => (
                        <div className="overflow-x-auto my-4 border border-card-border rounded-lg">
                            <table {...props} className="w-full text-left border-collapse" />
                        </div>
                    ),
                    th: ({ node, ...props }) => (
                        <th {...props} className="bg-card-bg px-4 py-2 border-b border-card-border font-semibold text-gray-200" />
                    ),
                    td: ({ node, ...props }) => (
                        <td {...props} className="px-4 py-2 border-b border-card-border/50 text-gray-300" />
                    ),
                }}
            >
                {processedContent}
            </ReactMarkdown>
        </div>
    );
}

export default MarkdownRenderer;
