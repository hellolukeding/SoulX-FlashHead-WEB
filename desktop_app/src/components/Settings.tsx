import { SettingOutlined } from '@ant-design/icons';
import { Button, Card, Col, Divider, Drawer, Form, Input, InputNumber, message, Radio, Select, Slider, Space, Switch, Typography } from 'antd';
import { useEffect, useState } from 'react';

const { Text } = Typography;

const LOCAL_STORAGE_KEY = 'livetalking_config';

interface ServiceConfig {
    tts_type: string;
    asr_type: string;
    llm_model: string;
    voice_id?: string;
    fps?: number;
    width?: number;
    height?: number;
    batch_size?: number;
    temperature?: number;
    max_tokens?: number;
    stream?: boolean;
}

const TTS_OPTIONS = [
    { label: 'Edge TTS (免费)', value: 'edge' },
    { label: 'Doubao TTS', value: 'doubao' },
    { label: '腾讯 TTS', value: 'tencent' },
    { label: 'Azure TTS', value: 'azure' },
];

const ASR_OPTIONS = [
    { label: 'Lip ASR (端到端)', value: 'lip' },
    { label: '腾讯 ASR', value: 'tencent' },
    { label: 'FunASR', value: 'funasr' },
];

const LLM_MODELS = [
    { label: 'GPT-4', value: 'gpt-4' },
    { label: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' },
    { label: 'Claude 3 Opus', value: 'claude-3-opus' },
    { label: 'Claude 3 Sonnet', value: 'claude-3-sonnet' },
    { label: '通义千问', value: 'qwen' },
    { label: '文心一言', value: 'ernie' },
    { label: '智谱 GLM', value: 'glm' },
];

const PRESET_MODES = [
    { label: '推荐模式', value: 'recommended', fps: 25, width: 384, height: 384, batch_size: 8 },
    { label: '极限性能', value: 'performance', fps: 20, width: 256, height: 256, batch_size: 4 },
    { label: '高质量', value: 'quality', fps: 30, width: 450, height: 450, batch_size: 12 },
];

interface SettingsProps {
    visible: boolean;
    onClose: () => void;
}

export default function Settings({ visible, onClose }: SettingsProps) {
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [config, setConfig] = useState<ServiceConfig>({
        tts_type: 'edge',
        asr_type: 'lip',
        llm_model: 'gpt-3.5-turbo',
        fps: 25,
        width: 384,
        height: 384,
        batch_size: 8,
        temperature: 0.7,
        max_tokens: 1000,
        stream: true,
    });

    // 加载配置
    useEffect(() => {
        if (visible) {
            loadConfig();
        }
    }, [visible]);

    const loadConfig = () => {
        setLoading(true);
        try {
            const savedConfig = localStorage.getItem(LOCAL_STORAGE_KEY);
            if (savedConfig) {
                const loadedConfig = { ...config, ...JSON.parse(savedConfig) };
                setConfig(loadedConfig);
                form.setFieldsValue(loadedConfig);
            }
        } catch (error) {
            console.error('Failed to load config:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        try {
            const values = await form.validateFields();
            setSaving(true);

            // 保存到 localStorage
            const newConfig = { ...config, ...values };
            localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(newConfig));
            setConfig(newConfig);

            message.success('配置已保存（本地）');
            onClose();
        } catch (error) {
            console.error('Failed to save config:', error);
            message.error('保存配置失败');
        } finally {
            setSaving(false);
        }
    };

    const handlePresetModeChange = (mode: string) => {
        const preset = PRESET_MODES.find(m => m.value === mode);
        if (preset) {
            form.setFieldsValue({
                fps: preset.fps,
                width: preset.width,
                height: preset.height,
                batch_size: preset.batch_size,
            });
        }
    };

    return (
        <Drawer
            title={
                <Space>
                    <SettingOutlined />
                    <span>系统设置</span>
                </Space>
            }
            placement="right"
            size={{ width: 480 }}
            open={visible}
            onClose={onClose}
            footer={
                <div style={{ textAlign: 'right' }}>
                    <Space>
                        <Button onClick={onClose}>取消</Button>
                        <Button type="primary" onClick={handleSave} loading={saving}>
                            保存配置
                        </Button>
                    </Space>
                </div>
            }
        >
            <Form
                form={form}
                layout="vertical"
                initialValues={config}
                disabled={loading}
            >
                {/* TTS 配置 */}
                <Card title="语音合成 (TTS)" size="small" className="mb-4">
                    <Form.Item
                        label="TTS 引擎"
                        name="tts_type"
                        tooltip="选择语音合成服务提供商"
                    >
                        <Select options={TTS_OPTIONS} />
                    </Form.Item>

                    <Form.Item
                        label="语音 ID"
                        name="voice_id"
                        tooltip="可选：指定特定语音（部分引擎支持）"
                    >
                        <Input placeholder="例如：zh-CN-XiaoxiaoNeural" />
                    </Form.Item>

                    <Form.Item
                        label="语速"
                        name="speed"
                        tooltip="调整语音播放速度（0.5 - 2.0）"
                    >
                        <Slider min={0.5} max={2} step={0.1} marks={{ 0.5: '慢', 1: '正常', 2: '快' }} />
                    </Form.Item>

                    <Form.Item
                        label="音量"
                        name="volume"
                        tooltip="调整语音音量（0 - 1）"
                    >
                        <Slider min={0} max={1} step={0.1} marks={{ 0: '静音', 1: '最大' }} />
                    </Form.Item>
                </Card>

                {/* ASR 配置 */}
                <Card title="语音识别 (ASR)" size="small" className="mb-4">
                    <Form.Item
                        label="ASR 引擎"
                        name="asr_type"
                        tooltip="选择语音识别服务提供商"
                    >
                        <Radio.Group options={ASR_OPTIONS} optionType="button" buttonStyle="solid" />
                    </Form.Item>

                    <Form.Item
                        label="语言"
                        name="language"
                        tooltip="识别语言（部分引擎支持）"
                    >
                        <Select
                            options={[
                                { label: '中文', value: 'zh-CN' },
                                { label: '英文', value: 'en-US' },
                                { label: '粤语', value: 'zh-YUE' },
                            ]}
                        />
                    </Form.Item>
                </Card>

                {/* LLM 配置 */}
                <Card title="大语言模型 (LLM)" size="small" className="mb-4">
                    <Form.Item
                        label="模型"
                        name="llm_model"
                        tooltip="选择对话使用的语言模型"
                    >
                        <Select options={LLM_MODELS} showSearch />
                    </Form.Item>

                    <Form.Item
                        label="Temperature"
                        name="temperature"
                        tooltip="控制生成随机性（0.0 - 1.0）"
                    >
                        <Slider min={0} max={1} step={0.1} marks={{ 0: '精确', 1: '创造' }} />
                    </Form.Item>

                    <Form.Item
                        label="最大 Tokens"
                        name="max_tokens"
                        tooltip="单次响应最大长度"
                    >
                        <InputNumber min={100} max={4000} step={100} className="w-full" />
                    </Form.Item>

                    <Form.Item
                        label="流式响应"
                        name="stream"
                        tooltip="启用流式输出以获得更快响应"
                        valuePropName="checked"
                    >
                        <Switch />
                    </Form.Item>
                </Card>

                {/* 性能配置 */}
                <Card title="性能优化" size="small" className="mb-4">
                    <Form.Item label="预设模式">
                        <Radio.Group
                            options={PRESET_MODES}
                            optionType="button"
                            buttonStyle="solid"
                            onChange={(e) => handlePresetModeChange(e.target.value)}
                        />
                    </Form.Item>

                    <Divider orientationMargin={0} plain>高级参数</Divider>

                    <Form.Item
                        label="FPS"
                        name="fps"
                        tooltip="视频帧率（越高越流畅但更消耗性能）"
                    >
                        <Slider min={15} max={50} step={5} marks={{ 15: '15', 25: '25', 30: '30', 50: '50' }} />
                    </Form.Item>

                    <Form.Item label="分辨率">
                        <Col span={11}>
                            <Form.Item name="width" noStyle>
                                <InputNumber min={256} max={512} step={64} addonAfter="W" className="w-full" />
                            </Form.Item>
                        </Col>
                        <Col span={2}>
                            <span style={{ textAlign: 'center', display: 'block' }}>×</span>
                        </Col>
                        <Col span={11}>
                            <Form.Item name="height" noStyle>
                                <InputNumber min={256} max={512} step={64} addonAfter="H" className="w-full" />
                            </Form.Item>
                        </Col>
                    </Form.Item>

                    <Form.Item
                        label="Batch Size"
                        name="batch_size"
                        tooltip="批处理大小（影响 GPU 内存占用）"
                    >
                        <Slider min={2} max={16} step={2} marks={{ 2: '2', 4: '4', 8: '8', 16: '16' }} />
                    </Form.Item>
                </Card>

                {/* 说明 */}
                <Card size="small" type="inner">
                    <Space direction="vertical" size="small">
                        <Text type="secondary">
                            <strong>提示：</strong>
                        </Text>
                        <ul style={{ margin: 0, paddingLeft: 20 }}>
                            <li>
                                <Text type="secondary">
                                    FPS 越高越流畅，但会消耗更多 CPU
                                </Text>
                            </li>
                            <li>
                                <Text type="secondary">
                                    分辨率越高画质越好，但计算量更大
                                </Text>
                            </li>
                            <li>
                                <Text type="secondary">
                                    Batch Size 需要根据显卡内存调整
                                </Text>
                            </li>
                        </ul>
                    </Space>
                </Card>
            </Form>
        </Drawer>
    );
}
