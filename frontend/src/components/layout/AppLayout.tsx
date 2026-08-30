import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
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
  Server
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface SidebarItem {
  label: string;
  path: string;
  icon: React.ReactNode;
}

export const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems: SidebarItem[] = [
    { label: 'Overview', path: '/dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
    { label: 'OpenAPI Discovery', path: '/api-discovery', icon: <Globe className="w-5 h-5" /> },
    { label: 'API Catalog', path: '/api-catalog', icon: <Database className="w-5 h-5" /> },
    { label: 'RAG Knowledge Base', path: '/rag', icon: <Server className="w-5 h-5" /> },
    { label: 'AI Agent Workflows', path: '/agent', icon: <Bot className="w-5 h-5" /> },
    { label: 'Human Verification', path: '/verification', icon: <ShieldCheck className="w-5 h-5" /> },
    { label: 'Direct Execution', path: '/execution', icon: <Terminal className="w-5 h-5" /> },
    { label: 'Execution Logs', path: '/execution-logs', icon: <History className="w-5 h-5" /> },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Header */}
      <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-30">
        <div className="px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 focus:outline-none"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-sky-500 flex items-center justify-center font-bold text-white shadow-md">
                D2A
              </div>
              <span className="text-xl font-bold tracking-tight text-white">
                Doc<span className="text-sky-400">2</span>Action
              </span>
              <span className="hidden sm:inline-block ml-2 px-2 py-0.5 text-xs font-semibold bg-slate-800 text-slate-300 rounded border border-slate-700">
                v0.1.0 Platform
              </span>
            </div>
          </div>

          {/* User Profile & Actions */}
          <div className="flex items-center space-x-4">
            {user && (
              <div className="flex items-center space-x-3 border-l border-slate-800 pl-4">
                <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
                  <UserIcon className="w-4 h-4" />
                </div>
                <div className="hidden md:block text-left">
                  <p className="text-sm font-medium text-slate-200">{user.full_name || user.email}</p>
                  <p className="text-xs text-slate-400 truncate max-w-[150px]">{user.email}</p>
                </div>
                <button
                  onClick={handleLogout}
                  title="Log out"
                  className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar Navigation - Desktop */}
        <aside className="hidden lg:flex lg:flex-shrink-0 lg:w-64 bg-slate-900 border-r border-slate-800 flex-col">
          <div className="p-4">
            <p className="px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Navigation Menu
            </p>
          </div>
          <nav className="flex-1 px-3 space-y-1 overflow-y-auto">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? 'bg-sky-600 text-white shadow-sm'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`
                }
              >
                <span className="mr-3 text-slate-400 group-hover:text-white">{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="p-4 border-t border-slate-800 text-xs text-slate-400">
            <p className="font-semibold text-slate-300">Doc2Action Security Engine</p>
            <p className="mt-1 text-slate-400">OpenAPI RAG & Human-in-the-Loop Agent</p>
          </div>
        </aside>

        {/* Mobile Sidebar Overlay */}
        {mobileMenuOpen && (
          <div className="fixed inset-0 z-40 lg:hidden flex">
            <div
              className="fixed inset-0 bg-slate-900/80 backdrop-blur-sm"
              onClick={() => setMobileMenuOpen(false)}
            />
            <div className="relative flex-1 flex flex-col max-w-xs w-full bg-slate-900 border-r border-slate-800 pt-5 pb-4">
              <div className="px-4 flex items-center justify-between">
                <span className="text-lg font-bold text-white">Doc2Action Menu</span>
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-1 rounded-md text-slate-400 hover:text-white"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
              <nav className="mt-5 flex-1 px-2 space-y-1">
                {navItems.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center px-3 py-2.5 text-sm font-medium rounded-lg ${
                        isActive
                          ? 'bg-sky-600 text-white'
                          : 'text-slate-300 hover:bg-slate-800'
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
