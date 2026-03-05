import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
    Plus,
    Play,
    History,
    Terminal,
    Clock,
    Hash,
    MoreHorizontal,
    Search,
    Tag,
    Cpu,
    CheckCircle2,
    XCircle,
    AlertTriangle,
    Timer,
    Ban,
    ShieldAlert,
} from 'lucide-react';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from '@/components/ui/table';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { authenticatedFetch } from '../auth';
import { useWebSocket } from '../hooks/useWebSocket';

interface Job {
    guid: string;
    status: string;
    task_type?: string;
    payload: Record<string, any>;
    result?: Record<string, any>;
    node_id?: string;
    started_at?: string;
    duration_seconds?: number;
    target_tags?: string[];
}

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

const getStatusVariant = (status: string) => {
    switch (status.toLowerCase()) {
        case 'completed': return 'success';
        case 'failed': return 'destructive';
        case 'cancelled': return 'destructive';
        case 'security_rejected': return 'destructive';
        case 'assigned': return 'secondary';
        case 'pending': return 'outline';
        default: return 'outline';
    }
};

const StatusIcon = ({ status }: { status: string }) => {
    switch (status.toLowerCase()) {
        case 'completed': return <CheckCircle2 className="h-4 w-4 text-green-500" />;
        case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
        case 'security_rejected': return <ShieldAlert className="h-4 w-4 text-orange-500" />;
        case 'assigned': return <Timer className="h-4 w-4 text-yellow-500 animate-pulse" />;
        default: return <Clock className="h-4 w-4 text-zinc-500" />;
    }
};

const ExecutionLogModal = ({ guid, open, onClose }: {
    guid: string;
    open: boolean;
    onClose: () => void;
}) => {
    const [executions, setExecutions] = useState<ExecutionRecord[]>([]);
    const [selected, setSelected] = useState<ExecutionRecord | null>(null);
    const logEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!open || !guid) return;
        authenticatedFetch(`/jobs/${guid}/executions`)
            .then(r => r.json())
            .then((data: ExecutionRecord[]) => {
                setExecutions(data);
                setSelected(data[0] ?? null);
            })
            .catch(() => {});
    }, [open, guid]);

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
            <DialogContent className="bg-zinc-950 border-zinc-800 text-white w-[95vw] max-w-6xl h-[90vh] flex flex-col p-0">
                <DialogHeader className="px-4 pt-4 pb-3 border-b border-zinc-800 shrink-0">
                    <div className="flex items-center justify-between">
                        <DialogTitle className="text-white text-sm font-medium flex items-center gap-3">
                            <span className="font-mono text-zinc-400 text-xs truncate max-w-[200px]">{guid}</span>
                            {selected && (
                                <>
                                    <span className={`font-bold text-sm ${selected.exit_code === 0 ? 'text-green-400' : selected.exit_code === null ? 'text-zinc-500' : 'text-red-400'}`}>
                                        {selected.exit_code === null ? 'exit: —' : `exit: ${selected.exit_code}`}
                                    </span>
                                    {selected.node_id && <span className="text-zinc-500 text-xs">{selected.node_id}</span>}
                                    {selected.duration_seconds != null && (
                                        <span className="text-zinc-500 text-xs">{selected.duration_seconds.toFixed(2)}s</span>
                                    )}
                                    {selected.started_at && (
                                        <span className="text-zinc-500 text-xs">{new Date(selected.started_at).toLocaleString()}</span>
                                    )}
                                </>
                            )}
                        </DialogTitle>
                        <div className="flex items-center gap-2 pr-8">
                            {executions.length > 1 && (
                                <select
                                    className="bg-zinc-800 border border-zinc-700 text-zinc-300 text-xs rounded px-2 py-1"
                                    value={selected?.id ?? ''}
                                    onChange={e => setSelected(executions.find(x => x.id === Number(e.target.value)) ?? null)}
                                >
                                    {executions.map((ex, i) => (
                                        <option key={ex.id} value={ex.id}>
                                            Attempt {executions.length - i} — {ex.status}
                                        </option>
                                    ))}
                                </select>
                            )}
                            <button
                                onClick={handleCopy}
                                className="text-zinc-400 hover:text-zinc-200 text-xs px-2 py-1 rounded border border-zinc-700 hover:border-zinc-500"
                            >
                                Copy
                            </button>
                        </div>
                    </div>
                </DialogHeader>

                <div className="flex-1 overflow-y-auto font-mono text-xs p-4 bg-black">
                    {lines.length === 0 && !selected?.truncated && (
                        <div className="text-zinc-600 italic">No output captured.</div>
                    )}
                    {lines.map((entry, i) => (
                        <div key={i} className="flex gap-2 leading-5">
                            <span className="text-zinc-600 shrink-0 select-none">
                                {new Date(entry.t).toLocaleTimeString()}
                            </span>
                            <span className="text-zinc-600 shrink-0 select-none">
                                {entry.stream === 'stderr' ? '[ERR]' : '[OUT]'}
                            </span>
                            <span className={entry.stream === 'stderr' ? 'text-amber-400' : 'text-zinc-300'}>
                                {entry.line}
                            </span>
                        </div>
                    ))}
                    {selected?.truncated && (
                        <div className="text-yellow-500 border-t border-zinc-800 mt-2 pt-2 italic">
                            Output truncated at 1MB — remaining lines not stored.
                        </div>
                    )}
                    {selected && selected.exit_code !== null && selected.exit_code !== undefined && (
                        <div className={`mt-4 font-bold text-sm ${selected.exit_code === 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {selected.exit_code === 0 ? '✔' : '✘'} Exit {selected.exit_code}
                        </div>
                    )}
                    <div ref={logEndRef} />
                </div>
            </DialogContent>
        </Dialog>
    );
};

const JobDetailPanel = ({ job, open, onClose, onCancel, onViewOutput }: { job: Job | null; open: boolean; onClose: () => void; onCancel: (guid: string) => void; onViewOutput: (guid: string) => void }) => {
    if (!job) return null;
    const cancellable = job.status === 'PENDING' || job.status === 'ASSIGNED';

    const flightRecorder = job.result?.flight_recorder;
    const resultData = job.result
        ? Object.fromEntries(Object.entries(job.result).filter(([k]) => k !== 'flight_recorder'))
        : null;

    return (
        <Sheet open={open} onOpenChange={onClose}>
            <SheetContent className="bg-zinc-900 border-zinc-800 text-white w-full sm:max-w-xl overflow-y-auto">
                <SheetHeader className="pb-4 border-b border-zinc-800">
                    <SheetTitle className="text-white flex items-center gap-2">
                        <StatusIcon status={job.status} />
                        Job Detail
                    </SheetTitle>
                    <SheetDescription className="font-mono text-zinc-500 text-xs break-all">
                        {job.guid}
                    </SheetDescription>
                </SheetHeader>

                <div className="space-y-6 pt-6">
                    {cancellable && (
                        <Button
                            variant="outline"
                            className="w-full border-red-500/40 text-red-400 hover:bg-red-500/10 hover:text-red-300"
                            onClick={() => { onCancel(job.guid); onClose(); }}
                        >
                            <Ban className="mr-2 h-4 w-4" /> Cancel Job
                        </Button>
                    )}

                    <Button
                        variant="outline"
                        className="w-full border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                        onClick={() => { onViewOutput(job.guid); onClose(); }}
                    >
                        <Terminal className="mr-2 h-4 w-4" /> View Output
                    </Button>

                    {/* Metadata */}
                    <section className="space-y-3">
                        <h3 className="text-2xs font-bold text-zinc-500 uppercase tracking-widest">Metadata</h3>
                        <div className="grid grid-cols-2 gap-y-2 text-sm">
                            <span className="text-zinc-500">Status</span>
                            <Badge variant={getStatusVariant(job.status) as any} className="w-fit capitalize">{job.status.toLowerCase()}</Badge>
                            <span className="text-zinc-500">Type</span>
                            <span className="font-mono text-zinc-300">{job.task_type || job.payload?.task_type || '—'}</span>
                            <span className="text-zinc-500">Node</span>
                            <span className="font-mono text-zinc-300 truncate">{job.node_id || '—'}</span>
                            <span className="text-zinc-500">Started</span>
                            <span className="text-zinc-300">{job.started_at ? new Date(job.started_at).toLocaleString() : '—'}</span>
                            <span className="text-zinc-500">Duration</span>
                            <span className="text-zinc-300">{job.duration_seconds != null ? `${job.duration_seconds.toFixed(2)}s` : '—'}</span>
                            {job.target_tags && job.target_tags.length > 0 && (
                                <>
                                    <span className="text-zinc-500">Tags</span>
                                    <div className="flex flex-wrap gap-1">
                                        {job.target_tags.map(t => (
                                            <span key={t} className="px-1.5 py-0.5 rounded bg-zinc-800 text-[10px] border border-zinc-700 text-zinc-400">{t}</span>
                                        ))}
                                    </div>
                                </>
                            )}
                        </div>
                    </section>

                    {/* Result */}
                    {resultData && Object.keys(resultData).length > 0 && (
                        <section className="space-y-2">
                            <h3 className="text-2xs font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-1.5">
                                <CheckCircle2 className="h-3 w-3 text-green-500" /> Result
                            </h3>
                            <pre className="text-xs text-green-400 font-mono bg-zinc-950 rounded-lg p-3 overflow-auto max-h-48 whitespace-pre-wrap">
                                {JSON.stringify(resultData, null, 2)}
                            </pre>
                        </section>
                    )}

                    {/* Flight Recorder */}
                    {flightRecorder && (
                        <section className="space-y-2">
                            <h3 className="text-2xs font-bold text-red-500 uppercase tracking-widest flex items-center gap-1.5">
                                <AlertTriangle className="h-3 w-3" /> Flight Recorder
                            </h3>
                            <div className="bg-zinc-950 rounded-lg p-3 space-y-2 border border-red-500/20">
                                {flightRecorder.error && (
                                    <p className="text-sm text-red-400 font-medium">{flightRecorder.error}</p>
                                )}
                                {flightRecorder.exit_code != null && (
                                    <p className="text-xs text-zinc-500">Exit code: <span className="font-mono text-zinc-300">{flightRecorder.exit_code}</span></p>
                                )}
                                {flightRecorder.stack_trace && (
                                    <pre className="text-xs text-zinc-400 font-mono overflow-auto max-h-40 whitespace-pre-wrap border-t border-zinc-800 pt-2">
                                        {flightRecorder.stack_trace}
                                    </pre>
                                )}
                            </div>
                        </section>
                    )}

                    {/* Payload */}
                    <section className="space-y-2">
                        <h3 className="text-2xs font-bold text-zinc-500 uppercase tracking-widest">Payload</h3>
                        <pre className="text-xs text-zinc-400 font-mono bg-zinc-950 rounded-lg p-3 overflow-auto max-h-40 whitespace-pre-wrap">
                            {JSON.stringify(job.payload, null, 2)}
                        </pre>
                    </section>
                </div>
            </SheetContent>
        </Sheet>
    );
};

const PAGE_SIZE = 50;

const Jobs = () => {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(0);
    const [filterText, setFilterText] = useState('');
    const [filterStatus, setFilterStatus] = useState<string>('all');
    const [selectedJob, setSelectedJob] = useState<Job | null>(null);
    const [detailOpen, setDetailOpen] = useState(false);
    const [loading, setLoading] = useState(true);

    // Dispatch form state
    const [newTaskType, setNewTaskType] = useState('web_task');
    const [newTaskPayload, setNewTaskPayload] = useState('{}');
    const [payloadError, setPayloadError] = useState<string | null>(null);
    const [targetTags, setTargetTags] = useState('');
    const [capabilityReqs, setCapabilityReqs] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [logModalGuid, setLogModalGuid] = useState<string | null>(null);

    const fetchJobs = async (p = page) => {
        try {
            const [jobsRes, countRes] = await Promise.all([
                authenticatedFetch(`/jobs?skip=${p * PAGE_SIZE}&limit=${PAGE_SIZE}`),
                authenticatedFetch('/jobs/count'),
            ]);
            if (jobsRes.ok) setJobs(await jobsRes.json());
            if (countRes.ok) { const d = await countRes.json(); setTotal(d.total); }
        } catch (e) {
            console.error(e);
            toast.error('Failed to load jobs');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchJobs(page);
        const interval = setInterval(() => fetchJobs(page), 10000);
        return () => clearInterval(interval);
    }, [page]);

    useWebSocket((event) => {
        if (event === 'job:created' || event === 'job:updated') fetchJobs(page);
    });

    const createJob = async () => {
        try {
            setIsSubmitting(true);
            setPayloadError(null);
            const payload = JSON.parse(newTaskPayload);

            // Parse tags: "linux, gpu" → ["linux", "gpu"]
            const tags = targetTags.trim()
                ? targetTags.split(',').map(t => t.trim()).filter(Boolean)
                : undefined;

            // Parse capability requirements: "python:3.11, docker:24" → { python: "3.11", docker: "24" }
            const caps = capabilityReqs.trim()
                ? Object.fromEntries(
                    capabilityReqs.split(',')
                        .map(s => s.trim().split(':').map(p => p.trim()))
                        .filter(parts => parts.length === 2 && parts[0])
                  )
                : undefined;

            const res = await authenticatedFetch('/jobs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    task_type: newTaskType,
                    payload,
                    ...(tags && { target_tags: tags }),
                    ...(caps && { capability_requirements: caps }),
                }),
            });
            if (res.ok) {
                toast.success('Job dispatched successfully');
                fetchJobs();
                setNewTaskPayload('{}');
                setTargetTags('');
                setCapabilityReqs('');
            } else {
                const err = await res.json();
                toast.error(err.detail || 'Failed to dispatch job');
            }
        } catch (e) {
            console.error('Invalid JSON Payload', e);
            setPayloadError('Invalid JSON Payload');
        } finally {
            setIsSubmitting(false);
        }
    };

    const openDetail = (job: Job) => {
        setSelectedJob(job);
        setDetailOpen(true);
    };

    const cancelJob = async (guid: string) => {
        try {
            const res = await authenticatedFetch(`/jobs/${guid}/cancel`, { method: 'PATCH' });
            if (res.ok) {
                toast.success('Job cancelled');
                fetchJobs();
            } else {
                toast.error('Failed to cancel job');
            }
        } catch (e) {
            console.error(e);
            toast.error('Failed to cancel job');
        }
    };

    const filteredJobs = jobs.filter(j => {
        const matchesText = !filterText || j.guid.toLowerCase().includes(filterText.toLowerCase());
        const matchesStatus = filterStatus === 'all' || j.status.toLowerCase() === filterStatus.toLowerCase();
        return matchesText && matchesStatus;
    });

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white">Jobs</h1>
                    <p className="text-sm text-zinc-500 mt-1">Dispatch and monitor task payloads.</p>
                </div>
                <div className="flex items-center gap-2">
                    <Button variant="outline" className="border-zinc-800 bg-zinc-900/50 hover:bg-zinc-900" asChild>
                        <Link to="/audit">
                            <History className="mr-2 h-4 w-4" />
                            Audit Log
                        </Link>
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                {/* Dispatch Form */}
                <Card className="bg-zinc-925 border-zinc-800/50">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-lg font-bold text-white">
                            <Plus className="h-5 w-5 text-primary" />
                            Submit New Job
                        </CardTitle>
                        <CardDescription className="text-zinc-500">Configure a manual orchestration payload.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">Task Definition</label>
                            <Select value={newTaskType} onValueChange={setNewTaskType}>
                                <SelectTrigger className="bg-zinc-900 border-zinc-800 text-white h-11">
                                    <SelectValue placeholder="Select type" />
                                </SelectTrigger>
                                <SelectContent className="bg-zinc-900 border-zinc-800 text-white">
                                    <SelectItem value="web_task">Web Task (Puppeteer)</SelectItem>
                                    <SelectItem value="python_script">Python Executor</SelectItem>
                                    <SelectItem value="file_download">File Provisioner</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">JSON Payload</label>
                            <div className="relative">
                                <Terminal className="absolute top-3 left-3 h-4 w-4 text-zinc-600" />
                                <textarea
                                    value={newTaskPayload}
                                    onChange={e => { setNewTaskPayload(e.target.value); setPayloadError(null); }}
                                    className={`w-full h-32 pl-10 pr-4 py-3 bg-zinc-900 border ${payloadError ? 'border-red-500/50' : 'border-zinc-800'} text-green-500 rounded-xl font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all`}
                                />
                                {payloadError && <p className="text-xs text-red-400 mt-1">{payloadError}</p>}
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-zinc-400 uppercase tracking-widest flex items-center gap-1.5">
                                <Tag className="h-3 w-3" /> Target Tags
                                <span className="text-zinc-600 normal-case font-normal">(optional)</span>
                            </label>
                            <Input
                                placeholder="linux, gpu, secure"
                                value={targetTags}
                                onChange={e => setTargetTags(e.target.value)}
                                className="bg-zinc-900 border-zinc-800 text-white h-9 font-mono text-sm placeholder:text-zinc-600"
                            />
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-zinc-400 uppercase tracking-widest flex items-center gap-1.5">
                                <Cpu className="h-3 w-3" /> Capability Requirements
                                <span className="text-zinc-600 normal-case font-normal">(optional)</span>
                            </label>
                            <Input
                                placeholder="python:3.11, docker:24.0"
                                value={capabilityReqs}
                                onChange={e => setCapabilityReqs(e.target.value)}
                                className="bg-zinc-900 border-zinc-800 text-white h-9 font-mono text-sm placeholder:text-zinc-600"
                            />
                        </div>

                        <Button
                            className="w-full h-11 bg-primary hover:bg-primary/90 text-white font-bold rounded-xl shadow-lg shadow-primary/10 transition-all active:scale-[0.98]"
                            onClick={createJob}
                            disabled={isSubmitting}
                        >
                            <Play className="mr-2 h-4 w-4 fill-current" />
                            {isSubmitting ? 'Dispatching...' : 'Dispatch Payload'}
                        </Button>
                    </CardContent>
                </Card>

                {/* Jobs Table */}
                <Card className="xl:col-span-2 bg-zinc-925 border-zinc-800/50 overflow-hidden">
                    <CardHeader className="flex flex-row items-center justify-between">
                        <div>
                            <CardTitle className="text-lg font-bold text-white">Queue Monitor</CardTitle>
                            <CardDescription className="text-zinc-500">Real-time status of dispatched tasks.</CardDescription>
                        </div>
                        <div className="flex items-center gap-2">
                            <Select value={filterStatus} onValueChange={(v) => { setFilterStatus(v); setPage(0); }}>
                                <SelectTrigger className="bg-zinc-900 border-zinc-800 text-white h-9 w-32 text-xs">
                                    <SelectValue placeholder="Status" />
                                </SelectTrigger>
                                <SelectContent className="bg-zinc-900 border-zinc-800 text-white">
                                    <SelectItem value="all">All Status</SelectItem>
                                    <SelectItem value="pending">Pending</SelectItem>
                                    <SelectItem value="assigned">Assigned</SelectItem>
                                    <SelectItem value="completed">Completed</SelectItem>
                                    <SelectItem value="failed">Failed</SelectItem>
                                    <SelectItem value="cancelled">Cancelled</SelectItem>
                                    <SelectItem value="security_rejected">Security Rejected</SelectItem>
                                </SelectContent>
                            </Select>
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-600" />
                                <Input
                                    placeholder="Filter GUID..."
                                    value={filterText}
                                    onChange={e => setFilterText(e.target.value)}
                                    className="pl-9 bg-zinc-900 border-zinc-800 h-9 w-44 text-sm text-white"
                                />
                            </div>
                        </div>
                    </CardHeader>
                    <Table>
                        <TableHeader className="bg-zinc-900/50 border-zinc-800">
                            <TableRow className="border-zinc-800 hover:bg-transparent">
                                <TableHead className="text-zinc-500 font-bold uppercase text-2xs tracking-widest pl-6">GUID</TableHead>
                                <TableHead className="text-zinc-500 font-bold uppercase text-2xs tracking-widest">Type</TableHead>
                                <TableHead className="text-zinc-500 font-bold uppercase text-2xs tracking-widest">Status</TableHead>
                                <TableHead className="text-zinc-500 font-bold uppercase text-2xs tracking-widest">Target Node</TableHead>
                                <TableHead className="text-zinc-500 font-bold uppercase text-2xs tracking-widest">Timestamp</TableHead>
                                <TableHead className="text-zinc-500 font-bold uppercase text-2xs tracking-widest pr-6 text-right">Detail</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {loading ? (
                                Array.from({ length: 5 }).map((_, i) => (
                                    <TableRow key={i} className="border-zinc-800">
                                        {Array.from({ length: 6 }).map((_, j) => (
                                            <TableCell key={j} className="py-3 pl-6">
                                                <div className="h-3 bg-zinc-800 animate-pulse rounded w-3/4" />
                                            </TableCell>
                                        ))}
                                    </TableRow>
                                ))
                            ) : filteredJobs.length > 0 ? (
                                filteredJobs.map(job => (
                                    <TableRow key={job.guid} className="border-zinc-800 hover:bg-zinc-900/30 transition-colors cursor-pointer" onClick={() => openDetail(job)}>
                                        <TableCell className="font-mono text-zinc-400 pl-6">
                                            <div className="flex items-center gap-2">
                                                <Hash className="h-3 w-3 text-zinc-600" />
                                                {job.guid.substring(0, 8)}
                                            </div>
                                        </TableCell>
                                        <TableCell className="text-white font-medium">
                                            {job.task_type || job.payload?.task_type || 'Generic'}
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant={getStatusVariant(job.status) as any} className="capitalize">
                                                {job.status.toLowerCase()}
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="font-mono text-xs text-zinc-500">
                                            {job.node_id ? job.node_id.substring(0, 12) : '-'}
                                        </TableCell>
                                        <TableCell className="text-zinc-500 text-xs">
                                            <div className="flex items-center gap-2">
                                                <Clock className="h-3 w-3" />
                                                {job.started_at ? new Date(job.started_at).toLocaleTimeString() : '-'}
                                            </div>
                                        </TableCell>
                                        <TableCell className="pr-6 text-right" onClick={e => { e.stopPropagation(); openDetail(job); }}>
                                            <Button variant="ghost" size="icon" className="h-8 w-8 text-zinc-600 hover:text-white hover:bg-zinc-800 rounded-lg">
                                                <MoreHorizontal className="h-4 w-4" />
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))
                            ) : (
                                <TableRow>
                                    <TableCell colSpan={6} className="h-32 text-center text-zinc-600">
                                        {filterText ? 'No jobs match that GUID.' : 'Queue is currently empty.'}
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                    {total > PAGE_SIZE && (
                        <div className="flex items-center justify-between px-6 py-3 border-t border-zinc-800 bg-zinc-900/30">
                            <span className="text-xs text-zinc-500">
                                Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total)} of {total}
                            </span>
                            <div className="flex items-center gap-2">
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-7 text-xs text-zinc-400 hover:text-white"
                                    disabled={page === 0}
                                    onClick={() => setPage(p => p - 1)}
                                >
                                    Previous
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-7 text-xs text-zinc-400 hover:text-white"
                                    disabled={(page + 1) * PAGE_SIZE >= total}
                                    onClick={() => setPage(p => p + 1)}
                                >
                                    Next
                                </Button>
                            </div>
                        </div>
                    )}
                </Card>
            </div>

            <JobDetailPanel job={selectedJob} open={detailOpen} onClose={() => setDetailOpen(false)} onCancel={cancelJob} onViewOutput={setLogModalGuid} />
            <ExecutionLogModal guid={logModalGuid ?? ''} open={!!logModalGuid} onClose={() => setLogModalGuid(null)} />
        </div>
    );
};

export default Jobs;
