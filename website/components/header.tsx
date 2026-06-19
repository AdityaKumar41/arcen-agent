'use client'

import Link from 'next/link'
import { Menu, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import React from 'react'

export const HeroHeader = () => {
    const [menuState, setMenuState] = React.useState(false)

    return (
        <header className="absolute top-0 left-0 w-full z-50 border-none bg-transparent font-mono">
            <div className="mx-auto max-w-6xl px-6">
                <div className="flex h-16 items-center justify-between">
                    
                    {/* Nav Links - Desktop (Left) */}
                    <div className="hidden md:flex items-center justify-start w-1/3">
                        <nav className="flex items-center gap-6 text-[10px] font-semibold text-white lowercase">
                            <Link href="#preview" className="hover:text-white/80 transition-colors">
                                // platform
                            </Link>
                            <Link href="#agenda" className="hover:text-white/80 transition-colors">
                                // technology
                            </Link>
                            <Link href="#playground" className="hover:text-white/80 transition-colors">
                                // playground
                            </Link>
                            <Link href="https://arcen-cli.arcenpay.com/docs/" target="_blank" className="hover:text-white/80 transition-colors">
                                // docs
                            </Link>
                        </nav>
                    </div>

                    {/* Brand - Center */}
                    <div className="flex items-center justify-center md:w-1/3 w-auto">
                        <Link href="/" className="flex items-center gap-2 group">
                            <span className="font-bold tracking-tight text-sm normal-case text-white">Arcen Agent</span>
                            <span className="text-[9px] text-white/60 border border-white/20 px-1 py-0.5 rounded bg-white/10 font-mono">v1.0.0</span>
                        </Link>
                    </div>

                    {/* Desktop Button - Right */}
                    <div className="hidden md:flex items-center justify-end w-1/3">
                        <Button asChild size="sm" className="bg-transparent hover:bg-white/10 text-white border border-white/40 font-semibold tracking-wider text-[10px] uppercase rounded-sm font-mono h-8 px-4">
                            <Link href="#downloads">
                                Get Started
                            </Link>
                        </Button>
                    </div>

                    {/* Mobile Menu Button */}
                    <button
                        onClick={() => setMenuState(!menuState)}
                        className="md:hidden p-2 text-white/80 hover:text-white transition-colors"
                        aria-label="Toggle menu"
                    >
                        {menuState ? <X className="size-5" /> : <Menu className="size-5" />}
                    </button>
                </div>
            </div>

            {/* Mobile Nav Drawer */}
            {menuState && (
                <div className="md:hidden border-b border-white/10 bg-zinc-950/95 backdrop-blur-lg">
                    <nav className="flex flex-col gap-4 p-6 text-sm text-white/80">
                        <Link href="#preview" onClick={() => setMenuState(false)} className="hover:text-white transition-colors">
                            // platform
                        </Link>
                        <Link href="#agenda" onClick={() => setMenuState(false)} className="hover:text-white transition-colors">
                            // technology
                        </Link>
                        <Link href="#playground" onClick={() => setMenuState(false)} className="hover:text-white transition-colors">
                            // playground
                        </Link>
                        <Link href="https://arcen-cli.arcenpay.com/docs/" target="_blank" className="hover:text-white transition-colors">
                            // docs
                        </Link>
                        <Button asChild size="sm" className="mt-2 bg-transparent hover:bg-white/10 text-white border border-white/20 uppercase text-xs">
                            <Link href="#downloads" onClick={() => setMenuState(false)}>
                                Get Started
                            </Link>
                        </Button>
                    </nav>
                </div>
            )}
        </header>
    )
}
