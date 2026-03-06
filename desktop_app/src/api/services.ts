import client from './client';

// ==================== 类型定义 ====================

export interface OfferPayload {
    sdp: string | undefined;
    type: string | undefined;
}

export interface OfferResponse {
    sdp: string;
    type: RTCSdpType;
    sessionid: string;
}

export interface MessagePayload {
    text: string;
    type: 'echo' | 'chat';
    interrupt?: boolean;
    sessionid: number;
}

export interface SpeakingStatus {
    code: number;
    data: boolean;
}

export interface TTSConfig {
    tts_type: 'edge' | 'doubao' | 'tencent' | 'azure';
    voice_id?: string;
    speed?: number;
    volume?: number;
}

export interface ASRConfig {
    asr_type: 'lip' | 'tencent' | 'funasr';
    language?: string;
}

export interface LLMConfig {
    model: string;
    temperature?: number;
    max_tokens?: number;
    stream?: boolean;
}

// ==================== WebRTC API ====================

export const negotiateOffer = async (payload: OfferPayload): Promise<OfferResponse> => {
    const response = await client.post<OfferResponse>('/offer', payload);
    return response.data;
};

export const sendHumanMessage = async (
    text: string,
    sessionId: string,
    options: {
        type?: 'echo' | 'chat';
        interrupt?: boolean;
    } = {}
) => {
    const { type = 'chat', interrupt = true } = options;
    return client.post('/human', {
        text,
        type,
        interrupt,
        sessionid: parseInt(sessionId),
    });
};

export const isSpeaking = async (sessionId: string): Promise<SpeakingStatus> => {
    const response = await client.post('/is_speaking', {
        sessionid: parseInt(sessionId),
    });
    return response.data;
};

export const interruptTalk = async (sessionId: string) => {
    return client.post('/interrupt_talk', {
        sessionid: parseInt(sessionId),
    });
};

// ==================== TTS API ====================
// 注意：以下 API 后端暂未实现，使用浏览器内置功能
// 可以在前端直接使用 useTTS hook

export const synthesizeSpeech = async (_text: string, _config: TTSConfig) => {
    // TODO: 等待后端实现 TTS API
    console.warn('TTS API not implemented on backend, using browser TTS instead');
    throw new Error('TTS API not implemented');
};

export const getTTSVoices = async (_ttsType: string) => {
    // TODO: 等待后端实现
    console.warn('getTTSVoices API not implemented');
    return [];
};

// ==================== ASR API ====================
// 注意：以下 API 后端暂未实现，使用浏览器内置功能
// 可以在前端直接使用 useASR hook

export const startASR = async (_config: ASRConfig, _sessionId: string) => {
    // TODO: 等待后端实现 ASR API
    console.warn('ASR API not implemented on backend, using browser ASR instead');
    throw new Error('ASR API not implemented');
};

export const stopASR = async (_sessionId: string) => {
    // TODO: 等待后端实现
    console.warn('stopASR API not implemented');
    return null;
};

export const getASRResult = async (_sessionId: string) => {
    // TODO: 等待后端实现
    console.warn('getASRResult API not implemented');
    return null;
};

// ==================== LLM API ====================
// 注意：LLM 对话通过 WebRTC 数据通道自动处理
// 以下 API 暂未实现

export const chatWithLLM = async (
    _message: string,
    _sessionId: string,
    _config: LLMConfig
) => {
    // TODO: 等待后端实现独立 LLM API
    console.warn('chatWithLLM API not implemented, use WebRTC data channel instead');
    throw new Error('LLM API not implemented');
};

// 流式 LLM 响应
export const chatWithLLMStream = async (
    _message: string,
    _sessionId: string,
    _config: LLMConfig,
    _onChunk: (chunk: string) => void,
    _onComplete: (fullText: string) => void,
    onError: (error: Error) => void
) => {
    // TODO: 等待后端实现流式 LLM API
    console.warn('chatWithLLMStream API not implemented, use WebRTC data channel instead');
    onError(new Error('LLM Stream API not implemented'));
};

// ==================== 配置 API ====================
// 注意：配置现在保存在前端 localStorage
// 以下 API 暂未实现

export const getServiceConfig = async () => {
    // TODO: 等待后端实现配置 API
    console.warn('getServiceConfig API not implemented, using localStorage instead');
    throw new Error('Config API not implemented');
};

export const updateServiceConfig = async (_config: {
    tts_type?: string;
    asr_type?: string;
    llm_model?: string;
    [key: string]: any;
}) => {
    // TODO: 等待后端实现配置 API
    console.warn('updateServiceConfig API not implemented, use localStorage instead');
    throw new Error('Config API not implemented');
};

// ==================== 健康检查 ====================

export const healthCheck = async () => {
    const response = await client.get('/health');
    return response.data;
};
