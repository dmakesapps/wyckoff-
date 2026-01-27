import { createContext, useContext } from "react";

interface PromptInputContextValue {
    value: string;
    onValueChange: (value: string) => void;
    isLoading: boolean;
    onSubmit: () => void;
    disabled?: boolean;
}

const PromptInputContext = createContext<PromptInputContextValue | null>(null);

function usePromptInput() {
    const context = useContext(PromptInputContext);
    if (!context) {
        throw new Error("usePromptInput must be used within a PromptInput");
    }
    return context;
}

interface PromptInputProps {
    value: string;
    onValueChange: (value: string) => void;
    isLoading: boolean;
    onSubmit: () => void;
    className?: string;
    disabled?: boolean;
    children: React.ReactNode;
}

export function PromptInput({
    value,
    onValueChange,
    isLoading,
    onSubmit,
    className = "",
    disabled,
    children,
}: PromptInputProps) {
    return (
        <PromptInputContext.Provider value={{ value, onValueChange, isLoading, onSubmit, disabled }}>
            <div
                className={`prompt-input ${className} ${disabled ? "opacity-50 pointer-events-none" : ""}`}
                onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey && !disabled) {
                        e.preventDefault();
                        onSubmit();
                    }
                }}
            >
                {children}
            </div>
        </PromptInputContext.Provider>
    );
}

interface PromptInputTextareaProps {
    placeholder?: string;
    disabled?: boolean;
}

export function PromptInputTextarea({ placeholder, disabled }: PromptInputTextareaProps) {
    const { value, onValueChange, disabled: contextDisabled } = usePromptInput();
    const isDisabled = disabled || contextDisabled;

    return (
        <textarea
            className="prompt-textarea"
            placeholder={placeholder}
            value={value}
            onChange={(e) => onValueChange(e.target.value)}
            rows={1}
            disabled={isDisabled}
        />
    );
}

interface PromptInputActionsProps {
    className?: string;
    children: React.ReactNode;
}

export function PromptInputActions({ className = "", children }: PromptInputActionsProps) {
    return <div className={`prompt-actions ${className}`}>{children}</div>;
}

interface PromptInputActionProps {
    tooltip?: string;
    children: React.ReactNode;
}

export function PromptInputAction({ tooltip, children }: PromptInputActionProps) {
    return (
        <div className="prompt-action" title={tooltip}>
            {children}
        </div>
    );
}
