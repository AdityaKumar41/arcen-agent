"use client";

import React, { useState, useEffect, useRef } from 'react'

interface CapItem {
    id: string;
    title: string;
    desc: string;
    logs: string[];
}

const capabilities: CapItem[] = [
    {
        id: "01",
        title: "Closed Learning Loop",
        desc: "arcen synthesizes new skills autonomously after successfully completing complex tasks. it automatically manages memory consolidation via user profiles.",
        logs: [
            "// [learning_loop] analyzing successful deployment trajectory...",
            "// [learning_loop] synthesized skill: 'Vercel Deployment Pipeline'",
            "// [learning_loop] saved to ~/.arcen/skills/vercel-deploy.md",
            "// [learning_loop] skill registered. ready for immediate use."
        ]
    },
    {
        id: "02",
        title: "Dialectic User Modeling",
        desc: "tracks user preferences, coding standards, and project constraints dynamically over time, updating the agent's behavior to match your habits.",
        logs: [
            "[nudge] checking dialectic profile for user rules...",
            "  -> rules loaded: 'never use style-jsx in server components'",
            "  -> rules loaded: 'prefer interface over type for react props'",
            "[nudge] profile validated. applying constraints to workspace."
        ]
    },
    {
        id: "03",
        title: "Serverless Workspaces",
        desc: "deploy and run tasks in Modal, Daytona, Docker, Singularity, or SSH sandboxes. sandboxes hibernate when idle to maintain zero context-costs.",
        logs: [
            "[info] sandbox environment: Modal serverless sandbox",
            "[info] workspace state: hibernating",
            "[info] waking up workspace on demand (1.2s boot)...",
            "[success] sandbox active. worktree synchronized."
        ]
    },
    {
        id: "04",
        title: "Cross-Platform Gateway",
        desc: "lives where you work. control the same agent instance from terminal CLI, Telegram, Slack, WhatsApp, Signal, or Email with voice-transcription.",
        logs: [
            "[gateway] listening on Telegram platform...",
            "  -> received voice memo (duration: 12s)",
            "  -> transcribing voice: 'run full test suite and notify slack'",
            "[info] task queued from chat interface."
        ]
    }
];

export default function Features() {
    const [activeIndex, setActiveIndex] = useState(0);
    const [consoleLines, setConsoleLines] = useState<string[]>([]);
    const [lineIdx, setLineIdx] = useState(0);
    const containerRef = useRef<HTMLDivElement>(null);
    const isAtBottom = useRef(true);

    const activeCap = capabilities[activeIndex];

    // Trigger console animation when active feature changes
    useEffect(() => {
        setConsoleLines([]);
        setLineIdx(0);
        isAtBottom.current = true;
    }, [activeIndex]);

    useEffect(() => {
        if (lineIdx < activeCap.logs.length) {
            const timer = setTimeout(() => {
                setConsoleLines(prev => [...prev, activeCap.logs[lineIdx]]);
                setLineIdx(prev => prev + 1);
            }, 800);
            return () => clearTimeout(timer);
        }
    }, [lineIdx, activeIndex]);

    useEffect(() => {
        if (containerRef.current && isAtBottom.current) {
            containerRef.current.scrollTop = containerRef.current.scrollHeight;
        }
    }, [consoleLines]);

    const handleScroll = () => {
        if (containerRef.current) {
            const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
            isAtBottom.current = scrollHeight - scrollTop - clientHeight < 15;
        }
    };

    return (
        <section className="py-16 md:py-32 border-t border-white/10 bg-black font-mono" id="preview">
            <div className="mx-auto max-w-6xl px-6">
                
                {/* Statement Block */}
                <div className="border border-zinc-200 rounded-none bg-white p-10 md:p-16 mb-24 text-left shadow-sm flex flex-col md:flex-row justify-between gap-8 items-start">
                    <div className="max-w-2xl">
                        <h2 className="text-2xl sm:text-3xl md:text-4xl font-serif font-medium tracking-tight text-zinc-950 uppercase leading-[1.1] mb-6">
                            We're not building flashy demos. We're engineering agents that think, learn, and work better with you.
                        </h2>
                    </div>
                    <div className="max-w-xs flex flex-col gap-4">
                        <p className="text-[11px] text-zinc-500 leading-relaxed lowercase font-medium">
                            arcen agent leverages a closed dialectic learning loop, synthesizing skills directly from task runs to build a personalized developer profile.
                        </p>
                        <span className="text-[9px] text-[#0029ff] font-bold uppercase tracking-widest">// engineering principles</span>
                    </div>
                </div>

                {/* Capability Header */}
                <div className="flex flex-col text-left mb-16 border-l-2 border-l-[#0029ff] pl-6">
                    <span className="text-[10px] text-[#0029ff] uppercase tracking-widest font-bold">// Capabilities</span>
                    <h2 className="text-2xl md:text-3xl font-serif font-medium tracking-tight text-white uppercase mt-2">
                        Boosting capabilities beyond limits.
                    </h2>
                </div>

                {/* Two-Column Showcase */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-stretch">
                    
                    {/* Left: Interactive list of capabilities */}
                    <div className="lg:col-span-6 flex flex-col gap-4 justify-center">
                        {capabilities.map((cap, index) => {
                            const isActive = index === activeIndex;
                            return (
                                <button
                                    key={index}
                                    onClick={() => setActiveIndex(index)}
                                    className={`text-left p-6 border-y border-r transition-all duration-300 font-mono border-l-4 ${
                                        isActive 
                                            ? 'border-l-[#0029ff] border-y-zinc-200 border-r-zinc-200 bg-zinc-50 shadow-sm' 
                                            : 'border-l-zinc-200 border-y-zinc-200 border-r-zinc-200 hover:border-l-zinc-400 bg-white'
                                    }`}
                                >
                                    <div className="flex items-center justify-between gap-4 mb-2">
                                        <h3 className={`font-bold text-xs uppercase tracking-wider ${isActive ? "text-[#0029ff]" : "text-zinc-950"}`}>{cap.title}</h3>
                                        <span className={`text-[10px] font-bold ${isActive ? "text-[#0029ff]" : "text-zinc-400"}`}>{cap.id}</span>
                                    </div>
                                    <p className={`text-[11px] leading-relaxed lowercase font-medium ${isActive ? 'text-zinc-700' : 'text-zinc-500'}`}>
                                        {cap.desc}
                                    </p>
                                </button>
                            );
                        })}
                    </div>

                    {/* Right: Live Interactive TUI Mockup */}
                    <div className="lg:col-span-6 border border-zinc-800 rounded-none bg-zinc-950 shadow-xl overflow-hidden text-[10px] text-left flex flex-col h-[320px] lg:h-auto">
                        <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-900 bg-zinc-900 shrink-0">
                            <div className="flex items-center gap-1.5 font-mono">
                                <div className="size-2 bg-[#ff5f56] rounded-full" />
                                <div className="size-2 bg-[#ffbd2e] rounded-full" />
                                <div className="size-2 bg-[#27c93f] rounded-full" />
                                <span className="text-[9px] text-zinc-500 uppercase tracking-wider font-bold ml-2">TUI Monitor</span>
                            </div>
                            <span className="text-[9px] text-blue-400 uppercase font-bold">// active: {activeCap.title.toLowerCase()}</span>
                        </div>
                        
                        <div 
                            ref={containerRef} 
                            onScroll={handleScroll}
                            className="flex-1 p-5 overflow-y-auto flex flex-col gap-2.5 scrollbar-none text-blue-400 font-bold font-mono bg-zinc-950"
                        >
                            <div className="text-zinc-600 mb-2 border-b border-zinc-900 pb-2 text-[9px] uppercase font-bold">// starting execution telemetry</div>
                            
                            {consoleLines.map((line, idx) => (
                                <div key={idx} className="text-blue-400 leading-relaxed break-all animate-fade-in font-mono">
                                    {line}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </section>
    )
}
