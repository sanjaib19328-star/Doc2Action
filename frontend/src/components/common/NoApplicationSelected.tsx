import React from 'react';
import { Link } from 'react-router-dom';
import { Layers, Plus } from 'lucide-react';

interface NoApplicationSelectedProps {
  moduleName?: string;
}

export const NoApplicationSelected: React.FC<NoApplicationSelectedProps> = ({ moduleName = 'this module' }) => {
  return (
    <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-8 sm:p-12 text-center shadow-xs max-w-2xl mx-auto my-8 font-sans">
      <div className="w-14 h-14 bg-amber-50 rounded-2xl flex items-center justify-center mx-auto text-amber-600 mb-4 border border-amber-200">
        <Layers className="w-7 h-7" />
      </div>
      <h2 className="text-xl font-black text-slate-900 tracking-tight">No Application Selected</h2>
      <p className="text-xs text-slate-500 mt-2 max-w-md mx-auto leading-relaxed">
        To access {moduleName}, you must select an existing application or create a new one. All specifications, catalog connections, and execution logs are isolated per application.
      </p>
      <div className="flex items-center justify-center space-x-3 mt-6">
        <Link
          to="/applications"
          className="inline-flex items-center px-4 py-2.5 text-xs font-semibold text-white bg-sky-600 hover:bg-sky-500 rounded-xl shadow-xs transition-colors space-x-1.5"
        >
          <Plus className="w-4 h-4" />
          <span>Select or Create Application</span>
        </Link>
      </div>
    </div>
  );
};
