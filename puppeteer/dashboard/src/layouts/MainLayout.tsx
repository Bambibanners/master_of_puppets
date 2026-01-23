import { useState } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import {
    LayoutDashboard,
    Network,
    Server,
    ShieldCheck,
    Settings,
    Menu,
    Cpu
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Separator } from '@/components/ui/separator';

const MainLayout = () => {
    const [isMobileOpen, setIsMobileOpen] = useState(false);

    const NavItem = ({ to, icon: Icon, label }: { to: string, icon: any, label: string }) => (
        <NavLink
            to={to}
            className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all hover:bg-accent hover:text-accent-foreground ${isActive ? "bg-accent text-accent-foreground" : "text-muted-foreground"
                }`
            }
            onClick={() => setIsMobileOpen(false)}
        >
            <Icon className="h-4 w-4" />
            {label}
        </NavLink>
    );

    const SidebarContent = () => (
        <div className="flex h-full max-h-screen flex-col gap-2">
            <div className="flex h-14 items-center border-b px-4 lg:h-[60px] lg:px-6">
                <a href="/" className="flex items-center gap-2 font-semibold">
                    <Network className="h-6 w-6" />
                    <span className="">Master of Puppets</span>
                </a>
            </div>
            <div className="flex-1 overflow-auto py-2">
                <nav className="grid items-start px-2 text-sm font-medium lg:px-4">
                    <NavItem to="/" icon={LayoutDashboard} label="Dashboard" />
                    <Separator className="my-2" />
                    <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase">
                        Monitoring
                    </div>
                    <NavItem to="/nodes" icon={Server} label="Puppets" />
                    <NavItem to="/jobs" icon={Cpu} label="Orchestration" />

                    <Separator className="my-2" />
                    <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase">
                        Security
                    </div>
                    <NavItem to="/signatures" icon={ShieldCheck} label="Signatures & Keys" />

                    <Separator className="my-2" />
                    <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase">
                        System
                    </div>
                    <NavItem to="/admin" icon={Settings} label="Settings" />
                </nav>
            </div>
            <div className="mt-auto border-t p-4 text-xs text-muted-foreground text-center">
                v1.2.0 • Online
            </div>
        </div>
    );

    return (
        <div className="grid min-h-screen w-full md:grid-cols-[220px_1fr] lg:grid-cols-[280px_1fr]">
            {/* Desktop Sidebar */}
            <div className="hidden border-r bg-muted/40 md:block">
                <SidebarContent />
            </div>

            {/* Mobile Sidebar & Main Content */}
            <div className="flex flex-col">
                <header className="flex h-14 items-center gap-4 border-b bg-muted/40 px-4 lg:h-[60px] lg:px-6">
                    <Sheet open={isMobileOpen} onOpenChange={setIsMobileOpen}>
                        <SheetTrigger asChild>
                            <Button variant="outline" size="icon" className="shrink-0 md:hidden">
                                <Menu className="h-5 w-5" />
                                <span className="sr-only">Toggle navigation</span>
                            </Button>
                        </SheetTrigger>
                        <SheetContent side="left" className="flex flex-col p-0">
                            <SidebarContent />
                        </SheetContent>
                    </Sheet>

                    {/* Topbar Content */}
                    <div className="w-full flex-1">
                        {/* Breadcrumbs or Search could go here */}
                    </div>

                    <Button variant="ghost" size="icon" className="rounded-full">
                        <span className="sr-only">User menu</span>
                        <div className="h-8 w-8 rounded-full bg-slate-200 border border-slate-300"></div>
                    </Button>
                </header>
                <main className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6 bg-background">
                    <Outlet />
                </main>
            </div>
        </div>
    );
};

export default MainLayout;
