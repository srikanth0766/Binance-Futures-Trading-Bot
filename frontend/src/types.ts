export type OrderSide = 'BUY' | 'SELL';
export type OrderType = 'MARKET' | 'LIMIT';

export interface OrderRequest {
    symbol: string;
    side: OrderSide;
    order_type: OrderType;
    quantity: number;
    price?: number;
}

export interface LogEntry {
    id: string;
    timestamp: string;
    level: 'info' | 'success' | 'error';
    message: string;
    data?: any;
}
