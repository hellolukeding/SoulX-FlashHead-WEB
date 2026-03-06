import { useCallback, useEffect, useRef, useState } from 'react';
import { message } from 'antd';
import { AudioRecorder, AudioPlayer } from '../utils/audio';

// ==================== ASR Hook ====================

interface UseASROptions {
    onError?: (error: Error) => void;
    onInterimResult?: (text: string) => void;
    onFinalResult?: (text: string) => void;
}

export const useASR = (options: UseASROptions = {}) => {
    const { onError, onInterimResult, onFinalResult } = options;
    const [isListening, setIsListening] = useState(false);
    const [interimText, setInterimText] = useState('');
    const recognitionRef = useRef<any>(null);

    const startListening = useCallback(() => {
        const SpeechRecognition = (window as any).SpeechRecognition
            || (window as any).webkitSpeechRecognition;

        if (!SpeechRecognition) {
            message.error('您的浏览器不支持语音识别');
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'zh-CN';

        recognition.onresult = (event: any) => {
            const last = event.results.length - 1;
            const transcript = event.results[last][0].transcript;

            if (event.results[last].isFinal) {
                setInterimText('');
                if (onFinalResult) {
                    onFinalResult(transcript.trim());
                }
            } else {
                setInterimText(transcript);
                if (onInterimResult) {
                    onInterimResult(transcript);
                }
            }
        };

        recognition.onerror = (event: any) => {
            console.error('ASR error:', event.error);
            if (event.error === 'not-allowed') {
                message.error('语音识别权限被拒绝');
            }
            if (onError) {
                onError(new Error(event.error));
            }
            setIsListening(false);
        };

        recognition.onend = () => {
            if (isListening) {
                // 自动重启（如果仍在监听状态）
                try {
                    recognition.start();
                } catch (e) {
                    console.error('Failed to restart ASR:', e);
                    setIsListening(false);
                }
            }
        };

        try {
            recognition.start();
            recognitionRef.current = recognition;
            setIsListening(true);
        } catch (e) {
            console.error('Failed to start ASR:', e);
            message.error('无法开启语音识别');
        }
    }, [isListening, onError, onInterimResult, onFinalResult]);

    const stopListening = useCallback(() => {
        if (recognitionRef.current) {
            recognitionRef.current.stop();
            recognitionRef.current = null;
        }
        setIsListening(false);
        setInterimText('');
    }, []);

    useEffect(() => {
        return () => {
            if (recognitionRef.current) {
                recognitionRef.current.stop();
            }
        };
    }, []);

    return {
        isListening,
        interimText,
        startListening,
        stopListening,
    };
};

// ==================== TTS Hook ====================

interface UseTTSOptions {
    autoPlay?: boolean;
    onPlayStart?: () => void;
    onPlayEnd?: () => void;
}

export const useTTS = (options: UseTTSOptions = {}) => {
    const { onPlayStart, onPlayEnd } = options;
    const [isPlaying, setIsPlaying] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const playerRef = useRef<AudioPlayer | null>(null);

    useEffect(() => {
        playerRef.current = new AudioPlayer();
        return () => {
            if (playerRef.current) {
                playerRef.current.release();
            }
        };
    }, []);

    const speak = useCallback(async (text: string, audioUrl?: string) => {
        if (!text.trim()) {
            return;
        }

        if (!playerRef.current) {
            message.error('音频播放器未初始化');
            return;
        }

        setIsLoading(true);
        try {
            if (audioUrl) {
                await playerRef.current.playFromUrl(audioUrl);
            } else {
                // 使用浏览器的 Speech Synthesis API
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'zh-CN';
                utterance.onstart = () => {
                    setIsPlaying(true);
                    if (onPlayStart) onPlayStart();
                };
                utterance.onend = () => {
                    setIsPlaying(false);
                    if (onPlayEnd) onPlayEnd();
                };
                window.speechSynthesis.speak(utterance);
                return;
            }

            setIsPlaying(true);
            if (onPlayStart) onPlayStart();

            // 监听播放结束
            const checkEnded = setInterval(() => {
                if (!playerRef.current?.isPlayingNow()) {
                    clearInterval(checkEnded);
                    setIsPlaying(false);
                    if (onPlayEnd) onPlayEnd();
                }
            }, 100);
        } catch (error) {
            console.error('TTS error:', error);
            message.error('语音播放失败');
            setIsPlaying(false);
        } finally {
            setIsLoading(false);
        }
    }, [onPlayStart, onPlayEnd]);

    const stop = useCallback(() => {
        if (playerRef.current) {
            playerRef.current.stop();
        }
        window.speechSynthesis.cancel();
        setIsPlaying(false);
    }, []);

    const setVolume = useCallback((volume: number) => {
        if (playerRef.current) {
            playerRef.current.setVolume(volume);
        }
    }, []);

    return {
        isPlaying,
        isLoading,
        speak,
        stop,
        setVolume,
    };
};

// ==================== LLM Hook ====================

interface UseLLMOptions {
    sessionId: string;
    onChunk?: (text: string) => void;
    onComplete?: (fullText: string) => void;
    onError?: (error: Error) => void;
    stream?: boolean;
}

export const useLLM = (options: UseLLMOptions) => {
    const { sessionId, onChunk, onComplete, onError, stream = true } = options;
    const [isLoading, setIsLoading] = useState(false);
    const [isStreaming, setIsStreaming] = useState(false);
    const abortControllerRef = useRef<AbortController | null>(null);

    const chat = useCallback(async (userMessage: string) => {
        if (!userMessage.trim()) {
            return;
        }

        setIsLoading(true);
        setIsStreaming(true);

        if (stream) {
            // 流式响应
            abortControllerRef.current = new AbortController();

            try {
                // 这里需要调用实际的流式 API
                // 暂时使用模拟数据
                const response = await fetch('/api/llm/chat/stream', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: userMessage,
                        sessionid: parseInt(sessionId),
                        stream: true,
                    }),
                    signal: abortControllerRef.current.signal,
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const reader = response.body?.getReader();
                const decoder = new TextDecoder();
                let fullText = '';

                if (reader) {
                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;

                        const chunk = decoder.decode(value);
                        const lines = chunk.split('\n').filter(l => l.trim());

                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                const data = line.slice(6);
                                if (data === '[DONE]') {
                                    if (onComplete) onComplete(fullText);
                                    break;
                                }

                                try {
                                    const parsed = JSON.parse(data);
                                    const text = parsed.content || parsed.text || '';
                                    if (text) {
                                        fullText += text;
                                        if (onChunk) onChunk(text);
                                    }
                                } catch (e) {
                                    console.warn('Parse error:', data);
                                }
                            }
                        }
                    }
                }
            } catch (error: any) {
                if (error.name === 'AbortError') {
                    console.log('Request aborted');
                } else {
                    console.error('LLM error:', error);
                    if (onError) onError(error);
                    message.error('对话失败');
                }
            } finally {
                setIsLoading(false);
                setIsStreaming(false);
            }
        } else {
            // 非流式响应
            try {
                // 这里调用实际的 API
                const response = await fetch('/api/llm/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: userMessage,
                        sessionid: parseInt(sessionId),
                    }),
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();
                const text = data.content || data.text || data.message || '';

                if (onComplete) onComplete(text);
            } catch (error) {
                console.error('LLM error:', error);
                if (onError) onError(error as Error);
                message.error('对话失败');
            } finally {
                setIsLoading(false);
            }
        }
    }, [sessionId, stream, onChunk, onComplete, onError]);

    const abort = useCallback(() => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
        }
        setIsStreaming(false);
        setIsLoading(false);
    }, []);

    useEffect(() => {
        return () => {
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, []);

    return {
        isLoading,
        isStreaming,
        chat,
        abort,
    };
};

// ==================== 音频录制 Hook ====================

export const useAudioRecorder = () => {
    const [isRecording, setIsRecording] = useState(false);
    const [audioLevel, setAudioLevel] = useState(0);
    const recorderRef = useRef<AudioRecorder | null>(null);
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const startRecording = useCallback(async (sampleRate = 16000) => {
        const recorder = new AudioRecorder();
        await recorder.start(sampleRate);
        recorderRef.current = recorder;
        setIsRecording(true);

        // 监控音频电平
        intervalRef.current = setInterval(async () => {
            const level = await recorder.getAudioLevel();
            setAudioLevel(level);
        }, 100);
    }, []);

    const stopRecording = useCallback(async () => {
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
        }

        if (recorderRef.current) {
            const blob = await recorderRef.current.stop();
            recorderRef.current.release();
            recorderRef.current = null;
            setIsRecording(false);
            setAudioLevel(0);
            return blob;
        }
        return null;
    }, []);

    useEffect(() => {
        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
            if (recorderRef.current) {
                recorderRef.current.release();
            }
        };
    }, []);

    return {
        isRecording,
        audioLevel,
        startRecording,
        stopRecording,
    };
};
