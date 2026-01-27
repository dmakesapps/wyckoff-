"use client";

import { useEffect, useMemo, useRef } from "react";
import { motion, useInView, useAnimation } from "framer-motion";
import type { Variants } from "framer-motion";

type TextEffectProps = {
    children: string;
    per?: "word" | "char" | "line";
    as?: keyof React.JSX.IntrinsicElements;
    variants?: {
        container?: Variants;
        item?: Variants;
    };
    className?: string;
    preset?: "fade" | "slide" | "blur";
    delay?: number;
    trigger?: boolean;
    segmentWrapperClassName?: string;
};

const presetVariants = {
    fade: {
        container: {
            hidden: { opacity: 0 },
            visible: { opacity: 1, transition: { staggerChildren: 0.05 } },
        },
        item: {
            hidden: { opacity: 0 },
            visible: { opacity: 1 },
        },
    },
    slide: {
        container: {
            hidden: { opacity: 0 },
            visible: { opacity: 1, transition: { staggerChildren: 0.05 } },
        },
        item: {
            hidden: { opacity: 0, y: 20 },
            visible: { opacity: 1, y: 0 },
        },
    },
    blur: {
        container: {
            hidden: { opacity: 0 },
            visible: { opacity: 1, transition: { staggerChildren: 0.05 } },
        },
        item: {
            hidden: { opacity: 0, filter: "blur(10px)" },
            visible: { opacity: 1, filter: "blur(0px)" },
        },
    },
};

export function TextEffect({
    children,
    per = "word",
    as: Component = "p",
    variants,
    className,
    preset = "fade",
    delay = 0,
    trigger = true,
    segmentWrapperClassName,
}: TextEffectProps) {
    const controls = useAnimation();
    const ref = useRef<HTMLElement>(null);
    const isInView = useInView(ref, { once: true });

    const selectedVariants = variants || presetVariants[preset];

    const segments = useMemo(() => {
        if (per === "line") {
            return children.split("\n");
        }
        if (per === "word") {
            return children.split(" ");
        }
        return children.split("");
    }, [children, per]);

    useEffect(() => {
        if (trigger && isInView) {
            const timeout = setTimeout(() => {
                controls.start("visible");
            }, delay * 1000);
            return () => clearTimeout(timeout);
        } else if (!trigger) {
            controls.start("exit");
        }
    }, [trigger, isInView, delay, controls]);

    const MotionComponent = motion(Component as any);

    return (
        <MotionComponent
            ref={ref}
            className={className}
            initial="hidden"
            animate={controls}
            exit="exit"
            variants={selectedVariants.container}
        >
            {segments.map((segment, i) => (
                <motion.span
                    key={i}
                    variants={selectedVariants.item}
                    className={segmentWrapperClassName}
                    style={{ display: per === "line" ? "block" : "inline-block" }}
                >
                    {segment}
                    {per === "word" && i < segments.length - 1 && "\u00A0"}
                </motion.span>
            ))}
        </MotionComponent>
    );
}

export default TextEffect;
