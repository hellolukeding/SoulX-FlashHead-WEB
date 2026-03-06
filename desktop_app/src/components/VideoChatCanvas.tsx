import {
    AudioMutedOutlined,
    AudioOutlined,
    LeftOutlined,
    MessageOutlined,
    PhoneOutlined,
    SettingOutlined,
    SoundOutlined
} from '@ant-design/icons';
import { message } from 'antd';
import { useEffect, useRef, useState } from 'react';
import ChatSidebar, { ChatMessage } from './ChatSidebar';
import Settings from './Settings';

interface WebSocketMessage {
    type: string;
    data?: any;
    message?: string;
}

export default function VideoChat() {
    const [isStarted, setIsStarted] = useState(false);
    const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
    const [isChatOpen, setIsChatOpen] = useState(false);
    const [callDuration, setCallDuration] = useState(0);
    const [isLoading, setIsLoading] = useState(false);
    const [isInitialized, setIsInitialized] = useState(false);

    const canvasRef = useRef<HTMLCanvasElement>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const durationRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const videoFrameRef = useRef<HTMLImageElement | null>(null);

    const [isVoiceChatOn, setIsVoiceChatOn] = useState(false);
    const [isSpeakerOn, setIsSpeakerOn] = useState(true);
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [isAISpeaking, setIsAISpeaking] = useState(false);
    const isAISpeakingRef = useRef(false);
    const recognitionRef = useRef<any>(null);
    const aiSpeakingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const micPermissionStreamRef = useRef<MediaStream | null>(null);

    const [processingState, setProcessingState] = useState<{
        stage: 'idle' | 'thinking' | 'tts' | 'generating' | 'playing';
        progress: number;
        message: string;
    }>({
        stage: 'idle',
        progress: 0,
        message: ''
    });

    // 可配置的 WebSocket URL
    const [wsUrl, setWsUrl] = useState<string>('');

    useEffect(() => {
        const LOCAL_STORAGE_KEY = 'livetalking_config';
        try {
            const savedConfig = localStorage.getItem(LOCAL_STORAGE_KEY);
            if (savedConfig) {
                const config = JSON.parse(savedConfig);
                if (config.backend_url) {
                    setWsUrl(config.backend_url);
                }
            }
        } catch (e) {
            console.warn('Failed to load config:', e);
        }
    }, []);

    const WS_URL = wsUrl ? `${wsUrl}/api/v1/video` : `/api/v1/video`;

    useEffect(() => {
        isAISpeakingRef.current = isAISpeaking;
    }, [isAISpeaking]);

    const formatDuration = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    useEffect(() => {
        if (isStarted) {
            durationRef.current = setInterval(() => {
                setCallDuration(prev => prev + 1);
            }, 1000);
        } else {
            if (durationRef.current) {
                clearInterval(durationRef.current);
                durationRef.current = null;
            }
            setCallDuration(0);
        }
        return () => {
            if (durationRef.current) {
                clearInterval(durationRef.current);
            }
        };
    }, [isStarted]);

    const markAISpeaking = () => {
        setIsAISpeaking(true);
        if (aiSpeakingTimeoutRef.current) {
            clearTimeout(aiSpeakingTimeoutRef.current);
        }
        aiSpeakingTimeoutRef.current = setTimeout(() => {
            setIsAISpeaking(false);
        }, 500);
    };

    // 在 Canvas 上绘制帧
    const drawFrame = (base64Image: string) => {
        if (!canvasRef.current) return;
        
        const ctx = canvasRef.current.getContext('2d');
        if (!ctx) return;

        const img = new Image();
        img.onload = () => {
            // 清空画布
            ctx.clearRect(0, 0, canvasRef.current!.width, canvasRef.current!.height);
            // 绘制帧
            ctx.drawImage(img, 0, 0, canvasRef.current!.width, canvasRef.current!.height);
        };
        img.src = `data:image/jpeg;base64,${base64Image}`;
    };

    const connectWebSocket = () => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            return;
        }

        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log('[WS] Connected to', WS_URL);
            message.success('WebSocket 连接成功');

            ws.send(JSON.stringify({
                type: 'init',
                data: { reference_image: 'default' }
            }));
        };

        ws.onmessage = (event) => {
            try {
                const msg: WebSocketMessage = JSON.parse(event.data);
                console.log('[WS] Message received:', msg.type);

                switch (msg.type) {
                    case 'connected':
                        if (msg.message) message.info(msg.message);
                        break;

                    case 'initialized':
                        setIsInitialized(true);
                        setIsStarted(true);
                        setIsLoading(false);
                        message.success('✅ 会话初始化成功！');
                        break;

                    case 'status':
                        if (msg.data?.stage) {
                            setProcessingState({
                                stage: msg.data.stage,
                                progress: msg.data.progress || 0,
                                message: msg.data.message || ''
                            });
                        }
                        break;

                    case 'ai_text_chunk':
                        if (msg.data?.text) {
                            markAISpeaking();
                            setChatHistory(prev => {
                                const lastMsg = prev[prev.length - 1];
                                if (lastMsg && lastMsg.role === 'assistant') {
                                    return [
                                        ...prev.slice(0, -1),
                                        { ...lastMsg, content: lastMsg.content + msg.data.text }
                                    ];
                                } else {
                                    return [...prev, {
                                        role: 'assistant' as const,
                                        content: msg.data.text,
                                        timestamp: Date.now()
                                    }];
                                }
                            });
                        }
                        break;

                    case 'ai_audio':
                        if (msg.data?.audio_data) {
                            playAudio(msg.data.audio_data);
                        }
                        break;

                    case 'video_frame':
                        if (msg.data?.frame_data) {
                            // JPEG 帧数据
                            drawFrame(msg.data.frame_data);
                        } else if (msg.data?.video_data) {
                            // H.264 数据（暂不支持）
                            console.warn('[Video] H.264 format not supported in Canvas mode');
                        }
                        break;

                    case 'complete':
                        setTimeout(() => {
                            setProcessingState({ stage: 'idle', progress: 0, message: '' });
                        }, 2000);
                        break;

                    case 'error':
                        console.error('[WS] Error:', msg.message);
                        message.error('错误: ' + (msg.message || '未知错误'));
                        break;
                }
            } catch (e) {
                console.error('[WS] Failed to parse message:', e);
            }
        };

        ws.onerror = () => {
            console.error('[WS] Error');
            message.error('WebSocket 连接错误');
        };

        ws.onclose = () => {
            console.log('[WS] Connection closed');
            setIsStarted(false);
            setIsInitialized(false);
            setIsLoading(false);
        };
    };

    const playAudio = (base64Audio: string) => {
        try {
            const audioData = base64ToArrayBuffer(base64Audio);
            const audioBlob = new Blob([audioData], { type: 'audio/wav' });
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            audio.play();
            audio.onended = () => URL.revokeObjectURL(audioUrl);
        } catch (e) {
            console.error('[Audio] Failed to play audio:', e);
        }
    };

    const base64ToArrayBuffer = (base64: string): ArrayBuffer => {
        const binaryString = window.atob(base64);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return bytes.buffer;
    };

    const start = async () => {
        if (isStarted || isLoading) return;
        setIsLoading(true);
        try {
            connectWebSocket();
        } catch (e) {
            console.error('[Start] Failed to start:', e);
            message.error('启动失败: ' + e);
            setIsLoading(false);
        }
    };

    const stop = () => {
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        setIsStarted(false);
        setIsInitialized(false);
    };

    const handleSendMessage = async (text: string) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
            message.error('WebSocket 未连接');
            return;
        }
        if (!isInitialized) {
            message.error('会话未初始化');
            return;
        }

        setChatHistory(prev => [...prev, {
            role: 'user',
            content: text,
            timestamp: Date.now()
        }]);

        setProcessingState({ stage: 'thinking', progress: 10, message: '正在处理...' });

        try {
            wsRef.current.send(JSON.stringify({
                type: 'message',
                data: { text }
            }));
        } catch (e) {
            console.error('[WS] Failed to send message:', e);
            message.error('发送失败');
        }
    };

    const toggleSpeaker = () => {
        setIsSpeakerOn(!isSpeakerOn);
    };

    // 语音识别逻辑省略，与原版相同
    useEffect(() => {
        if (isVoiceChatOn && isStarted) {
            const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
            if (!SpeechRecognition) {
                message.error('浏览器不支持语音识别');
                setIsVoiceChatOn(false);
                return;
            }

            navigator.mediaDevices.getUserMedia({ audio: true })
                .then((stream) => {
                    micPermissionStreamRef.current = stream;
                    stream.getTracks().forEach(track => track.stop());
                    
                    const recognition = new SpeechRecognition();
                    recognition.continuous = true;
                    recognition.interimResults = false;
                    recognition.lang = 'zh-CN';
                    
                    recognition.onresult = (event: any) => {
                        if (isAISpeakingRef.current) return;
                        const last = event.results.length - 1;
                        const text = event.results[last][0].transcript;
                        if (text && text.trim()) {
                            handleSendMessage(text.trim());
                        }
                    };
                    
                    recognition.onerror = () => setIsVoiceChatOn(false);
                    recognition.onend = () => {
                        if (isVoiceChatOn && isStarted) {
                            try { recognition.start(); } catch(e) {}
                        }
                    };
                    
                    try { recognition.start(); recognitionRef.current = recognition; }
                    catch(e) { message.error('无法开启语音识别'); setIsVoiceChatOn(false); }
                })
                .catch(() => {
                    message.error('麦克风权限被拒绝');
                    setIsVoiceChatOn(false);
                });
        } else {
            if (recognitionRef.current) {
                recognitionRef.current.stop();
                recognitionRef.current = null;
            }
        }

        return () => {
            if (recognitionRef.current) recognitionRef.current.stop();
            if (micPermissionStreamRef.current) {
                micPermissionStreamRef.current.getTracks().forEach(track => track.stop());
            }
        };
    }, [isVoiceChatOn, isStarted]);

    useEffect(() => {
        return () => {
            stop();
            if (aiSpeakingTimeoutRef.current) clearTimeout(aiSpeakingTimeoutRef.current);
        };
    }, []);

    return (
        <div className="relative w-full h-full bg-[#ededed] overflow-hidden">
            {/* 顶部状态 */}
            {isStarted && (
                <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 flex items-center gap-3">
                    <span className="text-gray-600 text-sm">{formatDuration(callDuration)}</span>
                    {isAISpeaking && (
                        <span className="px-2 py-1 bg-green-500 text-white text-xs rounded-full animate-pulse">
                            AI 正在说话
                        </span>
                    )}
                </div>
            )}

            {/* 主视频区域 - Canvas */}
            <div className="absolute inset-0 z-0">
                {isStarted && processingState.stage !== 'idle' && processingState.stage !== 'playing' && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30 z-10">
                        <div className="text-center text-white">
                            <div className="text-xl mb-2">{processingState.message || '正在处理中...'}</div>
                            <div className="w-64 mx-auto bg-white bg-opacity-30 rounded-full h-2">
                                <div className="h-full bg-green-500 transition-all" style={{ width: `${processingState.progress}%` }}></div>
                            </div>
                        </div>
                    </div>
                )}

                {!isStarted && !isLoading && (
                    <div className="absolute inset-0 flex items-center justify-center bg-[#ededed] z-10">
                        <div className="text-center">
                            <div className="w-32 h-32 mx-auto mb-6 rounded-full bg-gray-300 flex items-center justify-center">
                                <span className="text-6xl">🤖</span>
                            </div>
                            <div className="text-xl text-gray-700 mb-2">AI 数字人助手</div>
                            <div className="text-gray-500 text-sm">Canvas 渲染模式</div>
                        </div>
                    </div>
                )}

                {isLoading && !isStarted && (
                    <div className="absolute inset-0 flex items-center justify-center bg-[#ededed] z-10">
                        <div className="text-center">
                            <div className="w-32 h-32 mx-auto mb-6 rounded-full border-4 border-t-green-500 border-r-transparent border-b-transparent border-l-transparent animate-spin flex items-center justify-center">
                                <span className="text-5xl">🤖</span>
                            </div>
                            <div className="text-xl text-gray-700">正在连接中...</div>
                        </div>
                    </div>
                )}

                {/* Canvas 用于绘制视频帧 */}
                <canvas
                    ref={canvasRef}
                    width={512}
                    height={512}
                    className="w-full h-full object-contain bg-black"
                    style={{ display: isStarted ? 'block' : 'none' }}
                />
            </div>

            {/* 底部控制区 - 与原版相同 */}
            <div className="absolute bottom-0 left-0 right-0 z-20 pb-8">
                <div className="flex items-center justify-center gap-8 mb-6">
                    <div className="flex flex-col items-center gap-2">
                        <button onClick={() => isStarted && setIsVoiceChatOn(!isVoiceChatOn)}
                            style={{ width: 56, height: 56, borderRadius: '50%', backgroundColor: '#fff', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: isStarted ? 1 : 0.5 }}>
                            {isVoiceChatOn ? <AudioOutlined style={{ fontSize: 22 }} /> : <AudioMutedOutlined style={{ fontSize: 22 }} />}
                        </button>
                        <span className="text-gray-600 text-xs">{isVoiceChatOn ? '麦克风已开' : '麦克风已关'}</span>
                    </div>

                    <div className="flex flex-col items-center gap-2">
                        <button onClick={toggleSpeaker}
                            style={{ width: 56, height: 56, borderRadius: '50%', backgroundColor: '#fff', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: isStarted ? 1 : 0.5 }}>
                            <SoundOutlined style={{ fontSize: 22 }} />
                        </button>
                        <span className="text-gray-600 text-xs">{isSpeakerOn ? '扬声器已开' : '扬声器已关'}</span>
                    </div>

                    <div className="flex flex-col items-center gap-2">
                        <button onClick={() => setIsChatOpen(!isChatOpen)}
                            style={{ width: 56, height: 56, borderRadius: '50%', backgroundColor: '#fff', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <MessageOutlined style={{ fontSize: 22 }} />
                        </button>
                        <span className="text-gray-600 text-xs">消息</span>
                    </div>

                    <div className="flex flex-col items-center gap-2">
                        <button onClick={() => setIsSettingsOpen(!isSettingsOpen)}
                            style={{ width: 56, height: 56, borderRadius: '50%', backgroundColor: '#fff', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <SettingOutlined style={{ fontSize: 22 }} />
                        </button>
                        <span className="text-gray-600 text-xs">设置</span>
                    </div>
                </div>

                <div className="flex justify-center">
                    {isStarted ? (
                        <button onClick={stop}
                            style={{ width: 64, height: 64, borderRadius: '50%', backgroundColor: '#fa5151', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <PhoneOutlined style={{ fontSize: 28, color: '#fff', transform: 'rotate(135deg)' }} />
                        </button>
                    ) : (
                        <button onClick={start} disabled={isLoading}
                            style={{ width: 64, height: 64, borderRadius: '50%', backgroundColor: isLoading ? '#8fdcb8' : '#07c160', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: isLoading ? 0.7 : 1 }}>
                            {isLoading ? <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <PhoneOutlined style={{ fontSize: 28, color: '#fff' }} />}
                        </button>
                    )}
                </div>
            </div>

            {/* 聊天侧边栏 */}
            <div className={`absolute top-0 right-0 h-full z-30 transition-transform duration-300 ${isChatOpen ? 'translate-x-0' : 'translate-x-full'}`}>
                <div className="relative h-full">
                    <button onClick={() => setIsChatOpen(false)}
                        className="absolute left-0 top-1/2 -translate-x-full -translate-y-1/2 w-6 h-16 bg-white rounded-l-lg flex items-center justify-center shadow-lg">
                        <LeftOutlined className="text-gray-600" style={{ transform: 'rotate(180deg)' }} />
                    </button>
                    <ChatSidebar chatHistory={chatHistory} onSendMessage={handleSendMessage} />
                </div>
            </div>

            <Settings visible={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
        </div>
    );
}
