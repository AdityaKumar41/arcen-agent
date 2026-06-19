"use client";

import React, { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { Play, RotateCcw } from 'lucide-react'

// Simulated playground execution output based on inputs
const executionLogs: Record<string, string[]> = {
    "deploy": [
        '{"status": "initializing", "action": "resolving_model_routing"}',
        '{"model": "anthropic/claude-3.5-sonnet", "routing_metric": "highest_coding_capability"}',
        '{"status": "booting_sandbox", "provider": "modal", "region": "us-east-1"}',
        '{"sandbox": "active", "id": "sb_9821a", "boot_time": "1.12s"}',
        '{"action": "executing_command", "cmd": "bun run build"}',
        '{"output": "compiled successfully in 1.4s (Turbopack)"}',
        '{"status": "consolidating_memory", "skill": "Modal Edge Deployer"}',
        '{"success": true, "url": "https://arcen-edge.dev"}'
    ],
    "audit": [
        '{"status": "initializing", "action": "scanning_files"}',
        '{"target": "Dockerfile", "lines": 42}',
        '{"model": "meta-llama/llama-3-70b-instruct", "routing_metric": "fast_reasoning"}',
        '{"status": "running_linter", "rule_count": 18}',
        '{"issue_found": "high_severity", "line": 14, "rule": "DL3006", "msg": "Always tag base image"}',
        '{"action": "proposing_patch", "diff": "FROM node:18-alpine -> FROM node:18.19-alpine"}',
        '{"status": "consolidating_memory", "skill": "Dockerfile Tag Auditor"}',
        '{"success": true, "patch_applied": "local_worktree"}'
    ],
    "memory": [
        '{"status": "initializing", "action": "reading_trajectories"}',
        '{"session_count": 6, "total_tokens": 14205}',
        '{"model": "google/gemini-1.5-pro", "routing_metric": "largest_context_window"}',
        '{"action": "consolidating_dialectic_profile"}',
        '{"rule_synthesized": "prefer bun for next.js commands", "confidence": 0.98}',
        '{"rule_synthesized": "avoid styled-jsx in server components", "confidence": 0.94}',
        '{"status": "saving_profile", "file": "~/.arcen/config.yaml"}',
        '{"success": true, "profile_saved": "ok"}'
    ]
};

export default function CallToAction() {
    // Playground State
    const [selectedTask, setSelectedTask] = useState<"deploy" | "audit" | "memory">("deploy");
    const [selectedModel, setSelectedModel] = useState<"sonnet" | "pro" | "llama">("sonnet");
    const [selectedEnv, setSelectedEnv] = useState<"modal" | "daytona" | "ssh">("modal");
    const [isMemoryEnabled, setIsMemoryEnabled] = useState(true);
    const [logs, setLogs] = useState<string[]>([]);
    const [logIndex, setLogIndex] = useState(0);
    const [isRunning, setIsRunning] = useState(false);
    const consoleRef = useRef<HTMLDivElement>(null);
    const isAtBottom = useRef(true);



    // Run playground simulation
    useEffect(() => {
        if (!isRunning) return;

        const taskLogs = executionLogs[selectedTask];
        if (logIndex < taskLogs.length) {
            const timer = setTimeout(() => {
                // Adjust logs dynamically based on options selected
                let line = taskLogs[logIndex];
                if (logIndex === 1) {
                    if (selectedModel === "pro") line = '{"model": "google/gemini-1.5-pro", "routing_metric": "largest_context_window"}';
                    if (selectedModel === "llama") line = '{"model": "meta-llama/llama-3-70b-instruct", "routing_metric": "fast_reasoning"}';
                }
                if (logIndex === 2) {
                    if (selectedEnv === "daytona") line = '{"status": "booting_sandbox", "provider": "daytona", "container": "alpine-dev"}';
                    if (selectedEnv === "ssh") line = '{"status": "connecting_ssh", "host": "192.168.1.14", "port": 22}';
                }
                if (logIndex === 6 && !isMemoryEnabled) {
                    line = '{"status": "skipping_memory", "reason": "user_override"}';
                }

                setLogs(prev => [...prev, line]);
                setLogIndex(prev => prev + 1);
            }, 600);
            return () => clearTimeout(timer);
        } else {
            setIsRunning(false);
        }
    }, [isRunning, logIndex, selectedTask, selectedModel, selectedEnv, isMemoryEnabled]);

    useEffect(() => {
        if (consoleRef.current && isAtBottom.current) {
            consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
        }
    }, [logs]);

    const handlePlaygroundScroll = () => {
        if (consoleRef.current) {
            const { scrollTop, scrollHeight, clientHeight } = consoleRef.current;
            isAtBottom.current = scrollHeight - scrollTop - clientHeight < 15;
        }
    };

    const startSimulation = () => {
        setLogs([]);
        setLogIndex(0);
        isAtBottom.current = true;
        setIsRunning(true);
    };

    const resetSimulation = () => {
        setLogs([]);
        setLogIndex(0);
        setIsRunning(false);
    };

    return (
        <section className="py-16 md:py-32 border-t border-muted/20 bg-black font-mono" id="playground">
            <div className="mx-auto max-w-6xl px-6">
                
                {/* Header */}
                <div className="flex flex-col text-left mb-16 border-l border-blue-500 pl-6">
                    <span className="text-[10px] text-blue-400 uppercase tracking-widest font-semibold">// Live Sandbox</span>
                    <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground uppercase mt-2">
                        Test the mind of our AI agent.
                    </h2>
                </div>

                {/* Interactive Playground Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch mb-24 font-mono">
                    
                    {/* Left: Interactive selector & simulation inputs */}
                    <div className="lg:col-span-8 flex flex-col gap-6 text-left border border-zinc-200 rounded-none bg-white p-6 shadow-sm">
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            {/* Model selection */}
                            <div className="flex flex-col gap-2">
                                <label className="text-[9px] uppercase tracking-wider text-zinc-400 font-bold">// Select Model</label>
                                <select 
                                    value={selectedModel} 
                                    onChange={(e) => setSelectedModel(e.target.value as any)}
                                    className="bg-white border border-zinc-200 rounded-none px-2.5 py-1.5 text-[10px] text-zinc-800 focus:outline-none focus:border-[#0029ff] cursor-pointer font-mono font-bold"
                                >
                                    <option value="sonnet">Claude 3.5 Sonnet</option>
                                    <option value="pro">Gemini 1.5 Pro</option>
                                    <option value="llama">Llama 3 70B</option>
                                </select>
                            </div>

                            {/* Sandbox selection */}
                            <div className="flex flex-col gap-2">
                                <label className="text-[9px] uppercase tracking-wider text-zinc-400 font-bold">// Environment</label>
                                <select 
                                    value={selectedEnv} 
                                    onChange={(e) => setSelectedEnv(e.target.value as any)}
                                    className="bg-white border border-zinc-200 rounded-none px-2.5 py-1.5 text-[10px] text-zinc-800 focus:outline-none focus:border-[#0029ff] cursor-pointer font-mono font-bold"
                                >
                                    <option value="modal">Modal Sandbox</option>
                                    <option value="daytona">Daytona Container</option>
                                    <option value="ssh">Local SSH</option>
                                </select>
                            </div>

                            {/* Memory switch */}
                            <div className="flex flex-col gap-2">
                                <label className="text-[9px] uppercase tracking-wider text-zinc-400 font-bold">// Skill Synthesis</label>
                                <button 
                                    onClick={() => setIsMemoryEnabled(!isMemoryEnabled)}
                                    className={`border px-4 py-1.5 text-[10px] font-bold text-center uppercase tracking-wider transition-all rounded-none ${
                                        isMemoryEnabled ? "border-[#0029ff] bg-[#0029ff] text-white" : "border-zinc-200 bg-white text-zinc-500 hover:border-zinc-300"
                                    }`}
                                >
                                    {isMemoryEnabled ? "Active Consolidation" : "Disabled"}
                                </button>
                            </div>
                        </div>

                        {/* Prompt selector */}
                        <div className="flex flex-col gap-2 mt-2">
                            <label className="text-[9px] uppercase tracking-wider text-zinc-400 font-bold">// Select Task Script</label>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                <button 
                                    onClick={() => { setSelectedTask("deploy"); resetSimulation(); }}
                                    className={`p-3 border rounded-none text-left flex flex-col gap-1 transition-all ${
                                        selectedTask === "deploy" ? "border-[#0029ff] bg-zinc-50/50" : "border-zinc-200 hover:border-zinc-300 bg-white"
                                    }`}
                                >
                                    <span className={`text-[10px] font-bold ${selectedTask === "deploy" ? "text-[#0029ff]" : "text-zinc-800"}`}>deploy.sh</span>
                                    <span className="text-[9px] text-zinc-500 lowercase font-medium">build next.js static bundle and push to edge cdn sandbox.</span>
                                </button>
                                <button 
                                    onClick={() => { setSelectedTask("audit"); resetSimulation(); }}
                                    className={`p-3 border rounded-none text-left flex flex-col gap-1 transition-all ${
                                        selectedTask === "audit" ? "border-[#0029ff] bg-zinc-50/50" : "border-zinc-200 hover:border-zinc-300 bg-white"
                                    }`}
                                >
                                    <span className={`text-[10px] font-bold ${selectedTask === "audit" ? "text-[#0029ff]" : "text-zinc-800"}`}>audit_linter.py</span>
                                    <span className="text-[9px] text-zinc-500 lowercase font-medium">parse Dockerfile configurations and audit base tag vulnerabilities.</span>
                                </button>
                                <button 
                                    onClick={() => { setSelectedTask("memory"); resetSimulation(); }}
                                    className={`p-3 border rounded-none text-left flex flex-col gap-1 transition-all ${
                                        selectedTask === "memory" ? "border-[#0029ff] bg-zinc-50/50" : "border-zinc-200 hover:border-zinc-300 bg-white"
                                    }`}
                                >
                                    <span className={`text-[10px] font-bold ${selectedTask === "memory" ? "text-[#0029ff]" : "text-zinc-800"}`}>consolidate_memory.sh</span>
                                    <span className="text-[9px] text-zinc-500 lowercase font-medium">synthesize trajectories across active developer chat histories.</span>
                                </button>
                            </div>
                        </div>

                        {/* Controls & Console output */}
                        <div className="flex flex-col gap-4 border-t border-zinc-100 pt-6">
                            <div className="flex items-center gap-4">
                                <Button 
                                    onClick={startSimulation}
                                    disabled={isRunning}
                                    size="sm"
                                    className="bg-[#0029ff] hover:bg-[#0029ff]/90 text-white font-mono font-bold uppercase tracking-wider text-[10px] rounded-none flex items-center gap-1.5 px-4 h-9 shadow-sm"
                                >
                                    <Play className="size-3 fill-current" />
                                    <span>Run Simulation</span>
                                </Button>
                                <Button 
                                    onClick={resetSimulation}
                                    variant="outline"
                                    size="sm"
                                    className="border-zinc-200 bg-white hover:bg-zinc-50 text-zinc-700 font-mono font-bold uppercase tracking-wider text-[10px] rounded-none flex items-center gap-1.5 px-4 h-9 shadow-sm"
                                >
                                    <RotateCcw className="size-3" />
                                    <span>Reset Console</span>
                                </Button>
                            </div>

                            {/* Simulated console screen */}
                            <div className="border border-zinc-200 rounded-none bg-white h-48 flex flex-col overflow-hidden text-[9px] font-mono leading-relaxed shadow-inner">
                                <div className="flex items-center justify-between border-b border-zinc-200 bg-zinc-50 px-4 py-2 text-zinc-500 text-[8px] uppercase tracking-wider font-bold">
                                    <span>telemetry_stream_monitor</span>
                                    {isRunning && <span className="text-[#0029ff] animate-pulse">● executing</span>}
                                </div>
                                <div 
                                    ref={consoleRef}
                                    onScroll={handlePlaygroundScroll}
                                    className="flex-1 p-4 overflow-y-auto flex flex-col gap-1.5 scrollbar-none text-[#0029ff] font-bold"
                                >
                                    {logs.length === 0 ? (
                                        <span className="text-zinc-400 italic uppercase font-medium">// select task parameters and run simulation above</span>
                                    ) : (
                                        logs.map((log, index) => (
                                            <div key={index} className="break-all font-mono">
                                                {log}
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Right: Validation Checklist */}
                    <div className="lg:col-span-4 border border-zinc-200 rounded-none bg-white p-6 shadow-sm flex flex-col justify-between text-left gap-6">
                        <div className="flex flex-col gap-4 font-mono">
                            <span className="text-[9px] text-zinc-400 uppercase tracking-widest font-bold">// Diagnostics</span>
                            <h3 className="font-bold text-xs uppercase tracking-wide text-zinc-950 font-mono">Active Engine Status</h3>
                            <p className="text-[11px] text-zinc-500 leading-relaxed lowercase font-mono">
                                the active cognitive engine validates configuration constraints prior to launching actions.
                            </p>
                        </div>

                        <div className="flex flex-col gap-4 text-[10px] text-zinc-800 font-bold font-mono">
                            <div className="flex items-center gap-3 border-b border-zinc-100 pb-2.5">
                                <span className="size-4 rounded-none border border-[#0029ff]/30 flex items-center justify-center text-[#0029ff] text-[8px] bg-[#0029ff]/5 font-mono font-bold">✓</span>
                                <span className="lowercase">smart model routing active</span>
                            </div>
                            <div className="flex items-center gap-3 border-b border-zinc-100 pb-2.5">
                                <span className="size-4 rounded-none border border-[#0029ff]/30 flex items-center justify-center text-[#0029ff] text-[8px] bg-[#0029ff]/5 font-mono font-bold">✓</span>
                                <span className="lowercase">serverless sandbox online</span>
                            </div>
                            <div className="flex items-center gap-3 border-b border-zinc-100 pb-2.5">
                                <span className="size-4 rounded-none border border-[#0029ff]/30 flex items-center justify-center text-[#0029ff] text-[8px] bg-[#0029ff]/5 font-mono font-bold">✓</span>
                                <span className="lowercase">memory profile consolidated</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <span className="size-4 rounded-none border border-[#0029ff]/30 flex items-center justify-center text-[#0029ff] text-[8px] bg-[#0029ff]/5 font-mono font-bold">✓</span>
                                <span className="lowercase">synthesized skills registered</span>
                            </div>
                        </div>

                        <div className="border-t border-zinc-100 pt-4 flex flex-col gap-1.5 font-mono">
                            <span className="text-[8px] text-zinc-400 uppercase font-bold">// overall engine health</span>
                            <span className="text-[10px] text-[#0029ff] font-bold uppercase tracking-wider flex items-center gap-1.5">
                                <span className="size-1.5 bg-[#0029ff] rounded-full animate-ping"></span>
                                <span>diagnostic [OK]</span>
                            </span>
                        </div>
                    </div>
                </div>

                {/* Section 2: Reusable CTA Box / Install Command */}
                <div className="border border-white/10 rounded-none bg-[#0029ff] p-8 md:p-12 lg:p-16 text-center shadow-lg relative overflow-hidden" id="downloads">
                    <div className="relative z-10 max-w-xl mx-auto flex flex-col gap-6 font-mono">
                        <h3 className="text-3xl sm:text-4xl font-serif font-medium tracking-tight text-white uppercase">
                            Start building the future today.
                        </h3>
                        <p className="text-xs text-white/80 leading-relaxed lowercase max-w-sm mx-auto font-mono">
                            join other developers shipping faster automation with arcen agent. free to start, scales globally.
                        </p>
                        
                        <div className="flex flex-wrap justify-center gap-4 mt-2">
                            <Button asChild size="lg" className="bg-white hover:bg-white/95 text-[#0029ff] font-mono font-bold px-8 tracking-wider text-xs uppercase rounded-none transition-all duration-300">
                                <Link href="https://github.com/AdityaKumar41/arcen-agent" target="_blank">
                                    View GitHub Repo
                                </Link>
                            </Button>
                            
                            <Button asChild size="lg" variant="outline" className="border-white/40 bg-transparent hover:bg-white/10 text-white font-mono font-bold px-8 tracking-wider text-xs uppercase rounded-none transition-all duration-300">
                                <Link href="https://arcen-cli.arcenpay.com/docs/" target="_blank">
                                    Read Documentation
                                </Link>
                            </Button>
                        </div>
                        <span className="text-[9px] text-white/60 uppercase mt-4">// no credit card required • mit license</span>
                    </div>
                </div>
            </div>
        </section>
    )
}
