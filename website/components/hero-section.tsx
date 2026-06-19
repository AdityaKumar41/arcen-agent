"use client";

import React from 'react'
import Link from 'next/link'
import Dither from "@/components/Dither"
import { Copy, Check } from 'lucide-react'

export default function HeroSection() {
    const [activeTab, setActiveTab] = React.useState<'mac' | 'win'>('mac')
    const [copied, setCopied] = React.useState(false)

    const macCommand = 'curl -fsSL https://arcen-cli.arcenpay.com/install.sh | bash'
    const winCommand = 'iex (irm https://arcen-cli.arcenpay.com/install.ps1)'
    const activeCommand = activeTab === 'mac' ? macCommand : winCommand

    const handleCopy = () => {
        navigator.clipboard.writeText(activeCommand)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    return (
        <main className="overflow-x-hidden">
            <section className="relative min-h-screen flex items-center border-b border-white/10 pt-24 pb-20 bg-[#0029ff] overflow-hidden">
                
                {/* Background Dither Wave Graphic (Stretches across right background and bleeds behind text) */}
                <div className="absolute inset-y-0 right-0 w-full lg:w-[65%] pointer-events-none z-0 select-none">
                    <div className="w-full h-full opacity-90">
                        <Dither
                            waveColor={[1.0, 1.0, 1.0]}
                            disableAnimation={false}
                            enableMouseInteraction={false}
                            mouseRadius={0.3}
                            colorNum={4}
                            pixelSize={2}
                            waveAmplitude={0.4}
                            waveFrequency={4}
                            waveSpeed={0.03}
                        />
                    </div>
                    {/* Gradient fade to blend left edge of canvas with the royal blue background */}
                    <div className="absolute inset-0 bg-gradient-to-r from-[#0029ff] via-[#0029ff]/20 to-transparent pointer-events-none" />
                </div>

                <div className="mx-auto max-w-6xl px-6 w-full relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
                    
                    {/* Left Column: Copy & Actions (On top of dither) */}
                    <div className="lg:col-span-8 flex flex-col text-left justify-center py-6">
                        
                        <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-[76px] font-serif font-medium tracking-tight leading-[1.02] mb-6 uppercase text-white">
                            THE AGENT <br />
                            THAT GROWS <br />
                            WITH YOU
                        </h1>
                        
                        <p className="text-xs text-white/80 leading-relaxed max-w-lg mb-8 lowercase font-mono">
                            an open-source framework for agentic workflows. securely execute, deploy, and scale autonomous ai agents with a closed dialectic learning loop.
                        </p>

                        {/* Installers */}
                        <div className="flex flex-col gap-6 items-start w-full mt-4">
                            {/* Terminal Installer */}
                            <div className="flex flex-col gap-2 w-full max-w-md">
                                <span className="text-[9px] uppercase tracking-widest text-white/70 font-mono font-bold">// install via terminal</span>
                                <div className="w-full border border-white/20 rounded-none bg-white overflow-hidden text-left font-mono shadow-lg">
                                    <div className="flex border-b border-zinc-200 bg-zinc-50 px-3 pt-2">
                                        <button
                                            onClick={() => setActiveTab('mac')}
                                            className={`pb-2 px-3 text-[9px] tracking-wider uppercase border-b-2 transition-all font-bold ${
                                                activeTab === 'mac'
                                                    ? 'border-[#0029ff] text-zinc-900'
                                                    : 'border-transparent text-zinc-400 hover:text-zinc-600'
                                            }`}
                                        >
                                            macOS / Linux
                                        </button>
                                        <button
                                            onClick={() => setActiveTab('win')}
                                            className={`pb-2 px-3 text-[9px] tracking-wider uppercase border-b-2 transition-all font-bold ${
                                                activeTab === 'win'
                                                    ? 'border-[#0029ff] text-zinc-900'
                                                    : 'border-transparent text-zinc-400 hover:text-zinc-600'
                                            }`}
                                        >
                                            Windows
                                        </button>
                                    </div>
                                    <div className="p-3 flex items-center justify-between gap-4 h-11">
                                        <div className="flex items-center gap-1.5 overflow-x-auto select-all text-[10px] font-bold scrollbar-none text-[#0029ff] w-full">
                                            <span className="text-zinc-400 shrink-0 select-none">$</span>
                                            <span className="whitespace-nowrap font-mono">{activeCommand}</span>
                                        </div>
                                        <button
                                            onClick={handleCopy}
                                            className="shrink-0 p-1 hover:bg-zinc-100 rounded transition-all text-zinc-400 hover:text-[#0029ff]"
                                            title="Copy command"
                                        >
                                            {copied ? <Check className="size-3.5 text-green-600" /> : <Copy className="size-3.5" />}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Right Column: Spacing to show the canvas */}
                    <div className="lg:col-span-4 hidden lg:block pointer-events-none" />
                </div>
            </section>

            {/* Integration list */}
            <section className="bg-background/40 backdrop-blur-sm py-10 border-b border-muted/20 font-mono">
                <div className="mx-auto max-w-6xl px-6">
                    <div className="flex flex-col gap-4 items-center">
                        <p className="text-[9px] uppercase tracking-widest text-muted-foreground/60">// supported integrations & providers</p>
                        <div className="flex flex-wrap items-center justify-center gap-x-16 gap-y-6 mt-2 opacity-50 grayscale">
                            <span className="font-bold text-xs tracking-wider uppercase">OpenRouter</span>
                            <span className="font-bold text-xs tracking-wider uppercase">Ollama</span>
                            <span className="font-bold text-xs tracking-wider uppercase">Anthropic</span>
                            <span className="font-bold text-xs tracking-wider uppercase">OpenAI</span>
                            <span className="font-bold text-xs tracking-wider uppercase">Telegram</span>
                            <span className="font-bold text-xs tracking-wider uppercase">Slack</span>
                            <span className="font-bold text-xs tracking-wider uppercase">Modal</span>
                        </div>
                    </div>
                </div>
            </section>
        </main>
    )
}
