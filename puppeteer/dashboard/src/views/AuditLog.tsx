import { useQuery } from '@tanstack/react-query';
import { ScrollText } from 'lucide-react';
import { authenticatedFetch } from '../auth';

interface AuditEntry {
    id: number;
    timestamp: string;
    username: string;
    action: string;
    resource_id: string | null;
    detail: Record<string, unknown> | null;
}

const ACTION_COLOR: Record<string, string> = {
    'node:revoke': 'text-amber-400',
    'node:reinstate': 'text-emerald-400',
    'node:delete': 'text-red-400',
    'user:create': 'text-blue-400',
    'user:delete': 'text-red-400',
    'user:role_change': 'text-violet-400',
    'permission:grant': 'text-emerald-400',
    'permission:revoke': 'text-amber-400',
    'job:cancel': 'text-amber-400',
    'key:upload': 'text-blue-400',
    'signature:delete': 'text-red-400',
    'blueprint:delete': 'text-red-400',
    'template:delete': 'text-red-400',
    'template:build': 'text-violet-400',
    'base_image:marked_updated': 'text-emerald-400',
};

const AuditLog = () => {
    const { data: entries = [], isLoading } = useQuery<AuditEntry[]>({
        queryKey: ['audit-log'],
        queryFn: async () => {
            const res = await authenticatedFetch('/admin/audit-log?limit=200');
            if (!res.ok) throw new Error('Failed to fetch audit log');
            return await res.json();
        },
        refetchInterval: 15000,
    });

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                        <ScrollText className="h-6 w-6 text-primary" />
                        Audit Log
                    </h2>
                    <p className="text-zinc-500 text-sm mt-1">Security-relevant actions, most recent first.</p>
                </div>
            </div>

            <div className="rounded-xl border border-zinc-800 overflow-hidden">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="bg-zinc-900 border-b border-zinc-800">
                            <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 w-44">Timestamp</th>
                            <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 w-28">User</th>
                            <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 w-40">Action</th>
                            <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 w-40">Resource</th>
                            <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500">Detail</th>
                        </tr>
                    </thead>
                    <tbody>
                        {isLoading ? (
                            Array.from({ length: 8 }).map((_, i) => (
                                <tr key={i} className="border-b border-zinc-800/50">
                                    {Array.from({ length: 5 }).map((_, j) => (
                                        <td key={j} className="px-4 py-3">
                                            <div className="h-3 rounded bg-zinc-800 animate-pulse w-3/4" />
                                        </td>
                                    ))}
                                </tr>
                            ))
                        ) : entries.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="px-4 py-16 text-center text-zinc-600">
                                    No audit entries yet.
                                </td>
                            </tr>
                        ) : (
                            entries.map(entry => (
                                <tr key={entry.id} className="border-b border-zinc-800/40 hover:bg-zinc-900/40 transition-colors">
                                    <td className="px-4 py-2.5 font-mono text-[11px] text-zinc-500">
                                        {new Date(entry.timestamp).toLocaleString()}
                                    </td>
                                    <td className="px-4 py-2.5 font-mono text-[11px] text-zinc-300">
                                        {entry.username}
                                    </td>
                                    <td className="px-4 py-2.5 font-mono text-[11px]">
                                        <span className={ACTION_COLOR[entry.action] ?? 'text-zinc-400'}>
                                            {entry.action}
                                        </span>
                                    </td>
                                    <td className="px-4 py-2.5 font-mono text-[11px] text-zinc-500 truncate max-w-[160px]">
                                        {entry.resource_id ?? '—'}
                                    </td>
                                    <td className="px-4 py-2.5 font-mono text-[11px] text-zinc-600 truncate max-w-[300px]">
                                        {entry.detail ? JSON.stringify(entry.detail) : '—'}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default AuditLog;
