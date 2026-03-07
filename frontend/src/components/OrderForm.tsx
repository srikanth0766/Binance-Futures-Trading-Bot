import React, { useState } from 'react';
import type { OrderSide, OrderType, OrderRequest } from '../types';
import { Activity, DollarSign, Layers } from 'lucide-react';

interface OrderFormProps {
    onSubmit: (order: OrderRequest) => Promise<void>;
    isLoading: boolean;
}

export const OrderForm: React.FC<OrderFormProps> = ({ onSubmit, isLoading }) => {
    const [symbol, setSymbol] = useState('BTCUSDT');
    const [side, setSide] = useState<OrderSide>('BUY');
    const [orderType, setOrderType] = useState<OrderType>('MARKET');
    const [quantity, setQuantity] = useState('0.01');
    const [price, setPrice] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        const req: OrderRequest = {
            symbol: symbol.toUpperCase(),
            side,
            order_type: orderType,
            quantity: parseFloat(quantity),
        };

        if (orderType === 'LIMIT' && price) {
            req.price = parseFloat(price);
        }

        await onSubmit(req);
    };

    return (
        <div className="glass-panel">
            <h2 className="panel-title">
                <Activity size={20} className="text-accent" />
                Place Order (Testnet)
            </h2>

            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label className="form-label">Order Side</label>
                    <div className="segmented-control">
                        <input
                            type="radio"
                            id="side-buy"
                            name="side"
                            className="segment-input"
                            value="BUY"
                            checked={side === 'BUY'}
                            onChange={() => setSide('BUY')}
                        />
                        <label htmlFor="side-buy" className="segment-label">BUY</label>

                        <input
                            type="radio"
                            id="side-sell"
                            name="side"
                            className="segment-input"
                            value="SELL"
                            checked={side === 'SELL'}
                            onChange={() => setSide('SELL')}
                        />
                        <label htmlFor="side-sell" className="segment-label">SELL</label>
                    </div>
                </div>

                <div className="form-group">
                    <label className="form-label">Order Type</label>
                    <div className="segmented-control">
                        <input
                            type="radio"
                            id="type-market"
                            name="type"
                            className="segment-input"
                            value="MARKET"
                            checked={orderType === 'MARKET'}
                            onChange={() => setOrderType('MARKET')}
                        />
                        <label htmlFor="type-market" className="segment-label">MARKET</label>

                        <input
                            type="radio"
                            id="type-limit"
                            name="type"
                            className="segment-input"
                            value="LIMIT"
                            checked={orderType === 'LIMIT'}
                            onChange={() => setOrderType('LIMIT')}
                        />
                        <label htmlFor="type-limit" className="segment-label">LIMIT</label>
                    </div>
                </div>

                <div className="form-group">
                    <label className="form-label">Trading Pair Symbol</label>
                    <div className="relative">
                        <input
                            type="text"
                            className="form-input"
                            value={symbol}
                            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                            placeholder="e.g. BTCUSDT"
                            required
                        />
                    </div>
                </div>

                <div className="form-group">
                    <label className="form-label">
                        Quantity <span className="text-secondary">(Minimum Notional &gt; 100 USDT)</span>
                    </label>
                    <div className="relative">
                        <input
                            type="number"
                            className="form-input"
                            value={quantity}
                            onChange={(e) => setQuantity(e.target.value)}
                            step="0.001"
                            min="0.001"
                            required
                        />
                    </div>
                </div>

                {orderType === 'LIMIT' && (
                    <div className="form-group" style={{ animation: 'fadeIn 0.3s' }}>
                        <label className="form-label">Limit Price (USDT)</label>
                        <div className="relative">
                            <input
                                type="number"
                                className="form-input"
                                value={price}
                                onChange={(e) => setPrice(e.target.value)}
                                step="0.1"
                                placeholder="e.g. 50000"
                                required={orderType === 'LIMIT'}
                            />
                        </div>
                    </div>
                )}

                <button
                    type="submit"
                    className={`btn ${side === 'BUY' ? 'btn-buy' : 'btn-sell'} mt-4`}
                    disabled={isLoading || !symbol || !quantity || (orderType === 'LIMIT' && !price)}
                >
                    {isLoading ? (
                        <div className="spinner"></div>
                    ) : (
                        <>
                            {side === 'BUY' ? <Layers size={18} /> : <DollarSign size={18} />}
                            {side} {orderType}
                        </>
                    )}
                </button>
            </form>
        </div>
    );
};
