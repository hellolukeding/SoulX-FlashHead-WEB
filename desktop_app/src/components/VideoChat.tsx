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
    session_id?: string;
}

export default function VideoChat() {
    const [isStarted, setIsStarted] = useState(false);
    const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
    const [isChatOpen, setIsChatOpen] = useState(false);
    const [callDuration, setCallDuration] = useState(0);
    const [isLoading, setIsLoading] = useState(false);
    const [isInitialized, setIsInitialized] = useState(false);

    const videoRef = useRef<HTMLVideoElement>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const durationRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const [isVoiceChatOn, setIsVoiceChatOn] = useState(false);
    const [isSpeakerOn, setIsSpeakerOn] = useState(true);
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [isAISpeaking, setIsAISpeaking] = useState(false);
    const isAISpeakingRef = useRef(false);
    const recognitionRef = useRef<any>(null);
    const aiSpeakingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const micPermissionStreamRef = useRef<MediaStream | null>(null);

    // Processing state for better feedback - 阶段2新增
    const [processingState, setProcessingState] = useState<{
        stage: 'idle' | 'thinking' | 'tts' | 'generating' | 'playing';
        progress: number;
        message: string;
    }>({
        stage: 'idle',
        progress: 0,
        message: ''
    });

    // MSE MediaSource
    const mediaSourceRef = useRef<MediaSource | null>(null);
    const sourceBufferRef = useRef<SourceBuffer | null>(null);
    const queueRef = useRef<Uint8Array[]>([]);

    // WebSocket URL (可配置)
    const [wsUrl, setWsUrl] = useState<string>('');  // 空值表示使用代理
    const [debugMode, setDebugMode] = useState<boolean>(false);

    // Load configuration from localStorage
    useEffect(() => {
        const LOCAL_STORAGE_KEY = 'livetalking_config';
        try {
            const savedConfig = localStorage.getItem(LOCAL_STORAGE_KEY);
            if (savedConfig) {
                const config = JSON.parse(savedConfig);
                if (config.backend_url) {
                    setWsUrl(config.backend_url);
                }
                if (config.debug_mode !== undefined) {
                    setDebugMode(config.debug_mode);
                }
            }
        } catch (e) {
            console.warn('Failed to load config:', e);
        }
    }, []);

    // Construct WebSocket URL (使用代理路径)
    // 如果 wsUrl 为空，使用代理路径（开发模式）
    // 否则使用完整 URL（生产模式）
    const WS_URL = wsUrl ? `${wsUrl}/api/v1/video` : `/api/v1/video`;

    // 同步 isAISpeaking 状态到 ref
    useEffect(() => {
        isAISpeakingRef.current = isAISpeaking;
    }, [isAISpeaking]);

    // 格式化通话时长
    const formatDuration = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    // 通话时长计时器
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

    // 标记 AI 开始说话
    const markAISpeaking = () => {
        setIsAISpeaking(true);

        if (aiSpeakingTimeoutRef.current) {
            clearTimeout(aiSpeakingTimeoutRef.current);
        }

        aiSpeakingTimeoutRef.current = setTimeout(() => {
            console.log('[AEC] AI stopped speaking (no new messages for 500ms)');
            setIsAISpeaking(false);
        }, 500);
    };

    // 初始化 MediaSource
    const initMediaSource = () => {
        if ('MediaSource' in window && videoRef.current) {
            const mediaSource = new MediaSource();
            mediaSourceRef.current = mediaSource;
            videoRef.current.src = URL.createObjectURL(mediaSource);

            mediaSource.addEventListener('sourceopen', () => {
                console.log('[MSE] MediaSource opened');
                try {
                    const mimeCodec = 'video/mp4; codecs="avc1.42E01E, mp4a.40.2"';
                    const sourceBuffer = mediaSource.addSourceBuffer(mimeCodec);
                    sourceBufferRef.current = sourceBuffer;

                    sourceBuffer.addEventListener('updateend', () => {
                        // 处理队列中的下一个数据
                        if (queueRef.current.length > 0 && !sourceBuffer.updating) {
                            try {
                                const data = queueRef.current.shift();
                                if (data) {
                                    sourceBuffer.appendBuffer(data);
                                }
                            } catch (e) {
                                console.error('[MSE] Error appending buffer from queue:', e);
                            }
                        }
                    });

                    console.log('[MSE] SourceBuffer created:', mimeCodec);

                    // 自动播放视频
                    if (videoRef.current) {
                        videoRef.current.play().catch(e => {
                            console.warn('[MSE] Auto-play failed:', e);
                        });
                    }
                } catch (e) {
                    console.error('[MSE] Failed to create SourceBuffer:', e);
                    message.error('视频播放器初始化失败');
                }
            });

            mediaSource.addEventListener('sourceended', () => {
                console.log('[MSE] MediaSource ended');
            });

            console.log('[MSE] MediaSource initialized');
        } else {
            console.error('[MSE] MediaSource not supported');
            message.error('浏览器不支持 MediaSource API');
        }
    };

    // 连接 WebSocket
    const connectWebSocket = () => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            console.log('[WS] Already connected');
            return;
        }

        console.log('[WS] Connecting to', WS_URL);
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log('[WS] Connected to', WS_URL);
            if (debugMode) console.log('[WS] Debug mode enabled');
            message.success('WebSocket 连接成功');

            // 自动初始化会话
            console.log('[WS] Initializing session...');
            ws.send(JSON.stringify({
                type: 'init',
                data: {
                    reference_image: 'default'
                }
            }));
        };

        ws.onmessage = (event) => {
            try {
                const msg: WebSocketMessage = JSON.parse(event.data);
                console.log('[WS] Message received:', msg.type);

                switch (msg.type) {
                    case 'connected':
                        console.log('[WS] Session ID:', msg.session_id);
                        if (msg.message) {
                            message.info(msg.message);
                        }
                        break;

                    case 'initialized':
                        setIsInitialized(true);
                        setIsStarted(true);
                        setIsLoading(false);
                        message.success('✅ 会话初始化成功！现在可以发送消息了');
                        break;

                    case 'status':
                        // Processing status updates - 阶段2新增
                        if (msg.data?.stage) {
                            setProcessingState({
                                stage: msg.data.stage,
                                progress: msg.data.progress || 0,
                                message: msg.data.message || ''
                            });
                        }
                        break;

                    case 'ai_text_chunk':
                        // AI 文本回复
                        if (msg.data?.text) {
                            setProcessingState({
                                stage: 'playing',
                                progress: 100,
                                message: '正在回复...'
                            });

                            markAISpeaking();

                            setChatHistory(prev => {
                                const lastMsg = prev[prev.length - 1];
                                if (lastMsg && lastMsg.role === 'assistant') {
                                    const updated = [
                                        ...prev.slice(0, -1),
                                        { ...lastMsg, content: lastMsg.content + msg.data.text }
                                    ];
                                    return updated;
                                } else {
                                    const newMessage = {
                                        role: 'assistant' as const,
                                        content: msg.data.text,
                                        timestamp: Date.now()
                                    };
                                    return [...prev, newMessage];
                                }
                            });
                        }
                        break;

                    case 'ai_audio':
                        // TTS 音频
                        if (msg.data?.audio_data) {
                            console.log('[WS] Audio received:', msg.data.audio_format, msg.data.sample_rate, 'Hz');
                            setProcessingState({
                                stage: 'playing',
                                progress: 75,
                                message: '正在播放语音...'
                            });
                            playAudio(msg.data.audio_data);
                        }
                        break;

                    case 'video_frame':
                        // H.264 视频帧（传统模式）
                        if (msg.data?.video_data) {
                            console.log('[WS] Video frame received:', msg.data.video_frames, 'frames');
                            setProcessingState({
                                stage: 'playing',
                                progress: 90,
                                message: '正在显示视频...'
                            });
                            appendVideoData(msg.data.video_data);
                        }
                        break;

                    case 'video_chunk':
                        // H.264 视频片段（流式模式 - 阶段3优化）
                        if (msg.data?.video_data) {
                            const { chunk_index, total_chunks, video_frames, duration, is_first, is_last } = msg.data;
                            console.log(`[WS] Video chunk received: ${chunk_index + 1}/${total_chunks}, ${video_frames} frames, ${duration?.toFixed(2)}s`);

                            setProcessingState({
                                stage: 'playing',
                                progress: 60 + ((chunk_index + 1) / total_chunks) * 30,
                                message: `正在显示视频 ${chunk_index + 1}/${total_chunks}...`
                            });

                            appendVideoData(msg.data.video_data);

                            // 如果是最后一段，稍后重置状态
                            if (is_last) {
                                setTimeout(() => {
                                    setProcessingState({
                                        stage: 'idle',
                                        progress: 0,
                                        message: ''
                                    });
                                }, 2000);
                            }
                        }
                        break;

                    case 'complete':
                        if (msg.data?.success) {
                            console.log('[WS] Message processing complete');
                            // Reset processing state after a delay
                            setTimeout(() => {
                                setProcessingState({
                                    stage: 'idle',
                                    progress: 0,
                                    message: ''
                                });
                            }, 2000);
                        } else {
                            console.warn('[WS] Message processing completed with error:', msg.data?.message);
                            setProcessingState({
                                stage: 'idle',
                                progress: 0,
                                message: ''
                            });
                        }
                        break;

                    case 'error':
                        console.error('[WS] Error:', msg.message);
                        message.error('错误: ' + (msg.message || '未知错误'));
                        break;

                    default:
                        console.log('[WS] Unknown message type:', msg.type);
                }
            } catch (e) {
                console.error('[WS] Failed to parse message:', e);
            }
        };

        ws.onerror = (error) => {
            console.error('[WS] Error:', error);
            message.error('WebSocket 连接错误');
        };

        ws.onclose = () => {
            console.log('[WS] Connection closed');
            setIsStarted(false);
            setIsInitialized(false);
            setIsLoading(false);
        };
    };

    // 播放音频
    const playAudio = (base64Audio: string) => {
        try {
            const audioData = base64ToArrayBuffer(base64Audio);
            const audioBlob = new Blob([audioData], { type: 'audio/wav' });
            const audioUrl = URL.createObjectURL(audioBlob);

            const audio = new Audio(audioUrl);
            audio.play();

            console.log('[Audio] Playing audio...');

            audio.onended = () => {
                URL.revokeObjectURL(audioUrl);
                console.log('[Audio] Audio playback completed');
            };

            audio.onerror = (e) => {
                console.error('[Audio] Playback error:', e);
            };
        } catch (e) {
            console.error('[Audio] Failed to play audio:', e);
        }
    };

    // Base64 转 ArrayBuffer
    const base64ToArrayBuffer = (base64: string): ArrayBuffer => {
        const binaryString = window.atob(base64);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return bytes.buffer;
    };

    // 添加视频数据到 MSE
    const appendVideoData = (base64Video: string) => {
        if (!sourceBufferRef.current) {
            console.warn('[MSE] SourceBuffer not ready');
            return;
        }

        try {
            const videoData = base64ToArrayBuffer(base64Video);
            const data = new Uint8Array(videoData);

            if (!sourceBufferRef.current.updating) {
                sourceBufferRef.current.appendBuffer(data);
            } else {
                // 如果 SourceBuffer 忙碌，添加到队列
                queueRef.current.push(data);
                console.log('[MSE] Buffer busy, added to queue. Queue size:', queueRef.current.length);
            }
        } catch (e) {
            console.error('[MSE] Failed to append video data:', e);
        }
    };

    // 启动连接
    const start = async () => {
        if (isStarted || isLoading) return;

        setIsLoading(true);

        try {
            // 初始化 MediaSource
            initMediaSource();

            // 连接 WebSocket
            connectWebSocket();
        } catch (e) {
            console.error('[Start] Failed to start:', e);
            message.error('启动失败: ' + e);
            setIsLoading(false);
        }
    };

    // 停止连接
    const stop = () => {
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }

        // 关闭 MediaSource
        if (mediaSourceRef.current && mediaSourceRef.current.readyState === 'open') {
            try {
                mediaSourceRef.current.endOfStream();
            } catch (e) {
                console.error('[MSE] Failed to end stream:', e);
            }
        }

        setIsStarted(false);
        setIsInitialized(false);
    };

    // 发送文本消息
    const handleSendMessage = async (text: string) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
            message.error('WebSocket 未连接');
            return;
        }

        if (!isInitialized) {
            message.error('会话未初始化，请等待');
            return;
        }

        setChatHistory(prev => [...prev, {
            role: 'user',
            content: text,
            timestamp: Date.now()
        }]);

        // Show processing state - 阶段2新增
        setProcessingState({
            stage: 'thinking',
            progress: 10,
            message: '正在理解您的问题...'
        });

        try {
            wsRef.current.send(JSON.stringify({
                type: 'message',
                data: {
                    text: text,
                    streaming: true  // 启用流式视频生成（阶段3）
                }
            }));
            console.log('[WS] Message sent:', text);
        } catch (e) {
            console.error('[WS] Failed to send message:', e);
            message.error('发送失败');
            setProcessingState({
                stage: 'idle',
                progress: 0,
                message: ''
            });
        }
    };

    // 切换扬声器
    const toggleSpeaker = () => {
        setIsSpeakerOn(!isSpeakerOn);
        if (videoRef.current) {
            videoRef.current.muted = !isSpeakerOn;
        }
    };

    // 初始化语音识别
    useEffect(() => {
        if (isVoiceChatOn && isStarted) {
            const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
            if (!SpeechRecognition) {
                message.error('您的浏览器不支持语音识别');
                setIsVoiceChatOn(false);
                return;
            }

            message.loading({ content: '正在请求麦克风权限...', key: 'micPermission', duration: 0 });

            navigator.mediaDevices.enumerateDevices()
                .then((devices) => {
                    const audioInputs = devices.filter(device => device.kind === 'audioinput');
                    console.log('[ASR] Audio inputs:', audioInputs.length);

                    if (audioInputs.length === 0) {
                        message.error('未检测到麦克风设备');
                    }

                    return navigator.mediaDevices.getUserMedia({ audio: true });
                })
                .then((stream) => {
                    message.success({ content: '麦克风权限已授予', key: 'micPermission', duration: 2 });
                    micPermissionStreamRef.current = stream;
                    stream.getTracks().forEach(track => track.stop());
                    initSpeechRecognition();
                })
                .catch((err: any) => {
                    setIsVoiceChatOn(false);
                    if (err.name === 'NotAllowedError') {
                        message.error('麦克风权限被拒绝');
                    } else if (err.name === 'NotFoundError') {
                        message.error('未检测到麦克风设备');
                    } else {
                        message.error(`麦克风访问失败: ${err.message}`);
                    }
                    console.error('[ASR] Microphone permission denied:', err);
                });
        } else {
            if (recognitionRef.current) {
                recognitionRef.current.stop();
                recognitionRef.current = null;
            }
            if (micPermissionStreamRef.current) {
                micPermissionStreamRef.current.getTracks().forEach(track => track.stop());
                micPermissionStreamRef.current = null;
            }
        }

        return () => {
            if (recognitionRef.current) {
                recognitionRef.current.stop();
                recognitionRef.current = null;
            }
            if (micPermissionStreamRef.current) {
                micPermissionStreamRef.current.getTracks().forEach(track => track.stop());
                micPermissionStreamRef.current = null;
            }
        };
    }, [isVoiceChatOn, isStarted]);

    // 初始化语音识别
    const initSpeechRecognition = () => {
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = false;
        recognition.lang = 'zh-CN';

        recognition.onresult = (event: any) => {
            if (isAISpeakingRef.current) {
                console.log('[ASR] AI is speaking, ignoring input');
                return;
            }

            const last = event.results.length - 1;
            const text = event.results[last][0].transcript;
            if (text && text.trim()) {
                console.log('[ASR] Recognized:', text);
                handleSendMessage(text.trim());
            }
        };

        recognition.onerror = (event: any) => {
            console.error('[ASR] Speech recognition error:', event.error);
            if (event.error === 'not-allowed') {
                message.error('语音识别权限被拒绝');
                setIsVoiceChatOn(false);
            }
        };

        recognition.onend = () => {
            if (isVoiceChatOn && isStarted && recognitionRef.current) {
                try {
                    recognition.start();
                } catch (e) {
                    console.error('[ASR] Failed to restart recognition:', e);
                }
            }
        };

        try {
            recognition.start();
            recognitionRef.current = recognition;
            console.log('[ASR] Speech recognition started');
        } catch (e) {
            console.error('[ASR] Failed to start recognition:', e);
            message.error('无法开启语音识别');
            setIsVoiceChatOn(false);
        }
    };

    useEffect(() => {
        return () => {
            stop();
            if (aiSpeakingTimeoutRef.current) {
                clearTimeout(aiSpeakingTimeoutRef.current);
            }
        };
    }, []);

    return (
        <div className="relative w-full h-full bg-[#ededed] overflow-hidden">
            {/* 顶部通话时长和状态 */}
            {isStarted && (
                <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 flex items-center gap-3">
                    <span className="text-gray-600 text-sm">{formatDuration(callDuration)}</span>
                    {isAISpeaking && (
                        <span className="px-2 py-1 bg-green-500 text-white text-xs rounded-full animate-pulse">
                            AI 正在说话
                        </span>
                    )}
                    {isVoiceChatOn && !isAISpeaking && (
                        <span className="px-2 py-1 bg-blue-500 text-white text-xs rounded-full">
                            麦克风开启
                        </span>
                    )}
                </div>
            )}

            {/* 主视频区域 */}
            <div className="absolute inset-0 z-0">
                {/* Processing/Idle Animation Overlay - 阶段2新增 */}
                {isStarted && processingState.stage !== 'idle' && processingState.stage !== 'playing' && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30 z-10">
                        <div className="text-center">
                            {/* 呼吸动画圆环 */}
                            <div className="relative w-40 h-40 mx-auto mb-6">
                                <div className="absolute inset-0 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 opacity-20 animate-pulse"></div>
                                <div className="absolute inset-2 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 opacity-40 animate-ping" style={{ animationDuration: '2s' }}></div>

                                {/* 机器人头像 */}
                                <div className="absolute inset-4 rounded-full bg-white flex items-center justify-center shadow-lg">
                                    <span className="text-7xl">🤖</span>
                                </div>

                                {/* 思考点动画 */}
                                <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 flex gap-2">
                                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                                </div>
                            </div>

                            {/* 状态消息 */}
                            <div className="text-white text-xl mb-3 font-medium drop-shadow-lg">
                                {processingState.message || '正在处理中...'}
                            </div>

                            {/* 进度条 */}
                            <div className="w-64 mx-auto bg-white bg-opacity-30 rounded-full h-2 overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-blue-400 to-purple-500 transition-all duration-500 ease-out"
                                    style={{ width: `${processingState.progress}%` }}
                                ></div>
                            </div>

                            {/* 阶段指示器 */}
                            <div className="flex justify-center gap-4 mt-4 text-white text-sm">
                                <span className={processingState.stage === 'thinking' ? 'opacity-100 font-bold' : 'opacity-50'}>
                                    💭 思考
                                </span>
                                <span className={processingState.stage === 'tts' ? 'opacity-100 font-bold' : 'opacity-50'}>
                                    🔊 语音
                                </span>
                                <span className={processingState.stage === 'generating' ? 'opacity-100 font-bold' : 'opacity-50'}>
                                    🎬 视频
                                </span>
                            </div>
                        </div>
                    </div>
                )}

                {!isStarted && !isLoading && (
                    <div className="absolute inset-0 flex items-center justify-center bg-[#ededed] z-10">
                        <div className="text-center">
                            <div className="w-32 h-32 mx-auto mb-6 rounded-full bg-gray-300 flex items-center justify-center overflow-hidden">
                                <span className="text-6xl">🤖</span>
                            </div>
                            <div className="text-xl text-gray-700 mb-2">AI 数字人助手</div>
                            <div className="text-gray-500 text-sm">阶段3优化版 - 分段视频生成 + 音频优先</div>
                        </div>
                    </div>
                )}
                {isLoading && !isStarted && (
                    <div className="absolute inset-0 flex items-center justify-center bg-[#ededed] z-10">
                        <div className="text-center">
                            <div className="relative w-32 h-32 mx-auto mb-6">
                                <div className="absolute inset-0 rounded-full border-4 border-gray-200"></div>
                                <div className="absolute inset-0 rounded-full border-4 border-t-green-500 border-r-transparent border-b-transparent border-l-transparent animate-spin"></div>
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <span className="text-5xl">🤖</span>
                                </div>
                            </div>
                            <div className="text-xl text-gray-700 mb-2">正在连接中...</div>
                            <div className="text-gray-500 text-sm">请稍候，正在建立 WebSocket 连接</div>
                        </div>
                    </div>
                )}
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted={!isSpeakerOn}
                    className="w-full h-full object-cover"
                    style={{ display: isStarted ? 'block' : 'none' }}
                />
            </div>

            {/* 底部控制区域 */}
            <div className="absolute bottom-0 left-0 right-0 z-20 pb-8">
                {/* 功能按钮行 */}
                <div className="flex items-center justify-center gap-8 mb-6">
                    {/* 麦克风 */}
                    <div className="flex flex-col items-center gap-2">
                        <button
                            onClick={() => isStarted && setIsVoiceChatOn(!isVoiceChatOn)}
                            style={{
                                width: 56,
                                height: 56,
                                borderRadius: '50%',
                                backgroundColor: '#fff',
                                border: 'none',
                                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: 'pointer',
                                opacity: !isStarted ? 0.5 : 1
                            }}
                        >
                            {isVoiceChatOn ? (
                                <AudioOutlined style={{ fontSize: 22, color: '#000' }} />
                            ) : (
                                <AudioMutedOutlined style={{ fontSize: 22, color: '#000' }} />
                            )}
                        </button>
                        <span className="text-gray-600 text-xs">
                            {isVoiceChatOn ? '麦克风已开' : '麦克风已关'}
                        </span>
                    </div>

                    {/* 扬声器 */}
                    <div className="flex flex-col items-center gap-2">
                        <button
                            onClick={toggleSpeaker}
                            style={{
                                width: 56,
                                height: 56,
                                borderRadius: '50%',
                                backgroundColor: '#fff',
                                border: 'none',
                                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: 'pointer',
                                opacity: !isStarted ? 0.5 : 1
                            }}
                        >
                            <SoundOutlined style={{ fontSize: 22, color: '#000' }} />
                        </button>
                        <span className="text-gray-600 text-xs">
                            {isSpeakerOn ? '扬声器已开' : '扬声器已关'}
                        </span>
                    </div>

                    {/* 消息 */}
                    <div className="flex flex-col items-center gap-2">
                        <button
                            onClick={() => setIsChatOpen(!isChatOpen)}
                            style={{
                                width: 56,
                                height: 56,
                                borderRadius: '50%',
                                backgroundColor: '#fff',
                                border: 'none',
                                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: 'pointer'
                            }}
                        >
                            <MessageOutlined style={{ fontSize: 22, color: '#000' }} />
                        </button>
                        <span className="text-gray-600 text-xs">消息</span>
                    </div>

                    {/* 设置 */}
                    <div className="flex flex-col items-center gap-2">
                        <button
                            onClick={() => setIsSettingsOpen(!isSettingsOpen)}
                            style={{
                                width: 56,
                                height: 56,
                                borderRadius: '50%',
                                backgroundColor: '#fff',
                                border: 'none',
                                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: 'pointer'
                            }}
                        >
                            <SettingOutlined style={{ fontSize: 22, color: '#000' }} />
                        </button>
                        <span className="text-gray-600 text-xs">设置</span>
                    </div>
                </div>

                {/* 挂断/接听按钮 */}
                <div className="flex justify-center">
                    {isStarted ? (
                        <button
                            onClick={stop}
                            style={{
                                width: 64,
                                height: 64,
                                borderRadius: '50%',
                                backgroundColor: '#fa5151',
                                border: 'none',
                                boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: 'pointer'
                            }}
                        >
                            <PhoneOutlined style={{ fontSize: 28, color: '#fff', transform: 'rotate(135deg)' }} />
                        </button>
                    ) : (
                        <button
                            onClick={start}
                            disabled={isLoading}
                            style={{
                                width: 64,
                                height: 64,
                                borderRadius: '50%',
                                backgroundColor: isLoading ? '#8fdcb8' : '#07c160',
                                border: 'none',
                                boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: isLoading ? 'not-allowed' : 'pointer',
                                opacity: isLoading ? 0.7 : 1,
                                transition: 'all 0.3s ease'
                            }}
                        >
                            {isLoading ? (
                                <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            ) : (
                                <PhoneOutlined style={{ fontSize: 28, color: '#fff', transform: 'rotate(0deg)' }} />
                            )}
                        </button>
                    )}
                </div>
            </div>

            {/* 可收起的聊天侧边栏 */}
            <div
                className={`absolute top-0 right-0 h-full z-30 transition-transform duration-300 ease-in-out ${isChatOpen ? 'translate-x-0' : 'translate-x-full'
                    }`}
            >
                <div className="relative h-full">
                    <button
                        onClick={() => setIsChatOpen(false)}
                        className="absolute left-0 top-1/2 -translate-x-full -translate-y-1/2 w-6 h-16 bg-white rounded-l-lg flex items-center justify-center shadow-lg"
                    >
                        <LeftOutlined className="text-gray-600" style={{ transform: 'rotate(180deg)' }} />
                    </button>
                    <ChatSidebar
                        chatHistory={chatHistory}
                        onSendMessage={handleSendMessage}
                    />
                </div>
            </div>

            {/* 设置面板 */}
            <Settings
                visible={isSettingsOpen}
                onClose={() => setIsSettingsOpen(false)}
            />
        </div>
    );
}
