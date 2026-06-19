"use client";

import React from "react";
import Link from "next/link";
import { transitionVariants } from "@/lib/utils";
import { AnimatedGroup } from "@/components/motion-primitives/animated-group";

export default function Agenda() {
    return (
        <section className="py-16 md:py-32 border-t border-white/10 bg-black font-mono" id="agenda">
            <div className="mx-auto max-w-6xl px-6">
                
                {/* Dual Column Header */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start mb-20">
                    <div className="lg:col-span-6 flex flex-col text-left">
                        <span className="text-xs text-[#0029ff] uppercase tracking-widest font-bold mb-2">// Technology</span>
                        <h2 className="text-3xl md:text-4xl font-serif font-medium tracking-tight text-white uppercase leading-none">
                            The framework <br />
                            behind self-improving <br />
                            AI cognition.
                        </h2>
                    </div>
                    <div className="lg:col-span-6 flex flex-col gap-4 text-left justify-end h-full">
                        <p className="text-xs text-zinc-400 leading-relaxed lowercase max-w-md font-mono">
                            arcen is engineered to eliminate the manual cycle of tool-chain building. it autonomously tracks context, synthesizes fresh skills on success, and executes securely in isolated workspaces.
                        </p>
                        <Link href="https://arcen-cli.arcenpay.com/docs/" target="_blank" className="text-[10px] text-[#0029ff] font-bold tracking-wider hover:underline uppercase">
                            View Documentation →
                        </Link>
                    </div>
                </div>

                {/* Metrics Stats Grid */}
                <AnimatedGroup
                    triggerOnView
                    variants={{
                        container: {
                            visible: {
                                transition: {
                                    staggerChildren: 0.1,
                                }
                            }
                        },
                        ...transitionVariants
                    }}
                    className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-12 border-t border-white/5 items-stretch"
                >
                    {/* Stat 1 */}
                    <div className="flex flex-col text-left border border-zinc-200 bg-white p-6 shadow-sm h-full">
                        <div className="text-5xl md:text-6xl font-serif font-medium text-[#0029ff] tracking-tight">90+</div>
                        <div className="text-[10px] text-zinc-400 font-bold uppercase tracking-widest mt-3 font-mono">// Max Loop Iterations</div>
                        <p className="text-[11px] text-zinc-500 mt-2 lowercase font-mono font-medium leading-relaxed">
                            deep reasoning budgets are optimized automatically using server-side models.
                        </p>
                    </div>

                    {/* Stat 2 */}
                    <div className="flex flex-col text-left border border-zinc-200 bg-white p-6 shadow-sm h-full">
                        <div className="text-5xl md:text-6xl font-serif font-medium text-[#0029ff] tracking-tight">142ms</div>
                        <div className="text-[10px] text-zinc-400 font-bold uppercase tracking-widest mt-3 font-mono">// Average Latency</div>
                        <p className="text-[11px] text-zinc-500 mt-2 lowercase font-mono font-medium leading-relaxed">
                            planetary edge network executes tasks and caches workspace layers instantly.
                        </p>
                    </div>

                    {/* Stat 3 */}
                    <div className="flex flex-col text-left border border-zinc-200 bg-white p-6 shadow-sm h-full">
                        <div className="text-5xl md:text-6xl font-serif font-medium text-[#0029ff] tracking-tight">24/7</div>
                        <div className="text-[10px] text-zinc-400 font-bold uppercase tracking-widest mt-3 font-mono">// Daemon Scheduler</div>
                        <p className="text-[11px] text-zinc-500 mt-2 lowercase font-mono font-medium leading-relaxed">
                            background cron engines execute continuous tasks and handle async events.
                        </p>
                    </div>
                </AnimatedGroup>
                
            </div>
        </section>
    )
}
