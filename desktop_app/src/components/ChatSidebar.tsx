import { RobotOutlined, SendOutlined, UserOutlined } from '@ant-design/icons';
import { Bubble } from '@ant-design/x';
import { Avatar, Flex, Input } from 'antd';
import { useState } from 'react';

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: number;
}

interface ChatSidebarProps {
    chatHistory: ChatMessage[];
    onSendMessage: (text: string) => void;
}

export default function ChatSidebar({ chatHistory, onSendMessage }: ChatSidebarProps) {
    const [value, setValue] = useState('');

    const handleSubmit = () => {
        if (!value.trim()) return;
        onSendMessage(value);
        setValue('');
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <div className="w-80 bg-white/95 backdrop-blur-md flex flex-col h-full shadow-2xl">
            {/* 微信风格头部 */}
            <div className="p-4 border-b border-gray-100 bg-gray-50/80">
                <h2 className="text-gray-800 text-base font-medium m-0">聊天记录</h2>
            </div>

            {/* 消息列表 */}
            <div className="flex-1 overflow-y-auto p-3 bg-gray-50/50">
                {chatHistory.length === 0 ? (
                    <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                        暂无消息
                    </div>
                ) : (
                    <Flex vertical gap="small">
                        {chatHistory.map((item, index) => (
                            <Bubble
                                key={index}
                                placement={item.role === 'user' ? 'end' : 'start'}
                                content={item.content}
                                avatar={
                                    <Avatar
                                        size="small"
                                        icon={item.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
                                        style={{
                                            backgroundColor: item.role === 'user' ? '#07c160' : '#576b95',
                                            flexShrink: 0
                                        }}
                                    />
                                }
                                styles={{
                                    content: {
                                        backgroundColor: item.role === 'user' ? '#95ec69' : '#fff',
                                        color: '#000',
                                        borderRadius: item.role === 'user' ? '12px 4px 12px 12px' : '4px 12px 12px 12px',
                                        boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                                        maxWidth: '200px',
                                        wordBreak: 'break-word',
                                    }
                                }}
                            />
                        ))}
                    </Flex>
                )}
            </div>

            {/* 微信风格输入框 */}
            <div className="p-3 border-t border-gray-100 bg-gray-50/80">
                <div className="flex items-center gap-2">
                    <Input
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="输入消息..."
                        className="flex-1 rounded-full"
                        style={{
                            backgroundColor: '#fff',
                            border: '1px solid #e5e5e5'
                        }}
                    />
                    <button
                        onClick={handleSubmit}
                        disabled={!value.trim()}
                        className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${value.trim()
                                ? 'bg-green-500 text-white hover:bg-green-600'
                                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                            }`}
                    >
                        <SendOutlined style={{ fontSize: 14 }} />
                    </button>
                </div>
            </div>
        </div>
    );
}
