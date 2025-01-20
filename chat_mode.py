import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


class ChatMode:
    def __init__(self, ctx):
        self.ctx = ctx
        self.history: List[ChatMessage] = []
        
    def format_chat_prompt(self, user_input: str) -> str:
        """チャット用のプロンプトをフォーマット"""
        # システムプロンプトの設定
        system_prompt = f"""あなたは{self.ctx["char_name"]}として会話してください。
{self.ctx.get("char_settings", "")}"""

        # 会話履歴の構築
        memory_count = self.ctx.get("chat_memory_count", 5)
        conversation = []
        for msg in self.history[-memory_count:]:  # 指定された数の会話のみ使用
            if msg.role == 'user':
                conversation.append(f'{self.ctx["user_name"]}: {msg.content}')
            else:
                conversation.append(f'{self.ctx["char_name"]}: {msg.content}')

        # 新しい入力の追加
        conversation.append(f'{self.ctx["user_name"]}: {user_input}')
        
        # 最終プロンプトの構築
        prompt = f"""{system_prompt}

これまでの会話:
{chr(10).join(conversation)}

{self.ctx["char_name"]}:"""
        return prompt

    def add_message(self, role: str, content: str) -> None:
        """会話履歴に新しいメッセージを追加"""
        self.history.append(ChatMessage(role=role, content=content))
    
    def format_display_message(self, message: ChatMessage) -> str:
        """表示用のメッセージフォーマット"""
        if message.role == 'user':
            return f'{self.ctx["user_name"]} ({message.timestamp}):\n{message.content}\n\n'
        else:
            return f'{self.ctx["char_name"]} ({message.timestamp}):\n{message.content}\n\n'
    
    def get_formatted_history(self) -> str:
        """表示用に整形された会話履歴を取得"""
        return ''.join([self.format_display_message(msg) for msg in self.history])

    def clear_history(self) -> None:
        """会話履歴をクリア"""
        self.history.clear()