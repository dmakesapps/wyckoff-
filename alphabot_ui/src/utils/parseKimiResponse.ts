// utils/parseKimiResponse.ts
import type { KimiChartReference } from '../types/chart';

export interface ParsedResponse {
    parts: Array<{
        type: 'text' | 'chart';
        content: string | KimiChartReference;
    }>;
}

export function parseKimiResponse(content: string): ParsedResponse {
    // Regex to match chart tags
    const chartPattern = /\[CHART:([A-Z\-\^]+):(\w+):(\w+):([a-z0-9_,]+)\]/g;

    // Regex to match tool call tags (e.g. <search_market>...</search_market>)
    // We want to hide these from the user view as the backend/UI handles the "Running..." indicator separately.
    const toolPattern = /<([a-z_]+)>[\s\S]*?<\/\1>/g;

    const parts: ParsedResponse['parts'] = [];

    // First, temporarily mask tool calls so we don't render them
    // We replace them with an empty string or a placeholder if we wanted to show something,
    // but the requirement is to "hide" raw tags because the UI shows a separate indicator.
    const contentWithoutTools = content.replace(toolPattern, '');

    let lastIndex = 0;
    let match;

    while ((match = chartPattern.exec(contentWithoutTools)) !== null) {
        // Add text before the chart
        if (match.index > lastIndex) {
            parts.push({
                type: 'text',
                content: contentWithoutTools.slice(lastIndex, match.index),
            });
        }

        // Add chart reference
        parts.push({
            type: 'chart',
            content: {
                symbol: match[1],
                interval: match[2],
                period: match[3],
                indicators: match[4].split(','),
            },
        });

        lastIndex = chartPattern.lastIndex;
    }

    // Add remaining text
    if (lastIndex < contentWithoutTools.length) {
        parts.push({
            type: 'text',
            content: contentWithoutTools.slice(lastIndex),
        });
    }

    return { parts };
}
