import client from './client';

export interface OfferPayload {
    sdp: string | undefined;
    type: string | undefined;
}

export interface OfferResponse {
    sdp: string;
    type: RTCSdpType;
    sessionid: string;
}

export const negotiateOffer = async (payload: OfferPayload): Promise<OfferResponse> => {
    const response = await client.post<OfferResponse>('/offer', payload);
    return response.data;
};

export const sendHumanMessage = async (text: string, sessionId: string, interrupt: boolean = true) => {
    return client.post('/human', {
        text,
        type: 'chat',
        interrupt,
        sessionid: parseInt(sessionId),
    });
};

export const isSpeaking = async (sessionId: string) => {
    const response = await client.post('/is_speaking', {
        sessionid: parseInt(sessionId),
    });
    return response.data;
};
