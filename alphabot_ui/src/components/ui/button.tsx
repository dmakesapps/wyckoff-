import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: "default" | "outline" | "ghost";
    size?: "default" | "sm" | "icon";
    children: React.ReactNode;
}

export function Button({
    variant = "default",
    size = "default",
    className = "",
    children,
    ...props
}: ButtonProps) {
    const baseClasses = "button";
    const variantClasses = {
        default: "button-default",
        outline: "button-outline",
        ghost: "button-ghost",
    };
    const sizeClasses = {
        default: "button-size-default",
        sm: "button-size-sm",
        icon: "button-size-icon",
    };

    return (
        <button
            className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
            {...props}
        >
            {children}
        </button>
    );
}
