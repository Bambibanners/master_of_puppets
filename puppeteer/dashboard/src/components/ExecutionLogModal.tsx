import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'sonner';
import { Terminal, Copy } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { authenticatedFetch } from '../auth';

interface OutputLine {
    t: string;
    stream: 'stdout' | 'stderr';
    line: string;
}

interface ExecutionRecord {
    id: number;
    job_guid: string;
    node_id?: string;
    status: string;
    exit_code?: number | null;
    started_at?: string;
    completed_at?: string;
    output_log: OutputLine[];
    truncated: boolean;
    duration_seconds?: number | null;
}

export const ExecutionLogModal = ({ 
    jobGuid, 
    executionId,
    open, 
    onClose 
}: {
    jobGuid?: string;
    executionId?: number;
    open: boolean;
    onClose: () => void;
}) => {
    const [executions, setExecutions] = useState<ExecutionRecord[]>([]);
    const [selected, setSelected] = useState<ExecutionRecord | null>(null);
    const logEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!open) return;
        
        if (executionId) {
            // Fetch single execution (History view use-case)
            authenticatedFetch(`/api/executions/${executionId}`)
                .then(r => r.json())
                .then((data: ExecutionRecord) => {
                    setExecutions([data]);
                    setSelected(data);
                })
                .catch(() => {
                    toast.error('Failed to load execution record');
                });
        } else if (jobGuid) {
            // Fetch all executions for a job (Jobs view use-case)
            authenticatedFetch(`/jobs/${jobGuid}/executions`)
                .then(r => r.json())
                .then((data: ExecutionRecord[]) => {
                    setExecutions(data);
                    setSelected(data[0] ?? null);
                })
                .catch(() => {
                    toast.error('Failed to load job executions');
                });
        }
    }, [open, jobGuid, executionId]);

    useEffect(() => {
        if (open && logEndRef.current) {
            logEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [open, selected]);

    const lines = selected?.output_log ?? [];

    const handleCopy = () => {
        const text = lines.map(l => `[${l.stream === 'stderr' ? 'ERR' : 'OUT'}] ${l.line}`).join('\n');
        navigator.clipboard.writeText(text).then(() => toast('Copied to clipboard'));
    };

    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent className="bg-zinc-950 border-zinc-800 text-white w-[95vw] max-w-6xl h-[90vh] flex flex-col p-0 overflow-hidden shadow-2xl">
                <DialogHeader className="px-6 py-4 border-b border-zinc-900 bg-zinc-950 shrink-0">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="p-2 rounded-lg bg-primary/10 border border-primary/20">
                                <Terminal className="h-4 w-4 text-primary" />
                            </div>
                            <div>
                                <DialogTitle className="text-white text-base font-bold flex items-center gap-3">
                                    Execution Log
                                    {selected && (
                                        <Badge variant={selected.exit_code === 0 ? 'default' : 'destructive'} className="text-[10px] h-5 px-2">
                                            {selected.status}
                                        </Badge>
                                    )}
                                </DialogTitle>
                                <p className="text-zinc-500 text-xs font-mono truncate max-w-[300px]">
                                    {selected?.job_guid || jobGuid}
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center gap-6 text-zinc-400 mr-8">
                            {selected && (
                                <>
                                    <div className="text-center">
                                        <p className="text-[10px] uppercase tracking-wider text-zinc-600 font-bold mb-0.5">Exit Code</p>
                                        <p className={`text-xs font-mono ${selected.exit_code === 0 ? 'text-green-400' : 'text-red-400'}`}>
                                            {selected.exit_code === null ? '—' : selected.exit_code}
                                        </p>
                                    </div>
                                    <div className="text-center">
                                        <p className="text-[10px] uppercase tracking-wider text-zinc-600 font-bold mb-0.5">Duration</p>
                                        <p className="text-xs font-mono text-zinc-300">
                                            {selected.duration_seconds != null ? `${selected.duration_seconds.toFixed(2)}s` : '—'}
                                        </p>
                                    </div>
                                    <div className="text-center">
                                        <p className="text-[10px] uppercase tracking-wider text-zinc-600 font-bold mb-0.5">Node</p>
                                        <p className="text-xs font-mono text-zinc-300 truncate max-w-[120px]">{selected.node_id || '—'}</p>
                                    </div>
                                </>
                            )}
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={handleCopy}
                                className="h-9 w-9 p-0 hover:bg-zinc-800 hover:text-white"
                                title="Copy to clipboard"
                            >
                                <Copy className="h-4 w-4" />
                            </Button>
                        </div>
                    </div>
                </DialogHeader>

                <div className="flex-1 overflow-auto bg-black/50 font-mono text-sm leading-relaxed p-6 selection:bg-primary/30 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
                    <div className="space-y-1">
                        {lines.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-20 text-zinc-600 gap-4">
                                <Terminal className="h-10 w-10 opacity-20" />
                                <p className="text-sm font-medium italic">No output captured for this execution.</p>
                            </div>
                        ) : lines.map((l, i) => (
                            <div key={i} className="flex gap-4 group hover:bg-zinc-900/50 -mx-2 px-2 rounded transition-colors">
                                <span className="text-zinc-700 text-[10px] select-none w-20 pt-1 shrink-0 tabular-nums">
                                    {new Date(l.t).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                </span>
                                <span className={`w-12 pt-0.5 text-[9px] font-bold select-none shrink-0 ${l.stream === 'stderr' ? 'text-amber-500/80' : 'text-zinc-600'}`}>
                                    [{l.stream.slice(0, 3).toUpperCase()}]
                                </span>
                                <span className={`break-all ${l.stream === 'stderr' ? 'text-amber-200' : 'text-zinc-300'}`}>
                                    {l.line}
                                </span>
                            </div>
                        ))}
                        <div ref={logEndRef} />
                    </div>
                </div>

                {executions.length > 1 && (
                    <div className="p-2 border-t border-zinc-900 bg-zinc-950 flex gap-2 overflow-x-auto shrink-0 scrollbar-hide">
                        {executions.map((ex, i) => (
                            <Button
                                key={ex.id}
                                variant={selected?.id === ex.id ? 'secondary' : 'ghost'}
                                size="sm"
                                onClick={() => setSelected(ex)}
                                className="text-xs shrink-0 h-7"
                            >
                                Attempt {executions.length - i}
                            </Button>
                        ))}
                    </div>
                )}
            </DialogContent>
        </Dialog>
    );
};
