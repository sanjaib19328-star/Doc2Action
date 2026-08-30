import React, { useState, useEffect, useCallback, useRef } from 'react';
import { NavLink, useNavigate, Link } from 'react-router-dom';
import {
  Layers,
  LayoutDashboard,
  Globe,
  Database,
  Bot,
  Terminal,
  ShieldCheck,
  History,
  LogOut,
  User as UserIcon,
  Menu,
  X,
  ChevronDown,
  Plus,
  Server,
  Check,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useApplication } from '../../context/ApplicationContext';
import { healthApi } from '../../api/health';

interface SidebarItem {
  label: string;
  path: string;
  icon: React.ReactNode;
}

export const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout } = useAuth();
  const { applications, selectedApplication, selectedApplicationId, selectApplication, isLoading: appsLoading } = useApplication();
  const navigate = useNavigate();

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [appDropdownOpen, setAppDropdownOpen] = useState(false);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const dropdownRef = useRef<HTMLDivElement>(null);

  const checkStatus = useCallback(async () => {
    const res = await healthApi.checkHealth();
    if (res.isOnline) {
      setBackendStatus('online');
    } else {
      setBackendStatus('offline');
    }
  }, []);

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 15000);
    return () => clearInterval(interval);
  }, [checkStatus]);

  // Click outside to close app dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setAppDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const navItems: SidebarItem[] = [
    { label: 'Applications', path: '/applications', icon: <Layers className="w-4 h-4" /> },
    { label: 'Overview', path: '/dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
    { label: 'OpenAPI Discovery', path: '/api-discovery', icon: <Globe className="w-4 h-4" /> },
    { label: 'API Catalog', path: '/api-catalog', icon: <Database className="w-4 h-4" /> },
    { label: 'RAG Knowledge Base', path: '/rag', icon: <Server className="w-4 h-4" /> },
    { label: 'AI Agent', path: '/agent', icon: <Bot className="w-4 h-4" /> },
    { label: 'Human Verification', path: '/verification', icon: <ShieldCheck className="w-4 h-4" /> },
    { label: 'Direct Execution', path: '/execution', icon: <Terminal className="w-4 h-4" /> },
    { label: 'Execution Logs', path: '/execution-logs', icon: <History className="w-4 h-4" /> },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-900">
      {/* Top Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
        <div className="px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3 sm:space-x-4">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 focus:outline-hidden"
              aria-label="Toggle navigation"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>

            <Link to="/dashboard" className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-xl bg-linear-to-tr from-sky-600 to-indigo-600 flex items-center justify-center font-black text-white text-xs shadow-xs tracking-wider">
                D2A
              </div>
              <span className="text-lg font-bold tracking-tight text-slate-900 hidden sm:inline-block">
                Doc<span className="text-sky-600">2</span>Action
              </span>
            </Link>

            {/* Application Selector */}
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setAppDropdownOpen(!appDropdownOpen)}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all ${
                  selectedApplication
                    ? 'bg-slate-50 border-slate-300 hover:bg-slate-100 text-slate-800'
                    : 'bg-amber-50 border-amber-300 text-amber-900 hover:bg-amber-100'
                }`}
              >
                <Layers className="w-3.5 h-3.5 text-sky-600 shrink-0" />
                <div className="flex flex-col text-left">
                  <span className="text-[10px] text-slate-400 font-bold uppercase leading-none">Application</span>
                  <span className="truncate max-w-[140px] sm:max-w-[200px] leading-tight font-extrabold text-slate-900">
                    {appsLoading ? 'Loading...' : selectedApplication ? selectedApplication.name : 'No App Selected'}
                  </span>
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0 ml-0.5" />
              </button>

              {appDropdownOpen && (
                <div className="absolute left-0 mt-2 w-72 bg-white rounded-2xl shadow-xl border border-slate-200 py-2 z-50 animate-in fade-in zoom-in-95 duration-150">
                  <div className="px-3 py-1.5 border-b border-slate-100 flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Switch Application
                    </span>
                    <Link
                      to="/applications"
                      onClick={() => setAppDropdownOpen(false)}
                      className="text-[11px] font-semibold text-sky-600 hover:text-sky-700"
                    >
                      Manage
                    </Link>
                  </div>

                  <div className="max-h-56 overflow-y-auto py-1">
                    {applications.length === 0 ? (
                      <div className="px-4 py-3 text-center text-xs text-slate-400">
                        No applications found.
                      </div>
                    ) : (
                      applications.map((app) => {
                        const isSelected = app.id === selectedApplicationId;
                        return (
                          <button
                            key={app.id}
                            onClick={() => {
                              selectApplication(app.id);
                              setAppDropdownOpen(false);
                            }}
                            className={`w-full text-left px-3.5 py-2 text-xs flex items-center justify-between transition-colors ${
                              isSelected
                                ? 'bg-sky-50 text-sky-900 font-bold'
                                : 'text-slate-700 hover:bg-slate-50'
                            }`}
                          >
                            <div className="truncate pr-2">
                              <p className="truncate">{app.name}</p>
                              {app.description && (
                                <p className="text-[10px] text-slate-400 truncate font-normal">{app.description}</p>
                              )}
                            </div>
                            {isSelected && <Check className="w-4 h-4 text-sky-600 shrink-0" />}
                          </button>
                        );
                      })
                    )}
                  </div>

                  <div className="pt-1.5 border-t border-slate-100 px-2">
                    <Link
                      to="/applications"
                      onClick={() => setAppDropdownOpen(false)}
                      className="w-full flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-sky-600 hover:bg-sky-50 transition-colors"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Create New Application</span>
                    </Link>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Backend Status & User Profile Actions */}
          <div className="flex items-center space-x-3 sm:space-x-4">
            {/* Real Backend Health Indicator */}
            <div
              className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${
                backendStatus === 'online'
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : backendStatus === 'offline'
                  ? 'bg-rose-50 text-rose-700 border-rose-200'
                  : 'bg-amber-50 text-amber-700 border-amber-200'
              }`}
              title={`Backend status: ${backendStatus}`}
            >
              <span className="relative flex h-2 w-2">
                {backendStatus === 'online' && (
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                )}
                <span
                  className={`relative inline-flex rounded-full h-2 w-2 ${
                    backendStatus === 'online'
                      ? 'bg-emerald-500'
                      : backendStatus === 'offline'
                      ? 'bg-rose-500'
                      : 'bg-amber-500'
                  }`}
                ></span>
              </span>
              <span className="text-[11px] font-bold hidden md:inline">
                {backendStatus === 'online' ? 'Backend Online' : backendStatus === 'offline' ? 'Backend Offline' : 'Connecting...'}
              </span>
            </div>

            {user && (
              <div className="flex items-center space-x-3 border-l border-slate-200 pl-3">
                <div className="w-8 h-8 rounded-full bg-sky-100 border border-sky-200 flex items-center justify-center text-sky-700 font-semibold text-xs">
                  {user.full_name ? user.full_name.charAt(0).toUpperCase() : <UserIcon className="w-4 h-4" />}
                </div>
                <div className="hidden lg:block text-left">
                  <p className="text-xs font-bold text-slate-800 leading-none">{user.full_name || 'Operator'}</p>
                  <p className="text-[10px] text-slate-400 font-mono truncate max-w-[140px]">{user.email}</p>
                </div>
                <button
                  onClick={handleLogout}
                  title="Log out"
                  className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar Navigation - Desktop */}
        <aside className="hidden lg:flex lg:flex-shrink-0 lg:w-64 bg-white border-r border-slate-200 flex-col justify-between">
          <div className="p-4 space-y-4">
            <div className="px-3 flex items-center justify-between">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Application Workspace
              </p>
              {selectedApplication && (
                <span className="text-[10px] font-mono text-sky-600 truncate max-w-[90px]">
                  {selectedApplication.name}
                </span>
              )}
            </div>
            <nav className="space-y-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center px-3 py-2 text-xs font-medium rounded-xl transition-all ${
                      isActive
                        ? 'bg-sky-50 text-sky-700 font-bold border border-sky-100 shadow-xs'
                        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                    }`
                  }
                >
                  <span className="mr-3 text-slate-400 group-hover:text-slate-600">{item.icon}</span>
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>

          {/* Active Application Context Footer in Sidebar */}
          <div className="p-4 border-t border-slate-100 bg-slate-50/50 text-xs">
            {selectedApplication ? (
              <div>
                <div className="flex items-center space-x-1.5 text-slate-900 font-bold">
                  <Layers className="w-3.5 h-3.5 text-sky-600 shrink-0" />
                  <span className="truncate">{selectedApplication.name}</span>
                </div>
                <p className="text-[10px] text-slate-400 font-mono mt-0.5 truncate">
                  ID: {selectedApplication.id}
                </p>
              </div>
            ) : (
              <div className="text-amber-800">
                <p className="font-bold text-[11px]">No App Selected</p>
                <Link to="/applications" className="text-[10px] text-sky-600 underline font-semibold mt-0.5 block">
                  Select or Create App
                </Link>
              </div>
            )}
          </div>
        </aside>

        {/* Mobile Sidebar Overlay */}
        {mobileMenuOpen && (
          <div className="fixed inset-0 z-40 lg:hidden flex">
            <div
              className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs"
              onClick={() => setMobileMenuOpen(false)}
            />
            <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white border-r border-slate-200 pt-5 pb-4 shadow-xl">
              <div className="px-4 flex items-center justify-between pb-3 border-b border-slate-100">
                <span className="text-base font-bold text-slate-900">Navigation Menu</span>
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-1 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-100"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <nav className="mt-4 flex-1 px-3 space-y-1">
                {navItems.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center px-3 py-2 text-xs font-medium rounded-xl ${
                        isActive
                          ? 'bg-sky-50 text-sky-700 font-bold border border-sky-100'
                          : 'text-slate-600 hover:bg-slate-100'
                      }`
                    }
                  >
                    <span className="mr-3">{item.icon}</span>
                    {item.label}
                  </NavLink>
                ))}
              </nav>
            </div>
          </div>
        )}

        {/* Main Content Viewport */}
        <main className="flex-1 overflow-y-auto bg-slate-50 p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">{children}</div>
        </main>
      </div>
    </div>
  );
};
