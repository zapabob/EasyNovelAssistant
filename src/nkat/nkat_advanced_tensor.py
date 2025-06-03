# -*- coding: utf-8 -*-
"""
NKAT Advanced Tensor Processing System
Phase 3: 非可換テンソル理論統合システム

【実装機能】
1. 非可換テンソル代数処理
2. 文学的表現空間の高次元モデリング
3. 動的テンソル変換システム
4. 表現品質の数学的最適化
5. リアルタイム表現学習

Author: EasyNovelAssistant Development Team
Date: 2025-01-06
Version: Phase 3 Advanced Implementation
"""

import os
import sys
import json
import time
import threading
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import torch
import torch.nn as nn
import torch.nn.functional as F
from tqdm import tqdm
import logging

# プロジェクトパス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)


@dataclass
class TensorSpaceMetrics:
    """テンソル空間メトリクス"""
    dimension: int
    rank: int
    entropy: float
    coherence: float
    expressiveness: float
    non_commutativity: float
    literary_quality: float


@dataclass
class ExpressionTensor:
    """表現テンソル"""
    content: str
    semantic_tensor: torch.Tensor
    stylistic_tensor: torch.Tensor
    emotional_tensor: torch.Tensor
    character_tensor: torch.Tensor
    context_tensor: torch.Tensor
    timestamp: float
    quality_score: float


class NonCommutativeAlgebra:
    """非可換代数処理システム"""
    
    def __init__(self, dimension: int = 256, device: str = None):
        self.dimension = dimension
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 非可換代数の基底要素
        self.generators = self._initialize_generators()
        self.structure_constants = self._compute_structure_constants()
        
        # 学習可能パラメータ
        self.adaptation_matrix = nn.Parameter(
            torch.randn(dimension, dimension, device=self.device) * 0.1
        )
        self.commutator_weights = nn.Parameter(
            torch.ones(dimension, device=self.device)
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"🔢 非可換代数システム初期化完了 (次元: {dimension})")
    
    def _initialize_generators(self) -> torch.Tensor:
        """生成元の初期化（Pauli行列の高次元拡張）"""
        generators = torch.zeros(self.dimension, self.dimension, self.dimension, device=self.device)
        
        # Pauli行列風の非可換生成元を構築
        for i in range(self.dimension):
            # 反エルミート生成元
            generator = torch.zeros(self.dimension, self.dimension, device=self.device)
            
            # 主対角線上の要素（エルミート部分）
            generator[i, i] = 1.0
            
            # 非対角要素（反エルミート部分）
            if i + 1 < self.dimension:
                generator[i, i + 1] = 1j
                generator[i + 1, i] = -1j
            
            generators[i] = generator
        
        return generators
    
    def _compute_structure_constants(self) -> torch.Tensor:
        """構造定数の計算 [g_i, g_j] = f_{ij}^k g_k"""
        structure_constants = torch.zeros(
            self.dimension, self.dimension, self.dimension, 
            device=self.device, dtype=torch.complex64
        )
        
        for i in range(self.dimension):
            for j in range(self.dimension):
                commutator = torch.matmul(self.generators[i], self.generators[j]) - \
                           torch.matmul(self.generators[j], self.generators[i])
                
                # 生成元の線形結合として表現
                for k in range(self.dimension):
                    structure_constants[i, j, k] = torch.trace(
                        torch.matmul(commutator, self.generators[k].conj().T)
                    )
        
        return structure_constants
    
    def tensor_product(self, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        """非可換テンソル積"""
        # Jordan積の変形版（非可換性を保持）
        jordan_product = 0.5 * (torch.matmul(a, b) + torch.matmul(b, a))
        lie_bracket = torch.matmul(a, b) - torch.matmul(b, a)
        
        # 適応的重み付き結合
        alpha = torch.sigmoid(self.commutator_weights.mean())
        return (1 - alpha) * jordan_product + alpha * lie_bracket
    
    def exponential_map(self, tangent_vector: torch.Tensor) -> torch.Tensor:
        """指数写像（リー群の要素への変換）"""
        # BCH公式の近似（3次まで）
        exp_approx = torch.eye(self.dimension, device=self.device)
        exp_approx += tangent_vector
        exp_approx += 0.5 * torch.matmul(tangent_vector, tangent_vector)
        exp_approx += (1.0/6.0) * torch.matmul(
            torch.matmul(tangent_vector, tangent_vector), tangent_vector
        )
        
        return exp_approx
    
    def group_action(self, group_element: torch.Tensor, vector: torch.Tensor) -> torch.Tensor:
        """群作用による表現変換"""
        # 随伴表現
        return torch.matmul(
            torch.matmul(group_element, vector.unsqueeze(-1)), 
            group_element.conj().T
        ).squeeze(-1)


class LiteraryExpressionSpace:
    """文学的表現空間モデリング"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device = config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        self.dimension = config.get('expression_dimension', 256)
        
        # 文学的特徴の基底
        self.semantic_basis = self._create_semantic_basis()
        self.stylistic_basis = self._create_stylistic_basis()
        self.emotional_basis = self._create_emotional_basis()
        
        # 表現変換ネットワーク
        self.transformation_net = self._build_transformation_network()
        
        # 品質評価器
        self.quality_evaluator = self._build_quality_evaluator()
        
        # メモリシステム
        self.expression_memory = deque(maxlen=1000)
        self.pattern_memory = defaultdict(list)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"📚 文学的表現空間初期化完了 (次元: {self.dimension})")
    
    def _create_semantic_basis(self) -> torch.Tensor:
        """意味基底の構築"""
        # 事前学習済みword2vecやBERTの重みを模倣
        basis = torch.randn(self.dimension, self.dimension, device=self.device)
        
        # 正規直交化
        q, r = torch.linalg.qr(basis)
        return q
    
    def _create_stylistic_basis(self) -> torch.Tensor:
        """文体基底の構築"""
        # 文体特徴（語尾、語彙レベル、文長など）
        basis = torch.randn(self.dimension, 64, device=self.device)
        return F.normalize(basis, p=2, dim=1)
    
    def _create_emotional_basis(self) -> torch.Tensor:
        """感情基底の構築"""
        # Plutchikの感情環モデルを高次元に拡張
        basic_emotions = 8  # 基本感情の数
        emotional_components = torch.zeros(basic_emotions, self.dimension, device=self.device)
        
        # 各基本感情を円周上に配置（複素表現）
        for i in range(basic_emotions):
            angle = 2 * np.pi * i / basic_emotions
            emotional_components[i, :64] = torch.tensor([
                np.cos(angle), np.sin(angle)
            ] * 32, device=self.device)
        
        return emotional_components
    
    def _build_transformation_network(self) -> nn.Module:
        """表現変換ネットワーク"""
        return nn.Sequential(
            nn.Linear(self.dimension, self.dimension * 2),
            nn.LayerNorm(self.dimension * 2),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(self.dimension * 2, self.dimension * 2),
            nn.LayerNorm(self.dimension * 2),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(self.dimension * 2, self.dimension),
            nn.Tanh()
        ).to(self.device)
    
    def _build_quality_evaluator(self) -> nn.Module:
        """品質評価ネットワーク"""
        return nn.Sequential(
            nn.Linear(self.dimension, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 1),
            nn.Sigmoid()
        ).to(self.device)
    
    def encode_expression(self, text: str, character: str = None, 
                         context: str = None) -> ExpressionTensor:
        """表現をテンソル空間にエンコード"""
        # 簡単な特徴抽出（実際はBERTやGPTを使用）
        semantic_features = self._extract_semantic_features(text)
        stylistic_features = self._extract_stylistic_features(text, character)
        emotional_features = self._extract_emotional_features(text)
        character_features = self._extract_character_features(character or "unknown")
        context_features = self._extract_context_features(context or "")
        
        # テンソル構築
        semantic_tensor = torch.matmul(semantic_features, self.semantic_basis)
        stylistic_tensor = torch.matmul(stylistic_features, self.stylistic_basis)
        emotional_tensor = torch.matmul(emotional_features, self.emotional_basis)
        character_tensor = character_features
        context_tensor = context_features
        
        # 品質評価
        combined_features = semantic_tensor + stylistic_tensor * 0.5 + emotional_tensor * 0.3
        quality_score = self.quality_evaluator(combined_features).item()
        
        return ExpressionTensor(
            content=text,
            semantic_tensor=semantic_tensor,
            stylistic_tensor=stylistic_tensor,
            emotional_tensor=emotional_tensor,
            character_tensor=character_tensor,
            context_tensor=context_tensor,
            timestamp=time.time(),
            quality_score=quality_score
        )
    
    def _extract_semantic_features(self, text: str) -> torch.Tensor:
        """意味特徴の抽出"""
        # 簡単な実装（実際はより高度な手法を使用）
        words = text.split()
        features = torch.zeros(self.dimension, device=self.device)
        
        for i, word in enumerate(words[:self.dimension//4]):
            # 文字コードベースの簡単な特徴化
            char_sum = sum(ord(c) for c in word) % 1000
            features[i*4:(i+1)*4] = torch.tensor([
                char_sum / 1000.0,
                len(word) / 20.0,
                i / len(words),
                hash(word) % 1000 / 1000.0
            ], device=self.device)
        
        return F.normalize(features, p=2, dim=0)
    
    def _extract_stylistic_features(self, text: str, character: str) -> torch.Tensor:
        """文体特徴の抽出"""
        features = torch.zeros(64, device=self.device)
        
        # 基本統計
        features[0] = len(text) / 200.0  # 正規化された文長
        features[1] = len(text.split()) / 50.0  # 正規化された単語数
        features[2] = text.count('。') / 10.0  # 句点数
        features[3] = text.count('！') / 5.0   # 感嘆符数
        features[4] = text.count('？') / 5.0   # 疑問符数
        
        # キャラクター特徴
        if character:
            char_hash = hash(character) % 1000
            features[5:15] = torch.tensor([char_hash / 1000.0] * 10, device=self.device)
        
        # 語尾パターン
        endings = ['です', 'ます', 'だ', 'である', 'ね', 'よ', 'わ', 'の']
        for i, ending in enumerate(endings):
            features[16+i] = text.count(ending) / 5.0
        
        return F.normalize(features, p=2, dim=0)
    
    def _extract_emotional_features(self, text: str) -> torch.Tensor:
        """感情特徴の抽出"""
        # Plutchikの8基本感情
        emotion_keywords = {
            0: ['嬉しい', '楽しい', '幸せ', '喜び'],      # Joy
            1: ['信じる', '尊敬', '憧れ'],              # Trust  
            2: ['怖い', '不安', '心配'],                # Fear
            3: ['驚く', 'びっくり', '信じられない'],     # Surprise
            4: ['悲しい', '辛い', '寂しい'],            # Sadness
            5: ['嫌', '憎い', '腹立つ'],               # Disgust
            6: ['怒り', '腹立つ', 'むかつく'],          # Anger
            7: ['期待', '楽しみ', 'わくわく']           # Anticipation
        }
        
        emotion_scores = torch.zeros(8, device=self.device)
        for emotion_id, keywords in emotion_keywords.items():
            score = sum(text.count(keyword) for keyword in keywords)
            emotion_scores[emotion_id] = min(score / 3.0, 1.0)  # 正規化
        
        return emotion_scores
    
    def _extract_character_features(self, character: str) -> torch.Tensor:
        """キャラクター特徴の抽出"""
        features = torch.zeros(self.dimension, device=self.device)
        
        if character and character != "unknown":
            char_hash = hash(character)
            
            # キャラクター固有ベクトル
            for i in range(min(16, len(character))):
                features[i*16:(i+1)*16] = torch.tensor([
                    (char_hash >> (i*2)) & 0xFF
                ] * 16, device=self.device) / 255.0
        
        return F.normalize(features, p=2, dim=0)
    
    def _extract_context_features(self, context: str) -> torch.Tensor:
        """文脈特徴の抽出"""
        features = torch.zeros(self.dimension, device=self.device)
        
        if context:
            # 簡単な文脈特徴化
            context_words = context.split()
            for i, word in enumerate(context_words[:32]):
                features[i*8:(i+1)*8] = torch.tensor([
                    len(word) / 10.0,
                    hash(word) % 100 / 100.0
                ] * 4, device=self.device)
        
        return F.normalize(features, p=2, dim=0)


class NKATAdvancedProcessor:
    """NKAT高度処理システム（Phase 3実装）"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        
        # コアシステム
        self.algebra = NonCommutativeAlgebra(
            dimension=self.config.get('tensor_dimension', 256),
            device=self.device
        )
        self.expression_space = LiteraryExpressionSpace(self.config)
        
        # 最適化システム
        self.optimizer = torch.optim.AdamW([
            self.algebra.adaptation_matrix,
            self.algebra.commutator_weights
        ], lr=self.config.get('learning_rate', 0.001))
        
        # メトリクス
        self.performance_metrics = {
            'expressions_processed': 0,
            'quality_improvements': 0,
            'dimension_expansions': 0,
            'learning_iterations': 0,
            'average_quality_gain': 0.0
        }
        
        # 処理キャッシュ
        self.processing_cache = {}
        self.cache_lock = threading.Lock()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("🚀 NKAT Advanced Processor 初期化完了")
    
    def _default_config(self) -> Dict[str, Any]:
        """デフォルト設定"""
        return {
            'tensor_dimension': 256,
            'expression_dimension': 256,
            'learning_rate': 0.001,
            'quality_threshold': 0.7,
            'max_iterations': 10,
            'non_commutativity_strength': 0.3,
            'literary_enhancement': True,
            'realtime_adaptation': True,
            'cache_size': 1000,
            'device': 'cuda' if torch.cuda.is_available() else 'cpu'
        }
    
    def process_expression(self, text: str, character: str = None, 
                          context: str = None, target_quality: float = None) -> Tuple[str, Dict[str, Any]]:
        """表現の高度処理"""
        start_time = time.time()
        
        # キャッシュチェック
        cache_key = hash(f"{text}{character}{context}")
        with self.cache_lock:
            if cache_key in self.processing_cache:
                cached_result = self.processing_cache[cache_key]
                return cached_result['text'], cached_result['metrics']
        
        # 表現エンコーディング
        expression_tensor = self.expression_space.encode_expression(text, character, context)
        original_quality = expression_tensor.quality_score
        
        # 目標品質設定
        target_quality = target_quality or self.config.get('quality_threshold', 0.7)
        
        # 非可換テンソル処理
        enhanced_tensor = self._apply_noncommutative_transformation(expression_tensor)
        
        # 品質向上の反復処理
        iteration_count = 0
        max_iterations = self.config.get('max_iterations', 10)
        
        while (enhanced_tensor.quality_score < target_quality and 
               iteration_count < max_iterations):
            
            enhanced_tensor = self._iterative_quality_improvement(enhanced_tensor)
            iteration_count += 1
        
        # テンソルからテキストへのデコーディング
        enhanced_text = self._decode_expression(enhanced_tensor, text)
        
        # メトリクス計算
        processing_metrics = self._calculate_metrics(
            expression_tensor, enhanced_tensor, start_time, iteration_count
        )
        
        # キャッシュ保存
        with self.cache_lock:
            if len(self.processing_cache) < self.config.get('cache_size', 1000):
                self.processing_cache[cache_key] = {
                    'text': enhanced_text,
                    'metrics': processing_metrics
                }
        
        # 統計更新
        self._update_performance_metrics(processing_metrics)
        
        return enhanced_text, processing_metrics
    
    def _apply_noncommutative_transformation(self, expression_tensor: ExpressionTensor) -> ExpressionTensor:
        """非可換変換の適用"""
        # テンソル成分の非可換積
        semantic_enhanced = self.algebra.tensor_product(
            expression_tensor.semantic_tensor,
            expression_tensor.stylistic_tensor
        )
        
        # 指数写像による群作用
        tangent_vector = expression_tensor.emotional_tensor.unsqueeze(0)
        group_element = self.algebra.exponential_map(tangent_vector.squeeze(0))
        
        # 群作用による変換
        transformed_semantic = self.algebra.group_action(
            group_element, semantic_enhanced
        )
        
        # 新しいテンソル構築
        enhanced_tensor = ExpressionTensor(
            content=expression_tensor.content,
            semantic_tensor=transformed_semantic,
            stylistic_tensor=expression_tensor.stylistic_tensor,
            emotional_tensor=expression_tensor.emotional_tensor,
            character_tensor=expression_tensor.character_tensor,
            context_tensor=expression_tensor.context_tensor,
            timestamp=time.time(),
            quality_score=0.0  # 後で計算
        )
        
        # 品質再評価
        combined_features = (transformed_semantic + 
                           expression_tensor.stylistic_tensor * 0.5 + 
                           expression_tensor.emotional_tensor * 0.3)
        enhanced_tensor.quality_score = self.expression_space.quality_evaluator(
            combined_features
        ).item()
        
        return enhanced_tensor
    
    def _iterative_quality_improvement(self, expression_tensor: ExpressionTensor) -> ExpressionTensor:
        """反復的品質改善"""
        # 現在の品質を取得
        current_quality = expression_tensor.quality_score
        
        # 勾配ベースの改善
        with torch.enable_grad():
            # テンソル成分を学習可能にする
            semantic_tensor = expression_tensor.semantic_tensor.clone().requires_grad_(True)
            
            # 品質目標関数
            quality_pred = self.expression_space.quality_evaluator(semantic_tensor)
            quality_loss = -quality_pred  # 品質を最大化
            
            # 勾配計算
            quality_loss.backward()
            
            # 勾配ベースの更新
            with torch.no_grad():
                improvement_direction = semantic_tensor.grad
                step_size = self.config.get('learning_rate', 0.001)
                
                improved_semantic = semantic_tensor - step_size * improvement_direction
                improved_semantic = F.normalize(improved_semantic, p=2, dim=0)
        
        # 改善されたテンソル構築
        improved_tensor = ExpressionTensor(
            content=expression_tensor.content,
            semantic_tensor=improved_semantic,
            stylistic_tensor=expression_tensor.stylistic_tensor,
            emotional_tensor=expression_tensor.emotional_tensor,
            character_tensor=expression_tensor.character_tensor,
            context_tensor=expression_tensor.context_tensor,
            timestamp=time.time(),
            quality_score=0.0
        )
        
        # 品質再評価
        combined_features = (improved_semantic + 
                           expression_tensor.stylistic_tensor * 0.5 + 
                           expression_tensor.emotional_tensor * 0.3)
        improved_tensor.quality_score = self.expression_space.quality_evaluator(
            combined_features
        ).item()
        
        return improved_tensor
    
    def _decode_expression(self, expression_tensor: ExpressionTensor, 
                          original_text: str) -> str:
        """テンソルからテキストへのデコーディング"""
        # 品質向上度合いに基づく変換強度
        quality_improvement = expression_tensor.quality_score - 0.5  # 基準値0.5
        
        if quality_improvement < 0.1:
            return original_text  # 改善が少ない場合は元のまま
        
        # 簡単な改善手法（実際はより高度なデコーダーを使用）
        enhanced_text = self._apply_text_enhancements(
            original_text, expression_tensor, quality_improvement
        )
        
        return enhanced_text
    
    def _apply_text_enhancements(self, text: str, expression_tensor: ExpressionTensor, 
                                improvement_factor: float) -> str:
        """テキスト改善の適用"""
        enhanced_text = text
        
        # 感情強化
        emotional_strength = torch.max(expression_tensor.emotional_tensor).item()
        if emotional_strength > 0.5:
            enhanced_text = self._enhance_emotional_expression(enhanced_text, emotional_strength)
        
        # 文体調整
        stylistic_complexity = torch.norm(expression_tensor.stylistic_tensor).item()
        if stylistic_complexity > 0.3:
            enhanced_text = self._enhance_stylistic_variation(enhanced_text, stylistic_complexity)
        
        # 語彙多様化
        if improvement_factor > 0.3:
            enhanced_text = self._diversify_vocabulary(enhanced_text, improvement_factor)
        
        return enhanced_text
    
    def _enhance_emotional_expression(self, text: str, strength: float) -> str:
        """感情表現の強化"""
        # 感情語の強化辞書
        emotional_enhancements = {
            '嬉しい': ['とても嬉しい', 'すごく嬉しい', '心から嬉しい'],
            '悲しい': ['とても悲しい', 'すごく悲しい', '心が痛い'],
            '驚く': ['とても驚く', 'すごく驚く', '信じられない'],
            '怖い': ['とても怖い', 'すごく怖い', '心底怖い']
        }
        
        enhanced_text = text
        for base_emotion, enhanced_forms in emotional_enhancements.items():
            if base_emotion in text and strength > 0.6:
                enhancement = enhanced_forms[min(int(strength * 3), 2)]
                enhanced_text = enhanced_text.replace(base_emotion, enhancement)
        
        return enhanced_text
    
    def _enhance_stylistic_variation(self, text: str, complexity: float) -> str:
        """文体バリエーションの強化"""
        if complexity > 0.5:
            # 語尾のバリエーション
            if 'です。' in text:
                text = text.replace('です。', 'ですね。', 1)
            if 'ます。' in text:
                text = text.replace('ます。', 'ますよ。', 1)
        
        return text
    
    def _diversify_vocabulary(self, text: str, factor: float) -> str:
        """語彙多様化"""
        # 類義語辞書（簡単な例）
        synonyms = {
            'とても': ['すごく', 'かなり', '非常に', '大変'],
            'きれい': ['美しい', '素敵', '素晴らしい'],
            'いい': ['良い', '素晴らしい', '素敵', '優秀']
        }
        
        enhanced_text = text
        for original, alternatives in synonyms.items():
            if original in text and factor > 0.4:
                alternative = alternatives[hash(text) % len(alternatives)]
                enhanced_text = enhanced_text.replace(original, alternative, 1)
        
        return enhanced_text
    
    def _calculate_metrics(self, original: ExpressionTensor, enhanced: ExpressionTensor,
                          start_time: float, iterations: int) -> Dict[str, Any]:
        """メトリクス計算"""
        processing_time = time.time() - start_time
        quality_improvement = enhanced.quality_score - original.quality_score
        
        # テンソル空間メトリクス
        tensor_metrics = TensorSpaceMetrics(
            dimension=self.config.get('tensor_dimension', 256),
            rank=torch.matrix_rank(enhanced.semantic_tensor.unsqueeze(0)).item(),
            entropy=self._calculate_tensor_entropy(enhanced.semantic_tensor),
            coherence=self._calculate_coherence(original, enhanced),
            expressiveness=enhanced.quality_score,
            non_commutativity=self._calculate_non_commutativity(enhanced),
            literary_quality=self._calculate_literary_quality(enhanced)
        )
        
        return {
            'original_quality': original.quality_score,
            'enhanced_quality': enhanced.quality_score,
            'quality_improvement': quality_improvement,
            'processing_time_ms': processing_time * 1000,
            'iterations': iterations,
            'tensor_metrics': asdict(tensor_metrics),
            'system_efficiency': min(1.0, quality_improvement / max(processing_time, 0.001))
        }
    
    def _calculate_tensor_entropy(self, tensor: torch.Tensor) -> float:
        """テンソルエントロピーの計算"""
        eigenvalues = torch.linalg.eigvals(
            torch.matmul(tensor.unsqueeze(0), tensor.unsqueeze(1))
        ).real
        eigenvalues = F.softmax(eigenvalues, dim=0)
        entropy = -torch.sum(eigenvalues * torch.log(eigenvalues + 1e-8))
        return entropy.item()
    
    def _calculate_coherence(self, original: ExpressionTensor, 
                           enhanced: ExpressionTensor) -> float:
        """一貫性の計算"""
        semantic_coherence = F.cosine_similarity(
            original.semantic_tensor.unsqueeze(0),
            enhanced.semantic_tensor.unsqueeze(0)
        ).item()
        
        stylistic_coherence = F.cosine_similarity(
            original.stylistic_tensor.unsqueeze(0),
            enhanced.stylistic_tensor.unsqueeze(0)
        ).item()
        
        return (semantic_coherence + stylistic_coherence) / 2.0
    
    def _calculate_non_commutativity(self, tensor: ExpressionTensor) -> float:
        """非可換性の測定"""
        a = tensor.semantic_tensor.unsqueeze(0)
        b = tensor.stylistic_tensor.unsqueeze(0)
        
        commutator = torch.matmul(a, b.T) - torch.matmul(b.T, a)
        non_commutativity = torch.norm(commutator).item()
        
        return min(non_commutativity, 1.0)
    
    def _calculate_literary_quality(self, tensor: ExpressionTensor) -> float:
        """文学的品質の計算"""
        # 各要素の重み付き組み合わせ
        semantic_weight = 0.4
        stylistic_weight = 0.3
        emotional_weight = 0.3
        
        semantic_norm = torch.norm(tensor.semantic_tensor).item()
        stylistic_norm = torch.norm(tensor.stylistic_tensor).item()
        emotional_norm = torch.norm(tensor.emotional_tensor).item()
        
        literary_quality = (
            semantic_weight * semantic_norm +
            stylistic_weight * stylistic_norm +
            emotional_weight * emotional_norm
        )
        
        return min(literary_quality, 1.0)
    
    def _update_performance_metrics(self, processing_metrics: Dict[str, Any]):
        """パフォーマンスメトリクスの更新"""
        self.performance_metrics['expressions_processed'] += 1
        
        quality_improvement = processing_metrics['quality_improvement']
        if quality_improvement > 0.1:
            self.performance_metrics['quality_improvements'] += 1
        
        if processing_metrics['iterations'] > 1:
            self.performance_metrics['dimension_expansions'] += 1
        
        self.performance_metrics['learning_iterations'] += processing_metrics['iterations']
        
        # 平均品質向上の更新
        total_processed = self.performance_metrics['expressions_processed']
        current_avg = self.performance_metrics['average_quality_gain']
        new_avg = ((current_avg * (total_processed - 1)) + quality_improvement) / total_processed
        self.performance_metrics['average_quality_gain'] = new_avg
    
    def get_system_status(self) -> Dict[str, Any]:
        """システム状態の取得"""
        return {
            'device': self.device,
            'tensor_dimension': self.config.get('tensor_dimension', 256),
            'cache_size': len(self.processing_cache),
            'performance_metrics': self.performance_metrics,
            'algebra_parameters': {
                'adaptation_matrix_norm': torch.norm(self.algebra.adaptation_matrix).item(),
                'commutator_weights_mean': torch.mean(self.algebra.commutator_weights).item()
            }
        }
    
    def clear_cache(self):
        """キャッシュクリア"""
        with self.cache_lock:
            self.processing_cache.clear()
        self.logger.info("🧹 NKAT Advanced Processor キャッシュクリア完了")


def create_advanced_nkat_processor(config: Dict[str, Any] = None) -> NKATAdvancedProcessor:
    """NKAT高度プロセッサの作成"""
    return NKATAdvancedProcessor(config)


if __name__ == "__main__":
    # デモ実行
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 NKAT Advanced Tensor Processing System デモ")
    print("=" * 60)
    
    # システム初期化
    config = {
        'tensor_dimension': 128,  # デモ用に小さく設定
        'quality_threshold': 0.6,
        'max_iterations': 5,
        'literary_enhancement': True
    }
    
    processor = create_advanced_nkat_processor(config)
    
    # テストケース
    test_cases = [
        {
            'text': 'お兄ちゃんお兄ちゃん、どこに行くのですかお兄ちゃん？',
            'character': '妹キャラ',
            'context': '家族会話'
        },
        {
            'text': '嬉しいです。とても嬉しいです。本当に嬉しいです。',
            'character': '樹里',
            'context': '感情表現'
        },
        {
            'text': 'そうですね。そうですね。でも難しいですね。',
            'character': '美里',
            'context': '相槌会話'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 テストケース {i}")
        print(f"   キャラクター: {case['character']}")
        print(f"   原文: {case['text']}")
        
        enhanced_text, metrics = processor.process_expression(
            case['text'], case['character'], case['context']
        )
        
        print(f"   拡張後: {enhanced_text}")
        print(f"   品質改善: {metrics['quality_improvement']:.3f}")
        print(f"   処理時間: {metrics['processing_time_ms']:.1f}ms")
        print(f"   反復回数: {metrics['iterations']}")
        
        tensor_metrics = metrics['tensor_metrics']
        print(f"   テンソル次元: {tensor_metrics['dimension']}")
        print(f"   表現力: {tensor_metrics['expressiveness']:.3f}")
        print(f"   文学的品質: {tensor_metrics['literary_quality']:.3f}")
    
    # システム状態表示
    status = processor.get_system_status()
    print(f"\n📊 システム状態:")
    print(f"   処理数: {status['performance_metrics']['expressions_processed']}")
    print(f"   品質改善数: {status['performance_metrics']['quality_improvements']}")
    print(f"   平均品質向上: {status['performance_metrics']['average_quality_gain']:.3f}")
    print(f"   キャッシュサイズ: {status['cache_size']}")
    
    print("\n✅ NKAT Advanced Tensor Processing デモ完了") 