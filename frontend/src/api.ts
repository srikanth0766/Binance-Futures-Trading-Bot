import type { OrderRequest } from './types';

const API_BASE_URL = 'http://localhost:8000/api';

export const submitOrder = async (orderReq: OrderRequest) => {
    try {
        const response = await fetch(`${API_BASE_URL}/order`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ...orderReq,
                symbol: orderReq.symbol.toUpperCase()
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Unknown error occurred');
        }

        return data;
    } catch (error: any) {
        throw new Error(error.message || 'Network error connecting to the API');
    }
};
