import {
    PromptInput,
    PromptInputAction,
    PromptInputActions,
    PromptInputTextarea,
} from "./ui/prompt-input";
import { Button } from "./ui/button";
import { ArrowUp, Paperclip, X } from "lucide-react";
import { useRef, useState } from "react";

interface PromptInputWithActionsProps {
    onSend?: (message: string) => void;
    disabled?: boolean;
}

export function PromptInputWithActions({ onSend, disabled }: PromptInputWithActionsProps) {
    const [input, setInput] = useState("");
    const [files, setFiles] = useState<File[]>([]);
    const uploadInputRef = useRef<HTMLInputElement>(null);

    const handleSubmit = () => {
        if (input.trim() || files.length > 0) {
            // Call the onSend callback with the message
            if (onSend && input.trim()) {
                onSend(input.trim());
            }

            setInput("");
            setFiles([]);
        }
    };

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            const newFiles = Array.from(event.target.files);
            setFiles((prev) => [...prev, ...newFiles]);
        }
    };

    const handleRemoveFile = (index: number) => {
        setFiles((prev) => prev.filter((_, i) => i !== index));
        if (uploadInputRef?.current) {
            uploadInputRef.current.value = "";
        }
    };

    return (
        <PromptInput
            value={input}
            onValueChange={setInput}
            isLoading={false}
            disabled={disabled}
            onSubmit={handleSubmit}
            className="prompt-input-wrapper"
        >
            {files.length > 0 && (
                <div className="file-list">
                    {files.map((file, index) => (
                        <div key={index} className="file-chip">
                            <Paperclip className="icon-sm" />
                            <span className="file-name">{file.name}</span>
                            <button onClick={() => handleRemoveFile(index)} className="file-remove">
                                <X className="icon-sm" />
                            </button>
                        </div>
                    ))}
                </div>
            )}

            <PromptInputTextarea
                placeholder="Ask me anything..."
                disabled={disabled}
            />

            <PromptInputActions className="prompt-actions">
                <PromptInputAction tooltip="Attach files">
                    <label htmlFor="file-upload" className="attach-label">
                        <input
                            type="file"
                            multiple
                            onChange={handleFileChange}
                            className="hidden"
                            id="file-upload"
                            ref={uploadInputRef}
                        />
                        <Paperclip className="icon-md" />
                    </label>
                </PromptInputAction>

                <PromptInputAction tooltip="Send message">
                    <Button
                        size="icon"
                        className="send-button"
                        onClick={handleSubmit}
                    >
                        <ArrowUp className="icon-md" />
                    </Button>
                </PromptInputAction>
            </PromptInputActions>
        </PromptInput>
    );
}

export default PromptInputWithActions;
