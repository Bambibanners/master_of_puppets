import { useState, useEffect } from 'react';
import { authenticatedFetch } from '../auth';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Plus, Trash2, Loader2 } from 'lucide-react';

interface NetworkMount {
    name: string;
    path: string;
}

interface ManageMountsModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

const ManageMountsModal = ({ open, onOpenChange }: ManageMountsModalProps) => {
    const [mounts, setMounts] = useState<NetworkMount[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        if (open) {
            setLoading(true);
            setError('');
            authenticatedFetch('/config/mounts')
                .then(res => res.json())
                .then((data: NetworkMount[]) => setMounts(data))
                .catch(() => setError('Failed to load mounts.'))
                .finally(() => setLoading(false));
        }
    }, [open]);

    const addRow = () => setMounts(prev => [...prev, { name: '', path: '' }]);

    const removeRow = (i: number) => setMounts(prev => prev.filter((_, idx) => idx !== i));

    const updateRow = (i: number, field: keyof NetworkMount, value: string) => {
        setMounts(prev => prev.map((m, idx) => idx === i ? { ...m, [field]: value } : m));
    };

    const handleSave = async () => {
        setError('');
        for (const m of mounts) {
            if (!m.name.trim() || !m.path.trim()) {
                setError('All rows must have a name and path.');
                return;
            }
        }
        setSaving(true);
        try {
            const res = await authenticatedFetch('/config/mounts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mounts }),
            });
            if (!res.ok) {
                const err = await res.json();
                setError(err.detail || 'Save failed.');
            } else {
                onOpenChange(false);
            }
        } catch {
            setError('Network error.');
        } finally {
            setSaving(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[560px] bg-zinc-900 border-zinc-800">
                <DialogHeader>
                    <DialogTitle className="text-white">Network Mounts</DialogTitle>
                    <DialogDescription className="text-zinc-500">
                        Configure UNC paths distributed to all enrolled nodes at next heartbeat.
                    </DialogDescription>
                </DialogHeader>

                {loading ? (
                    <div className="py-8 flex items-center justify-center text-zinc-500 gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" /> Loading mounts...
                    </div>
                ) : (
                    <div className="space-y-3 py-2">
                        {mounts.length > 0 && (
                            <div className="grid grid-cols-[1fr_2fr_auto] gap-2 px-1">
                                <Label className="text-zinc-500 text-xs uppercase tracking-widest">Name</Label>
                                <Label className="text-zinc-500 text-xs uppercase tracking-widest">UNC Path</Label>
                                <span />
                            </div>
                        )}
                        {mounts.map((m, i) => (
                            <div key={i} className="grid grid-cols-[1fr_2fr_auto] gap-2 items-center">
                                <Input
                                    placeholder="finance_data"
                                    value={m.name}
                                    onChange={e => updateRow(i, 'name', e.target.value)}
                                    className="bg-zinc-800 border-zinc-700 text-white placeholder:text-zinc-600 h-9"
                                />
                                <Input
                                    placeholder="//server/share"
                                    value={m.path}
                                    onChange={e => updateRow(i, 'path', e.target.value)}
                                    className="bg-zinc-800 border-zinc-700 text-white placeholder:text-zinc-600 h-9 font-mono text-sm"
                                />
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-9 w-9 text-zinc-600 hover:text-red-400 hover:bg-red-500/10"
                                    onClick={() => removeRow(i)}
                                >
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </div>
                        ))}

                        {mounts.length === 0 && (
                            <p className="text-center text-zinc-600 text-sm py-4">No mounts configured.</p>
                        )}

                        <Button
                            variant="outline"
                            size="sm"
                            className="w-full border-dashed border-zinc-700 text-zinc-500 hover:text-white hover:border-zinc-500 bg-transparent"
                            onClick={addRow}
                        >
                            <Plus className="mr-2 h-3.5 w-3.5" /> Add Mount
                        </Button>

                        {error && <p className="text-red-400 text-xs">{error}</p>}
                    </div>
                )}

                <DialogFooter>
                    <Button variant="ghost" className="text-zinc-400" onClick={() => onOpenChange(false)}>Cancel</Button>
                    <Button
                        onClick={handleSave}
                        disabled={saving || loading}
                        className="bg-primary hover:bg-primary/90 text-white font-bold"
                    >
                        {saving ? <><Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" /> Saving...</> : 'Save Mounts'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
};

export default ManageMountsModal;
