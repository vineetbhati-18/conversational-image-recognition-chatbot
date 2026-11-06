import React from 'react';
import { AlertTriangle, RefreshCw, Terminal } from 'lucide-react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null, showDetails: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error('ErrorBoundary caught an unhandled exception:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null, showDetails: false });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen w-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6 select-none font-sans">
          <div className="max-w-lg w-full bg-slate-900 border border-red-500/30 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-500 to-amber-500" />
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-slate-100">Application Rendering Exception</h1>
                <p className="text-xs text-slate-400">BEL Reconnaissance Interface encountered an unexpected state</p>
              </div>
            </div>

            <p className="text-sm text-slate-300 mb-6 leading-relaxed">
              The interface intercepted a runtime fault. Your data integrity and local session parameters remain secure.
            </p>

            <div className="space-y-3 mb-6">
              <button
                type="button"
                onClick={() => this.setState((prev) => ({ showDetails: !prev.showDetails }))}
                className="flex items-center space-x-2 text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
              >
                <Terminal className="w-3.5 h-3.5" />
                <span>{this.state.showDetails ? 'Hide Diagnostic Trace' : 'View Diagnostic Trace'}</span>
              </button>

              {this.state.showDetails && (
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-red-300 overflow-x-auto max-h-48">
                  <p className="font-semibold">{this.state.error?.toString()}</p>
                  <pre className="mt-2 text-[10px] text-slate-500 whitespace-pre-wrap">
                    {this.state.errorInfo?.componentStack}
                  </pre>
                </div>
              )}
            </div>

            <div className="flex items-center justify-end space-x-3">
              <button
                type="button"
                onClick={this.handleReset}
                className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow transition-all duration-150"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Reload Application</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
