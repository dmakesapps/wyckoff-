/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                bg: 'var(--bg)',
                fg: 'var(--fg)',
                'card-bg': 'var(--card-bg)',
                'card-border': 'var(--card-border)',
                accent: 'var(--accent)',
                'accent-dark': 'var(--accent-dark)',
                'accent-pink': 'var(--accent-pink)',
            },
            fontFamily: {
                serif: ['"Libre Baskerville"', 'serif'],
            },
            typography: {
                DEFAULT: {
                    css: {
                        color: 'var(--fg)', // Default text color
                        maxWidth: 'none',   // Don't constrain width
                        a: {
                            color: 'var(--accent)',
                            textDecoration: 'none',
                            '&:hover': {
                                textDecoration: 'underline',
                            },
                        },
                        'h1, h2, h3, h4': {
                            color: 'var(--fg)',
                            fontFamily: 'var(--font-serif)',
                            marginTop: '1.5em',
                            marginBottom: '0.6em',
                        },
                        strong: {
                            color: 'var(--fg)', // Keep bold text light
                            fontWeight: 700,
                        },
                        code: {
                            color: '#e0e0e0',
                            backgroundColor: 'rgba(255,255,255,0.1)',
                            padding: '0.2em 0.4em',
                            borderRadius: '0.25rem',
                            fontWeight: 400,
                        },
                        'code::before': { content: '""' },
                        'code::after': { content: '""' },
                        pre: {
                            backgroundColor: 'var(--card-bg)',
                            color: 'var(--fg)',
                            border: '1px solid var(--card-border)',
                            borderRadius: '0.5rem',
                            padding: '1rem',
                        },
                        hr: {
                            borderColor: 'var(--card-border)',
                        },
                        blockquote: {
                            color: 'var(--fg)',
                            borderLeftColor: 'var(--accent)',
                        },
                        ul: {
                            'li::marker': {
                                color: 'var(--accent)',
                            },
                        },
                    },
                },
            },
        },
    },
    plugins: [
        require('@tailwindcss/typography'),
    ],
}
