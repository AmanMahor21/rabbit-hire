import React from "react";
type State = { hasError: boolean; error?: Error };
export class ErrorBoundary extends React.Component<{ children: React.ReactNode }, State> {
  state: State = { hasError: false };
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error(error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-dvh items-center justify-center bg-[var(--color-bg)] p-6">
          <div className="max-w-md rounded-2xl border border-red-500/20 bg-red-500/5 p-6">
            <h2 className="text-lg font-semibold text-red-300">Something went wrong</h2>
            <p className="mt-2 text-sm text-red-200/70">{this.state.error?.message}</p>
            <button
              onClick={() => this.setState({ hasError: false, error: undefined })}
              className="mt-4 rounded-xl bg-white px-4 py-2 text-sm font-medium text-black"
            >
              Try again
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
