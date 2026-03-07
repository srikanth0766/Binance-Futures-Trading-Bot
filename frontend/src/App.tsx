import { useState } from 'react';
import './App.css';
import { OrderForm } from './components/OrderForm';
import { TradeConsole } from './components/TradeConsole';
import type { OrderRequest, LogEntry } from './types';
import { submitOrder } from './api';
import { Activity } from 'lucide-react';

function App() {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    const addLog = (level: LogEntry['level'], message: string, data?: any) => {
        const newLog: LogEntry = {
            id: crypto.randomUUID(),
            timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }),
            level,
            message,
            data
        };
        setLogs(prev => [...prev, newLog]);
    };

    const handleOrderSubmit = async (orderReq: OrderRequest) => {
        setIsLoading(true);
        addLog('info', `Submitting ${orderReq.side} ${orderReq.order_type} for ${orderReq.quantity} ${orderReq.symbol}...`);

        try {
            const result = await submitOrder(orderReq);
            const d = result.data;
            const summary = [
                `✓ Order #${d.orderId} accepted`,
                `${d.side} ${d.origQty} ${d.symbol} @ ${d.type}`,
                `Status: ${d.status}${d.avgPrice && d.avgPrice !== '0.00' ? ` · Avg Price: $${d.avgPrice}` : ''}`,
            ].join('  ·  ');
            addLog('success', summary);
        } catch (error: any) {
            addLog(
                'error',
                `API rejected order: ${error.message}`
            );
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="app-container" style={{ animation: 'fadeIn 0.5s ease-out' }}>
            <header>
                <div className="logo">
                    <Activity color="#58a6ff" size={28} />
                    Binance Testnet Swarm
                </div>

            </header>

            <main className="main-content">
                <div className="form-section">
                    <OrderForm onSubmit={handleOrderSubmit} isLoading={isLoading} />
                </div>

                <div className="console-section" style={{ height: 'calc(100vh - 150px)', minHeight: '500px' }}>
                    <TradeConsole logs={logs} />
                </div>
            </main>
        </div>
    );
}

export default App;
