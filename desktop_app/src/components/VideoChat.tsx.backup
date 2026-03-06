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
import { negotiateOffer, sendHumanMessage } from '../api';
import ChatSidebar, { ChatMessage } from './ChatSidebar';
import Settings from './Settings';

export default function VideoChat() {
    const [sessionId, setSessionId] = useState<string>('0');
    const [isStarted, setIsStarted] = useState(false);
    const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
    const [isChatOpen, setIsChatOpen] = useState(false);
    const [callDuration, setCallDuration] = useState(0);
    const [isLoading, setIsLoading] = useState(false);

    const videoRef = useRef<HTMLVideoElement>(null);
    const localVideoRef = useRef<HTMLVideoElement>(null);
    const audioRef = useRef<HTMLAudioElement>(null);
    const pcRef = useRef<RTCPeerConnection | null>(null);
    const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const durationRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const localStreamRef = useRef<MediaStream | null>(null);

    const [isVoiceChatOn, setIsVoiceChatOn] = useState(false);
    const [isSpeakerOn, setIsSpeakerOn] = useState(true);
    const [isCameraOn, setIsCameraOn] = useState(false);
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [isAISpeaking, setIsAISpeaking] = useState(false); // AI 是否正在说话
    const isAISpeakingRef = useRef(false); // 用于在闭包中获取最新值
    const recognitionRef = useRef<any>(null);
    const aiSpeakingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const micPermissionStreamRef = useRef<MediaStream | null>(null); // 用于权限检查的流

    // 同步isAISpeaking状态到ref
    useEffect(() => {
        isAISpeakingRef.current = isAISpeaking;
    }, [isAISpeaking]);

    // 格式化通话时长
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

    useEffect(() => {
        if (isVoiceChatOn && isStarted) {
            const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
            if (!SpeechRecognition) {
                message.error('您的浏览器不支持语音识别');
                setIsVoiceChatOn(false);
                return;
            }

            // 先请求麦克风权限（确保触发权限提示）
            message.loading({ content: '正在请求麦克风权限...', key: 'micPermission', duration: 0 });

            // 先枚举可用的音频设备，帮助诊断问题
            navigator.mediaDevices.enumerateDevices()
                .then((devices) => {
                    const audioInputs = devices.filter(device => device.kind === 'audioinput');
                    const audioOutputs = devices.filter(device => device.kind === 'audiooutput');
                    const videoInputs = devices.filter(device => device.kind === 'videoinput');

                    console.log('[ASR] ========== Device Enumeration ==========');
                    console.log('[ASR] Audio Input devices (microphones):', audioInputs.length);
                    audioInputs.forEach((device, index) => {
                        console.log(`  [${index}] ${device.label || '(无标签)'} (ID: ${device.deviceId})`);
                    });
                    console.log('[ASR] Audio Output devices (speakers):', audioOutputs.length);
                    audioOutputs.forEach((device, index) => {
                        console.log(`  [${index}] ${device.label || '(无标签)'}`);
                    });
                    console.log('[ASR] Video Input devices (cameras):', videoInputs.length);
                    videoInputs.forEach((device, index) => {
                        console.log(`  [${index}] ${device.label || '(无标签)'}`);
                    });
                    console.log('[ASR] ========================================');

                    if (audioInputs.length === 0) {
                        console.warn('[ASR] ❌ No audio input devices found!');
                        message.error({
                            content: '未检测到麦克风设备。请检查：1) macOS系统设置中Chrome是否已获得麦克风权限 2) 麦克风是否被其他应用占用',
                            duration: 8
                        });
                    } else {
                        console.log('[ASR] ✓ Found audio input devices');
                    }

                    return navigator.mediaDevices.getUserMedia({ audio: true });
                })
                .then((stream) => {
                    message.success({ content: '麦克风权限已授予', key: 'micPermission', duration: 2 });
                    console.log('[ASR] Microphone permission granted');

                    // 保存流引用，用于后续清理
                    micPermissionStreamRef.current = stream;

                    // 立即停止音频轨道（我们只需要权限，不需要实际的音频流）
                    stream.getTracks().forEach(track => track.stop());

                    // 权限获取成功后，启动语音识别
                    initSpeechRecognition();
                })
                .catch((err: any) => {
                    setIsVoiceChatOn(false);

                    // 根据不同的错误类型提供不同的提示
                    if (err.name === 'NotAllowedError') {
                        message.error({ content: '麦克风权限被拒绝，请允许麦克风访问以使用语音识别功能', key: 'micPermission', duration: 5 });
                        message.warning({
                            content: '如需使用语音识别，请点击浏览器地址栏左侧的锁图标，允许麦克风访问',
                            duration: 6
                        });
                    } else if (err.name === 'NotFoundError') {
                        message.error({ content: '未检测到麦克风设备，请连接麦克风后重试', key: 'micPermission', duration: 5 });
                        message.warning({
                            content: '请检查麦克风是否已正确连接，并在系统设置中确认音频输入设备可用',
                            duration: 6
                        });
                    } else {
                        message.error({ content: `麦克风访问失败: ${err.message || err.name}`, key: 'micPermission', duration: 5 });
                    }
                    console.error('[ASR] Microphone permission denied:', err);
                });
        } else {
            if (recognitionRef.current) {
                recognitionRef.current.stop();
                recognitionRef.current = null;
                console.log('[ASR] Speech recognition stopped');
            }
            // 清理权限检查的流
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
            // 清理权限检查的流
            if (micPermissionStreamRef.current) {
                micPermissionStreamRef.current.getTracks().forEach(track => track.stop());
                micPermissionStreamRef.current = null;
            }
        };
    }, [isVoiceChatOn, isStarted]); // 移除 isAISpeaking 依赖

    // 初始化语音识别
    const initSpeechRecognition = () => {
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = false;
        recognition.lang = 'zh-CN';

        recognition.onresult = (event: any) => {
            // AI 正在说话时，忽略识别结果（使用ref获取最新值）
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
                message.error('语音识别权限被拒绝，请在浏览器设置中允许麦克风权限', 5);
                message.warning('请点击浏览器地址栏左侧的锁图标，允许麦克风访问', 6);
                setIsVoiceChatOn(false);
            } else if (event.error === 'no-speech') {
                // 忽略无语音错误，继续监听
                console.log('[ASR] No speech detected, continuing...');
            } else if (event.error === 'network') {
                console.error('[ASR] Network error, will retry...');
            } else if (event.error === 'aborted') {
                console.log('[ASR] Recognition aborted');
            } else {
                console.warn('[ASR] Unhandled recognition error:', event.error);
            }
        };

        recognition.onend = () => {
            // 如果麦克风开启且服务已连接，则自动重启（持续监听）
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

    const resetTimer = () => {
        if (timerRef.current) clearTimeout(timerRef.current);
        if (isStarted) {
            timerRef.current = setTimeout(() => {
                message.info('长时间未操作，已自动断开连接');
                stop();
            }, 60000);
        }
    };

    // 标记AI开始说话（由data channel消息触发）
    const markAISpeaking = () => {
        setIsAISpeaking(true);

        // 清除之前的定时器
        if (aiSpeakingTimeoutRef.current) {
            clearTimeout(aiSpeakingTimeoutRef.current);
        }

        // 500ms后如果没有新消息，则认为AI停止说话
        aiSpeakingTimeoutRef.current = setTimeout(() => {
            console.log('[AEC] AI stopped speaking (no new messages for 500ms)');
            setIsAISpeaking(false);
        }, 500);
    };

    const start = async () => {
        if (isStarted || isLoading) return;

        setIsLoading(true);

        // 先开启本地摄像头
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'user' },
                audio: false
            });
            localStreamRef.current = stream;
            if (localVideoRef.current) {
                localVideoRef.current.srcObject = stream;
            }
            setIsCameraOn(true);
        } catch (err) {
            console.error('无法获取摄像头', err);
            // 摄像头获取失败不阻止通话
        }

        const config: RTCConfiguration = {
            sdpSemantics: 'unified-plan'
        } as any;

        const pc = new RTCPeerConnection(config);
        pcRef.current = pc;

        const dc = pc.createDataChannel("chat");
        dc.onmessage = (event) => {
            const text = event.data;
            if (text) {
                // 每次收到AI消息时，标记AI正在说话
                markAISpeaking();

                setChatHistory(prev => {
                    const lastMsg = prev[prev.length - 1];
                    if (lastMsg && lastMsg.role === 'assistant') {
                        const updated = [
                            ...prev.slice(0, -1),
                            { ...lastMsg, content: lastMsg.content + text }
                        ];
                        return updated;
                    } else {
                        const newMessage = {
                            role: 'assistant' as const,
                            content: text,
                            timestamp: Date.now()
                        };
                        return [...prev, newMessage];
                    }
                });
            }
        };

        pc.addEventListener('track', (evt) => {
            if (evt.track.kind === 'video') {
                if (videoRef.current) {
                    videoRef.current.srcObject = evt.streams[0];
                }
            } else {
                if (audioRef.current) {
                    audioRef.current.srcObject = evt.streams[0];
                }
            }
        });

        pc.addTransceiver('video', { direction: 'recvonly' });
        pc.addTransceiver('audio', { direction: 'recvonly' });

        try {
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);

            await new Promise<void>((resolve) => {
                if (pc.iceGatheringState === 'complete') {
                    resolve();
                } else {
                    const checkState = () => {
                        if (pc.iceGatheringState === 'complete') {
                            pc.removeEventListener('icegatheringstatechange', checkState);
                            resolve();
                        }
                    };
                    pc.addEventListener('icegatheringstatechange', checkState);
                }
            });

            const answer = await negotiateOffer({
                sdp: pc.localDescription?.sdp,
                type: pc.localDescription?.type,
            });

            setSessionId(answer.sessionid);
            await pc.setRemoteDescription(answer);
            setIsStarted(true);
            setIsLoading(false);

        } catch (e) {
            console.error(e);
            message.error('连接失败: ' + e);
            // 连接失败时关闭摄像头
            if (localStreamRef.current) {
                localStreamRef.current.getTracks().forEach(track => track.stop());
                localStreamRef.current = null;
            }
            setIsCameraOn(false);
            setIsLoading(false);
        }
    };

    const stop = () => {
        if (pcRef.current) {
            pcRef.current.close();
            pcRef.current = null;
        }
        // 关闭本地摄像头
        if (localStreamRef.current) {
            localStreamRef.current.getTracks().forEach(track => track.stop());
            localStreamRef.current = null;
        }
        setIsCameraOn(false);
        setIsStarted(false);
    };

    const handleSendMessage = async (text: string) => {
        resetTimer();
        setChatHistory(prev => [...prev, {
            role: 'user',
            content: text,
            timestamp: Date.now()
        }]);

        try {
            await sendHumanMessage(text, sessionId);
        } catch (e) {
            console.error(e);
            message.error('发送失败');
        }
    };

    const toggleSpeaker = () => {
        setIsSpeakerOn(!isSpeakerOn);
        if (audioRef.current) {
            audioRef.current.muted = isSpeakerOn;
        }
    };

    // 开启/关闭本地摄像头
    const toggleCamera = async () => {
        if (isCameraOn) {
            // 关闭摄像头
            if (localStreamRef.current) {
                localStreamRef.current.getTracks().forEach(track => track.stop());
                localStreamRef.current = null;
            }
            if (localVideoRef.current) {
                localVideoRef.current.srcObject = null;
            }
            setIsCameraOn(false);
        } else {
            // 开启摄像头
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: 'user' },
                    audio: false
                });
                localStreamRef.current = stream;
                if (localVideoRef.current) {
                    localVideoRef.current.srcObject = stream;
                }
                setIsCameraOn(true);
            } catch (err) {
                console.error('无法获取摄像头', err);
                message.error('无法获取摄像头权限');
            }
        }
    };

    useEffect(() => {
        resetTimer();
        return () => {
            if (timerRef.current) clearTimeout(timerRef.current);
        };
    }, [isStarted]);

    // 当 isStarted 变为 true 且有本地流时，绑定到 video 元素
    useEffect(() => {
        if (isStarted && isCameraOn && localStreamRef.current && localVideoRef.current) {
            localVideoRef.current.srcObject = localStreamRef.current;
        }
    }, [isStarted, isCameraOn]);

    useEffect(() => {
        return () => {
            stop();
            // 清理AI说话定时器
            if (aiSpeakingTimeoutRef.current) {
                clearTimeout(aiSpeakingTimeoutRef.current);
            }
        }
    }, []);

    return (
        <div
            className="relative w-full h-full bg-[#ededed] overflow-hidden"
            onMouseMove={resetTimer}
            onClick={resetTimer}
        >
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
                {!isStarted && !isLoading && (
                    <div className="absolute inset-0 flex items-center justify-center bg-[#ededed] z-10">
                        <div className="text-center">
                            <div className="w-32 h-32 mx-auto mb-6 rounded-full bg-gray-300 flex items-center justify-center overflow-hidden">
                                <span className="text-6xl">🤖</span>
                            </div>
                            <div className="text-xl text-gray-700 mb-2">AI 助手</div>
                            <div className="text-gray-500 text-sm">等待接听...</div>
                        </div>
                    </div>
                )}
                {isLoading && !isStarted && (
                    <div className="absolute inset-0 flex items-center justify-center bg-[#ededed] z-10">
                        <div className="text-center">
                            {/* Loading 动画 */}
                            <div className="relative w-32 h-32 mx-auto mb-6">
                                <div className="absolute inset-0 rounded-full border-4 border-gray-200"></div>
                                <div className="absolute inset-0 rounded-full border-4 border-t-green-500 border-r-transparent border-b-transparent border-l-transparent animate-spin"></div>
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <span className="text-5xl">🤖</span>
                                </div>
                            </div>
                            <div className="text-xl text-gray-700 mb-2">正在连接中...</div>
                            <div className="text-gray-500 text-sm">请稍候，正在建立连接</div>
                        </div>
                    </div>
                )}
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    className="w-full h-full object-cover"
                    style={{ display: isStarted ? 'block' : 'none' }}
                />
                <audio ref={audioRef} autoPlay />
            </div>

            {/* 右上角小窗口（本地摄像头画面） */}
            {isStarted && (
                <div
                    className="absolute top-12 right-4 w-24 h-32 bg-gray-800 overflow-hidden shadow-lg z-20 cursor-pointer"
                    style={{ borderRadius: 8, border: '2px solid white' }}
                    onClick={toggleCamera}
                >
                    <video
                        ref={localVideoRef}
                        autoPlay
                        playsInline
                        muted
                        className="w-full h-full object-cover"
                        style={{
                            transform: 'scaleX(-1)',
                            display: isCameraOn ? 'block' : 'none'
                        }}
                    />
                    {!isCameraOn && (
                        <div className="w-full h-full flex flex-col items-center justify-center bg-gray-700">
                            <span className="text-2xl mb-1">📷</span>
                            <span className="text-white text-xs">点击开启</span>
                        </div>
                    )}
                </div>
            )}

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

            <input type="hidden" id="sessionid" value={sessionId} readOnly />

            {/* 设置面板 */}
            <Settings
                visible={isSettingsOpen}
                onClose={() => setIsSettingsOpen(false)}
            />
        </div>
    );
}
