import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Boxes, CheckCircle2, Clock, AlertCircle, Loader2, Plus, Cpu, Globe, Zap } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { authenticatedFetch } from '../auth';
import { CreateBlueprintDialog } from '../components/CreateBlueprintDialog';
import { CreateTemplateDialog } from '../components/CreateTemplateDialog';

interface Template {
    id: string;
    friendly_name: string;
    canonical_id: string;
    last_built_image?: string;
    last_built_at?: string;
    runtime_blueprint_id: string;
    network_blueprint_id: string;
}

interface Blueprint {
    id: string;
    type: 'RUNTIME' | 'NETWORK';
    name: string;
    definition: any;
    version: number;
    created_at: string;
}

const TemplateCard = ({ template }: { template: Template }) => {
    const queryClient = useQueryClient();
    const [buildStatus, setBuildStatus] = useState<'idle' | 'building' | 'success' | 'failed'>('idle');

    const buildMutation = useMutation({
        mutationFn: async () => {
            const res = await authenticatedFetch(`/api/templates/${template.id}/build`, { method: 'POST' });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Build failed');
            }
            return await res.json();
        },
        onMutate: () => setBuildStatus('building'),
        onSuccess: () => {
            setBuildStatus('success');
            queryClient.invalidateQueries({ queryKey: ['templates'] });
        },
        onError: () => setBuildStatus('failed'),
    });

    return (
        <Card className="bg-zinc-925 border-zinc-800/50 hover:border-primary/30 transition-all flex flex-col shadow-none">
            <CardHeader className="pb-4">
                <div className="flex items-start justify-between">
                    <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
                        <Boxes className="h-5 w-5 text-primary" />
                    </div>
                    <Badge variant="outline" className="font-mono text-[10px] border-zinc-800 text-zinc-500 py-0 px-1.5 h-5">
                        {template.canonical_id}
                    </Badge>
                </div>
                <CardTitle className="mt-4 text-white font-bold">{template.friendly_name}</CardTitle>
                <CardDescription className="text-zinc-500 text-xs truncate">
                    {template.last_built_image
                        ? `Image: ${template.last_built_image}`
                        : 'Never built'}
                </CardDescription>
            </CardHeader>
            <CardContent className="flex-1 pb-4">
                {buildStatus === 'success' && (
                    <div className="flex items-center gap-2 text-[10px] text-green-500 font-bold uppercase tracking-wider animate-in fade-in">
                        <CheckCircle2 className="h-3 w-3" /> Build succeeded
                    </div>
                )}
                {buildStatus === 'failed' && (
                    <div className="flex items-center gap-2 text-[10px] text-red-500 font-bold uppercase tracking-wider animate-in fade-in">
                        <AlertCircle className="h-3 w-3" /> Build failed
                    </div>
                )}
                {buildStatus === 'idle' && template.last_built_at && (
                    <div className="flex items-center gap-2 text-[10px] text-zinc-500 font-medium">
                        <Clock className="h-3 w-3" />
                        {new Date(template.last_built_at).toLocaleString()}
                    </div>
                )}
            </CardContent>
            <CardFooter className="bg-white/[0.01] border-t border-zinc-800/50 pt-4">
                <Button
                    onClick={() => buildMutation.mutate()}
                    disabled={buildStatus === 'building'}
                    className="w-full h-9 bg-primary hover:bg-primary/90 text-white font-bold rounded-lg transition-all"
                >
                    {buildStatus === 'building' ? (
                        <><Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" /> Building...</>
                    ) : (
                        <><Zap className="mr-2 h-3.5 w-3.5 fill-current" /> Build Image</>
                    )}
                </Button>
            </CardFooter>
        </Card>
    );
};

const BlueprintItem = ({ blueprint }: { blueprint: Blueprint }) => (
    <div className="group flex items-center justify-between p-4 bg-zinc-925 border border-zinc-800/50 rounded-xl hover:border-primary/20 transition-all">
        <div className="flex items-center gap-4">
            <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${
                blueprint.type === 'RUNTIME' ? 'bg-blue-500/10' : 'bg-green-500/10'
            }`}>
                {blueprint.type === 'RUNTIME' ? 
                    <Cpu className={`h-5 w-5 ${blueprint.type === 'RUNTIME' ? 'text-blue-400' : 'text-green-400'}`} /> : 
                    <Globe className="h-5 w-5 text-green-400" />
                }
            </div>
            <div>
                <div className="flex items-center gap-2">
                    <h4 className="text-sm font-bold text-white">{blueprint.name}</h4>
                    <Badge variant="outline" className="text-[10px] h-4 px-1 border-zinc-800 text-zinc-500">v{blueprint.version}</Badge>
                </div>
                <p className="text-xs text-zinc-500 mt-0.5">
                    {blueprint.type === 'RUNTIME' 
                        ? `OS: ${blueprint.definition.base_os} | ${blueprint.definition.tools?.length || 0} tools`
                        : `${blueprint.definition.egress_rules?.length || 0} egress rules | Mode: ${blueprint.definition.policy}`
                    }
                </p>
            </div>
        </div>
        <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button variant="ghost" size="sm" className="text-zinc-500 hover:text-white">View JSON</Button>
        </div>
    </div>
);

const Templates = () => {
    const [activeTab, setActiveTab] = useState<'templates' | 'blueprints'>('templates');
    const [isBlueprintOpen, setIsBlueprintOpen] = useState(false);
    const [isTemplateOpen, setIsTemplateOpen] = useState(false);

    const { data: templates = [], isLoading: loadingTemplates } = useQuery<Template[]>({
        queryKey: ['templates'],
        queryFn: async () => {
            const res = await authenticatedFetch('/api/templates');
            return await res.json();
        }
    });

    const { data: blueprints = [], isLoading: loadingBlueprints } = useQuery<Blueprint[]>({
        queryKey: ['blueprints'],
        queryFn: async () => {
            const res = await authenticatedFetch('/api/blueprints');
            return await res.json();
        }
    });

    const isLoading = loadingTemplates || loadingBlueprints;

    return (
        <div className="space-y-8 animate-in fade-in duration-500 max-w-6xl mx-auto">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Puppet Foundry</h1>
                    <p className="text-zinc-500 text-sm">Compose and build immutable agent environments from standardized blueprints.</p>
                </div>
                <div className="flex gap-2">
                    <Button 
                        variant="outline" 
                        className="bg-zinc-900 border-zinc-800 text-white h-10 px-4 rounded-xl"
                        onClick={() => setIsBlueprintOpen(true)}
                    >
                        <Plus className="mr-2 h-4 w-4" /> New Blueprint
                    </Button>
                    <Button 
                        className="bg-primary hover:bg-primary/90 text-white h-10 px-4 rounded-xl font-bold shadow-lg shadow-primary/10"
                        onClick={() => setIsTemplateOpen(true)}
                    >
                        <Plus className="mr-2 h-4 w-4" /> New Template
                    </Button>
                </div>
            </div>

            <div className="flex border-b border-zinc-800/50 gap-8">
                <button 
                    onClick={() => setActiveTab('templates')}
                    className={`pb-4 text-sm font-bold transition-all relative ${
                        activeTab === 'templates' ? 'text-primary' : 'text-zinc-500 hover:text-zinc-300'
                    }`}
                >
                    Templates ({templates.length})
                    {activeTab === 'templates' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary rounded-full" />}
                </button>
                <button 
                    onClick={() => setActiveTab('blueprints')}
                    className={`pb-4 text-sm font-bold transition-all relative ${
                        activeTab === 'blueprints' ? 'text-primary' : 'text-zinc-500 hover:text-zinc-300'
                    }`}
                >
                    Blueprints ({blueprints.length})
                    {activeTab === 'blueprints' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary rounded-full" />}
                </button>
            </div>

            {isLoading ? (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="h-48 rounded-2xl bg-zinc-900/50 border border-zinc-800 animate-pulse" />
                    ))}
                </div>
            ) : activeTab === 'templates' ? (
                templates.length > 0 ? (
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                        {templates.map(t => <TemplateCard key={t.id} template={t} />)}
                    </div>
                ) : (
                    <div className="py-20 text-center rounded-2xl border border-dashed border-zinc-800 bg-zinc-900/20">
                        <Boxes className="h-12 w-12 text-zinc-800 mx-auto mb-4" />
                        <h3 className="text-zinc-400 font-medium">No templates found</h3>
                        <p className="text-zinc-600 text-sm mt-1">Compose your first template using blueprints.</p>
                    </div>
                )
            ) : (
                <div className="space-y-4">
                    {blueprints.length > 0 ? (
                        blueprints.map(b => <BlueprintItem key={b.id} blueprint={b} />)
                    ) : (
                        <div className="py-20 text-center rounded-2xl border border-dashed border-zinc-800 bg-zinc-900/20">
                            <Cpu className="h-12 w-12 text-zinc-800 mx-auto mb-4" />
                            <h3 className="text-zinc-400 font-medium">No blueprints found</h3>
                            <p className="text-zinc-600 text-sm mt-1">Create runtime or network blueprints to get started.</p>
                        </div>
                    )}
                </div>
            )}

            <CreateBlueprintDialog open={isBlueprintOpen} onOpenChange={setIsBlueprintOpen} />
            <CreateTemplateDialog open={isTemplateOpen} onOpenChange={setIsTemplateOpen} />
        </div>
    );
};

export default Templates;
