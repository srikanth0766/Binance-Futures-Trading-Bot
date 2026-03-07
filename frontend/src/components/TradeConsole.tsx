import React, { useEffect, useRef } from 'react';
import type { LogEntry } from '../types';
import { Terminal } from 'lucide-react';

interface TradeConsoleProps {
    logs: LogEntry[];
}

export const TradeConsole: React.FC<TradeConsoleProps> = ({ logs }) => {
    const consoleEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when new logs arrive
    useEffect(() => {
        consoleEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    return (
        <div className="glass-panel console-container">
            <h2 className="panel-title">
                <Terminal size={20} className="text-accent" />
                Execution Log
            </h2>

            <div className="console-output">
                {logs.length === 0 ? (
                    <div className="text-center mt-4 opacity-50">Waiting for events...</div>
                ) : (
                    logs.map((log) => (
                        <div key={log.id} className={`log-entry ${log.level}`}>
                            <span className="log-timestamp">[{log.timestamp}]</span>
                            {log.message}
                        </div>
                    ))
                )}
                <div ref={consoleEndRef} />
            </div>
        </div>
    );
};
