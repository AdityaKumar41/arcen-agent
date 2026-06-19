import Link from 'next/link'
import React from "react";

export default function FooterSection() {
    return (
        <footer className="border-t border-white/10 bg-black/40 backdrop-blur-sm py-16 font-mono text-xs">
            <div className="mx-auto max-w-6xl px-6">
                <div className="grid grid-cols-2 md:grid-cols-6 gap-8 mb-12 items-start">
                    
                    {/* Brand column */}
                    <div className="col-span-2 md:col-span-2 flex flex-col gap-4">
                        <Link href="/" className="flex items-center gap-2">
                            <span className="font-bold tracking-tight text-base normal-case text-white">Arcen Agent</span>
                        </Link>
                        <p className="text-zinc-400 leading-relaxed lowercase text-[11px] max-w-xs font-mono">
                            AI that understands. Acts. Learns. The complete framework to build, automate, and scale intelligent agent workflows.
                        </p>
                    </div>

                    {/* Product Directory */}
                    <div className="col-span-1 md:col-span-1">
                        <h4 className="font-bold text-white mb-4 uppercase tracking-wider text-[10px]">// Platform</h4>
                        <ul className="flex flex-col gap-2.5 text-zinc-400 lowercase">
                            <li><Link href="#preview" className="hover:text-white transition-colors">features</Link></li>
                            <li><Link href="#agenda" className="hover:text-white transition-colors">technology</Link></li>
                            <li><Link href="#playground" className="hover:text-white transition-colors">playground</Link></li>
                        </ul>
                    </div>

                    {/* Developer Directory */}
                    <div className="col-span-1 md:col-span-1">
                        <h4 className="font-bold text-white mb-4 uppercase tracking-wider text-[10px]">// Resources</h4>
                        <ul className="flex flex-col gap-2.5 text-zinc-400 lowercase">
                            <li><Link href="https://arcen-cli.arcenpay.com/docs/" target="_blank" className="hover:text-white transition-colors">documentation</Link></li>
                            <li><Link href="https://github.com/AdityaKumar41/arcen-agent" target="_blank" className="hover:text-white transition-colors">github</Link></li>
                            <li><Link href="https://agentskills.io" target="_blank" className="hover:text-white transition-colors">skills</Link></li>
                        </ul>
                    </div>

                    {/* Subscribe Column */}
                    <div className="col-span-2 md:col-span-2 flex flex-col gap-4">
                        <h4 className="font-bold text-white uppercase tracking-wider text-[10px]">// Subscribe to updates</h4>
                        <div className="flex gap-2">
                            <input
                                type="email"
                                placeholder="enter your email"
                                className="h-8 flex-1 rounded-none bg-white border border-zinc-200 px-3 text-[10px] text-zinc-950 placeholder:text-zinc-400 focus:outline-none focus:border-[#0029ff] focus:ring-1 focus:ring-[#0029ff] font-mono font-bold transition-all"
                            />
                            <button className="h-8 bg-[#0029ff] hover:bg-[#0029ff]/90 text-white px-4 text-[10px] font-bold rounded-none uppercase tracking-wider transition-all font-mono">
                                Subscribe
                            </button>
                        </div>
                    </div>
                </div>

                <div className="flex flex-col md:flex-row items-center justify-between pt-8 border-t border-white/5 text-zinc-500 text-[10px] leading-relaxed gap-4">
                    <span>
                        built by <Link href="https://arcenpay.com" target="_blank" className="text-white underline">arcenpay</Link> • open source under mit license.
                    </span>
                    <span>
                        copyright © 2026 arcen. all rights reserved.
                    </span>
                </div>
            </div>
        </footer>
    )
}
