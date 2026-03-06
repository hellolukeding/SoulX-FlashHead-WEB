// ==================== 音频录制器 ====================

export class AudioRecorder {
    private mediaRecorder: MediaRecorder | null = null;
    private audioChunks: Blob[] = [];
    private stream: MediaStream | null = null;

    async start(sampleRate = 16000): Promise<void> {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                },
            });

            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4',
            });

            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.start(100); // 每100ms触发一次
        } catch (error) {
            console.error('Failed to start audio recording:', error);
            throw error;
        }
    }

    async stop(): Promise<Blob> {
        return new Promise((resolve) => {
            if (!this.mediaRecorder) {
                resolve(new Blob());
                return;
            }

            this.mediaRecorder.onstop = () => {
                const blob = new Blob(this.audioChunks, {
                    type: this.mediaRecorder?.mimeType || 'audio/webm',
                });
                this.audioChunks = [];
                resolve(blob);
            };

            this.mediaRecorder.stop();
            if (this.stream) {
                this.stream.getTracks().forEach(track => track.stop());
            }
        });
    }

    getAudioLevel(): Promise<number> {
        return new Promise((resolve) => {
            if (!this.stream) {
                resolve(0);
                return;
            }

            const audioContext = new AudioContext();
            const analyser = audioContext.createAnalyser();
            const source = audioContext.createMediaStreamSource(this.stream);
            source.connect(analyser);

            analyser.fftSize = 256;
            const dataArray = new Uint8Array(analyser.frequencyBinCount);

            const checkLevel = () => {
                analyser.getByteFrequencyData(dataArray);
                const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
                resolve(average / 255);
            };

            checkLevel();
            audioContext.close();
        });
    }

    release(): void {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        this.mediaRecorder = null;
        this.audioChunks = [];
    }
}

// ==================== 音频播放器 ====================

export class AudioPlayer {
    private audioContext: AudioContext | null = null;
    private source: AudioBufferSourceNode | null = null;
    private analyser: AnalyserNode | null = null;
    private gainNode: GainNode | null = null;
    private isPlaying: boolean = false;

    constructor() {
        if (typeof window !== 'undefined' && 'AudioContext' in window) {
            this.audioContext = new AudioContext();
            this.analyser = this.audioContext.createAnalyser();
            this.gainNode = this.audioContext.createGain();

            this.gainNode.connect(this.audioContext.destination);
        }
    }

    async playFromArrayBuffer(arrayBuffer: ArrayBuffer): Promise<void> {
        if (!this.audioContext) {
            throw new Error('AudioContext not available');
        }

        // 停止当前播放
        this.stop();

        try {
            const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);

            this.source = this.audioContext.createBufferSource();
            this.source.buffer = audioBuffer;

            if (this.analyser && this.gainNode) {
                this.source.connect(this.analyser);
                this.analyser.connect(this.gainNode);
            } else if (this.gainNode) {
                this.source.connect(this.gainNode);
            } else {
                this.source.connect(this.audioContext.destination);
            }

            this.source.onended = () => {
                this.isPlaying = false;
            };

            this.source.start(0);
            this.isPlaying = true;
        } catch (error) {
            console.error('Failed to play audio:', error);
            throw error;
        }
    }

    async playFromBlob(blob: Blob): Promise<void> {
        const arrayBuffer = await blob.arrayBuffer();
        await this.playFromArrayBuffer(arrayBuffer);
    }

    async playFromUrl(url: string): Promise<void> {
        const response = await fetch(url);
        const arrayBuffer = await response.arrayBuffer();
        await this.playFromArrayBuffer(arrayBuffer);
    }

    stop(): void {
        if (this.source) {
            try {
                this.source.stop();
            } catch (e) {
                // 忽略已停止的错误
            }
            this.source = null;
        }
        this.isPlaying = false;
    }

    setVolume(volume: number): void {
        if (this.gainNode) {
            this.gainNode.gain.value = volume;
        }
    }

    getVolume(): number {
        if (this.gainNode) {
            return this.gainNode.gain.value;
        }
        return 1;
    }

    async getAudioLevel(): Promise<number> {
        if (!this.analyser || !this.isPlaying) {
            return 0;
        }

        const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteFrequencyData(dataArray);

        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        return average / 255;
    }

    isPlayingNow(): boolean {
        return this.isPlaying;
    }

    release(): void {
        this.stop();
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
    }
}

// ==================== 音频可视化 ====================

export const drawAudioVisualizer = (
    canvas: HTMLCanvasElement,
    analyser: AnalyserNode,
    options: {
        barColor?: string;
        barWidth?: number;
        barGap?: number;
        minHeight?: number;
    } = {}
) => {
    const {
        barColor = '#4CAF50',
        barWidth = 3,
        barGap = 1,
        minHeight = 2
    } = options;

    if (!canvas || !analyser) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
        requestAnimationFrame(draw);

        analyser.getByteFrequencyData(dataArray);

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const barCount = Math.floor(bufferLength / 4);
        const totalBarWidth = barWidth + barGap;
        const startX = (canvas.width - barCount * totalBarWidth) / 2;

        for (let i = 0; i < barCount; i++) {
            const value = dataArray[i];
            const percent = value / 255;
            const height = Math.max(minHeight, canvas.height * percent * 0.8);

            const x = startX + i * totalBarWidth;
            const y = (canvas.height - height) / 2;

            ctx.fillStyle = barColor;
            ctx.fillRect(x, y, barWidth, height);
        }
    };

    draw();
};

// ==================== 音频格式转换 ====================

export const convertBlobToWav = async (blob: Blob): Promise<Blob> => {
    const arrayBuffer = await blob.arrayBuffer();
    const audioContext = new AudioContext();
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

    const offlineContext = new OfflineAudioContext(
        audioBuffer.numberOfChannels,
        audioBuffer.length,
        audioBuffer.sampleRate
    );

    const source = offlineContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(offlineContext.destination);
    source.start(0);

    const renderedBuffer = await offlineContext.startRendering();

    // 编码为 WAV
    const wav = audioBufferToWav(renderedBuffer);
    audioContext.close();

    return new Blob([wav], { type: 'audio/wav' });
};

const audioBufferToWav = (buffer: AudioBuffer): ArrayBuffer => {
    const length = buffer.length * buffer.numberOfChannels * 2 + 44;
    const arrayBuffer = new ArrayBuffer(length);
    const view = new DataView(arrayBuffer);

    const writeString = (offset: number, string: string) => {
        for (let i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    };

    // WAV 头
    writeString(0, 'RIFF');
    view.setUint32(4, length - 8, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM
    view.setUint16(22, 1, true); // Mono
    view.setUint32(24, buffer.sampleRate, true);
    view.setUint32(28, buffer.sampleRate * 2 * buffer.numberOfChannels, true);
    view.setUint16(32, 2, true); // 16-bit
    view.setUint16(34, buffer.numberOfChannels, true);
    writeString(36, 'data');
    view.setUint32(40, length - 44, true);

    // 写入音频数据
    const channels: Float32Array[] = [];
    for (let i = 0; i < buffer.numberOfChannels; i++) {
        channels.push(buffer.getChannelData(i));
    }

    let offset = 44;
    for (let i = 0; i < buffer.length; i++) {
        for (let channel = 0; channel < buffer.numberOfChannels; channel++) {
            const sample = Math.max(-1, Math.min(1, channels[channel][i]));
            view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
            offset += 2;
        }
    }

    return arrayBuffer;
};
