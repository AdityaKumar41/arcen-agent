"use client";

import React from "react";
import { transitionVariants } from "@/lib/utils";
import { AnimatedGroup } from "@/components/motion-primitives/animated-group";

interface CapItem {
    id: string;
    title: string;
    desc: string;
    icon: React.ReactNode;
}

const capItems: CapItem[] = [
    {
        id: "01",
        title: "Context Memory",
        desc: "autonomously aggregates task history, user dialectic profiles, and workspace configurations in local session files.",
        icon: (
            <svg viewBox="0 0 100 100" className="size-14 text-[#0029ff]" fill="currentColor">
                <circle cx="50" cy="50" r="35" stroke="currentColor" strokeWidth="1" strokeDasharray="2 4" fill="none" />
                <circle cx="50" cy="50" r="25" stroke="currentColor" strokeWidth="1" strokeDasharray="3 3" fill="none" />
                <circle cx="50" cy="50" r="15" stroke="currentColor" strokeWidth="1" strokeDasharray="4 2" fill="none" />
                <circle cx="50" cy="50" r="5" fill="currentColor" />
            </svg>
        )
    },
    {
        id: "02",
        title: "Persistent Memory",
        desc: "consolidates long-term skills and saves context-free indexing profiles across platform gateways.",
        icon: (
            <svg viewBox="0 0 100 100" className="size-14 text-[#0029ff]" fill="none" stroke="currentColor" strokeWidth="1">
                <rect x="25" y="25" width="50" height="50" rx="4" strokeDasharray="2 2" />
                <rect x="35" y="35" width="30" height="30" rx="2" strokeDasharray="4 2" />
                <circle cx="50" cy="50" r="4" fill="currentColor" />
                <line x1="25" y1="35" x2="15" y2="35" strokeDasharray="2 2" />
                <line x1="25" y1="65" x2="15" y2="65" strokeDasharray="2 2" />
                <line x1="75" y1="35" x2="85" y2="35" strokeDasharray="2 2" />
                <line x1="75" y1="65" x2="85" y2="65" strokeDasharray="2 2" />
                <line x1="35" y1="25" x2="35" y2="15" strokeDasharray="2 2" />
                <line x1="65" y1="25" x2="65" y2="15" strokeDasharray="2 2" />
                <line x1="35" y1="75" x2="35" y2="85" strokeDasharray="2 2" />
                <line x1="65" y1="75" x2="65" y2="85" strokeDasharray="2 2" />
            </svg>
        )
    },
    {
        id: "03",
        title: "Synthetic Control",
        desc: "executes sandboxed terminal bash instructions safely with intelligent auto-recovery capabilities.",
        icon: (
            <svg viewBox="0 0 100 100" className="size-14 text-[#0029ff]" fill="none" stroke="currentColor" strokeWidth="1">
                <circle cx="50" cy="50" r="35" strokeDasharray="4 3" />
                <circle cx="50" cy="50" r="10" strokeDasharray="2 2" />
                <line x1="50" y1="15" x2="50" y2="85" strokeDasharray="3 3" />
                <line x1="15" y1="50" x2="85" y2="50" strokeDasharray="3 3" />
                <line x1="25" y1="25" x2="75" y2="75" strokeDasharray="3 3" />
                <line x1="25" y1="75" x2="75" y2="25" strokeDasharray="3 3" />
            </svg>
        )
    },
    {
        id: "04",
        title: "Dynamic APIs",
        desc: "integrates with major developer toolsets and third-party environments on edge runtimes.",
        icon: (
            <svg viewBox="0 0 100 100" className="size-14 text-[#0029ff]" fill="none" stroke="currentColor" strokeWidth="1">
                <circle cx="50" cy="50" r="35" strokeDasharray="4 3" />
                <ellipse cx="50" cy="50" rx="35" ry="12" strokeDasharray="2 2" />
                <ellipse cx="50" cy="50" rx="12" ry="35" strokeDasharray="2 2" />
                <line x1="15" y1="50" x2="85" y2="50" strokeDasharray="3 3" />
                <line x1="50" y1="15" x2="50" y2="85" strokeDasharray="3 3" />
            </svg>
        )
    }
];

export default function CapabilitiesGrid() {
    return (
        <section className="py-16 md:py-32 border-t border-white/10 bg-black font-mono">
            <div className="mx-auto max-w-6xl px-6">
                
                {/* Header */}
                <div className="flex flex-col text-left mb-16 border-l-2 border-[#0029ff] pl-6">
                    <span className="text-[10px] text-[#0029ff] uppercase tracking-widest font-bold font-mono">// Architecture</span>
                    <h2 className="text-2xl md:text-3xl font-serif font-medium tracking-tight text-white uppercase mt-2">
                        Designed to grow and adapt.
                    </h2>
                </div>

                {/* 4-Column Cards Grid */}
                <AnimatedGroup
                    triggerOnView
                    variants={{
                        container: {
                            visible: {
                                transition: {
                                    staggerChildren: 0.05,
                                }
                            }
                        },
                        ...transitionVariants
                    }}
                    className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 items-stretch"
                >
                    {capItems.map((item) => (
                        <div 
                            key={item.id}
                            className="border border-zinc-200 rounded-none bg-white hover:border-[#0029ff]/50 p-6 flex flex-col items-start gap-4 transition-all duration-300 group shadow-sm h-full"
                        >
                            {/* SVG Graphic Frame */}
                            <div className="w-full h-36 flex items-center justify-center bg-zinc-50 rounded-none border border-zinc-200 relative overflow-hidden group-hover:border-[#0029ff]/20 transition-colors shrink-0">
                                {item.icon}
                            </div>
                            
                            {/* Card ID */}
                            <span className="text-[10px] text-[#0029ff] font-bold uppercase tracking-wider font-mono">// {item.id}</span>
                            
                            {/* Title & Desc */}
                            <div className="flex flex-col gap-1.5 text-left font-mono flex-grow">
                                <h3 className="font-bold text-xs text-zinc-950 uppercase tracking-wide">{item.title}</h3>
                                <p className="text-[11px] text-zinc-500 leading-relaxed lowercase font-medium">
                                    {item.desc}
                                </p>
                            </div>
                        </div>
                    ))}
                </AnimatedGroup>

            </div>
        </section>
    )
}
