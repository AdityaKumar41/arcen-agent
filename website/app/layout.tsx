import React from "react"
import type {Metadata} from 'next'
import {Space_Grotesk, Geist_Mono, Playfair_Display} from 'next/font/google'
import {Analytics} from '@vercel/analytics/next'
import './globals.css'
import FooterSection from "@/components/footer";
import {HeroHeader} from "@/components/header";

const spaceGrotesk = Space_Grotesk({ subsets: ["latin"], variable: "--font-sans" });
const geistMono = Geist_Mono({ subsets: ["latin"], variable: "--font-mono" });
const playfair = Playfair_Display({ subsets: ["latin"], variable: "--font-serif" });

export const metadata: Metadata = {
    title: 'Arcen Agent — The Self-Improving AI Agent That Grows With You',
    description: 'The self-improving AI agent built by ArcenPay. Features a closed learning loop, terminal TUI, and messaging platform gateway (Telegram, Discord, Slack, WhatsApp, Signal).',
    generator: 'Arcen Agent',
    icons: {
        icon: [
            {
                url: '/icon.svg',
                type: 'image/svg+xml',
            },
        ],
        apple: '/icon.svg',
    },
}

export default function RootLayout({
                                       children,
                                    }: Readonly<{
    children: React.ReactNode
}>) {
    return (
        <html lang="en" className={`dark ${spaceGrotesk.variable} ${geistMono.variable} ${playfair.variable}`}>
        <body className="font-sans antialiased bg-grid-pattern relative min-h-screen">
        <HeroHeader/>
        {children}
        <FooterSection/>
        <Analytics/>
        </body>
        </html>
    )
}
