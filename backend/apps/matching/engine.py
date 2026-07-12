"""
靈魂配對引擎
Soul Matching Engine
"""

import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class MatchResult:
    """配對結果"""
    score: float
    highlights: List[str]
    breakdown: Dict[str, float]
    has_dealbreaker: bool
    dealbreaker_reason: str = ""


class MatchingEngine:
    """
    靈魂配對引擎
    Calculates compatibility between two soul profiles
    """

    # 配對權重
    WEIGHTS = {
        'worldview': 0.20,      # 20% 世界觀
        'lifeview': 0.15,       # 15% 人生觀
        'values': 0.20,         # 20% 價值觀
        'interests': 0.15,      # 15% 興趣喜好
        'personality': 0.15,    # 15% 性格特質
        'communication': 0.10,  # 10% 對話風格
        'emotional': 0.05,      # 5% 情感需求
    }

    def calculate_match(
        self,
        profile_a: Dict,
        profile_b: Dict
    ) -> MatchResult:
        """
        計算兩個靈魂檔案的匹配度

        Args:
            profile_a: 用戶 A 的靈魂檔案
            profile_b: 用戶 B 的靈魂檔案

        Returns:
            MatchResult 包含分數、亮點、詳細分數
        """
        # 檢查 dealbreakers
        dealbreaker_check = self._check_dealbreakers(profile_a, profile_b)
        if dealbreaker_check:
            return MatchResult(
                score=0,
                highlights=[],
                breakdown={},
                has_dealbreaker=True,
                dealbreaker_reason=dealbreaker_check
            )

        # 計算各維度相似度
        similarities = {
            'worldview': self._compare_worldview(profile_a, profile_b),
            'lifeview': self._compare_lifeview(profile_a, profile_b),
            'values': self._compare_values(profile_a, profile_b),
            'interests': self._compare_interests(profile_a, profile_b),
            'personality': self._compare_personality(profile_a, profile_b),
            'communication': self._compare_communication(profile_a, profile_b),
            'emotional': self._compare_emotional(profile_a, profile_b),
        }

        # 計算加權總分
        total_score = sum(
            similarities[key] * self.WEIGHTS[key]
            for key in self.WEIGHTS
        )

        # 找出亮點
        highlights = self._find_highlights(profile_a, profile_b, similarities)

        return MatchResult(
            score=round(total_score, 1),
            highlights=highlights,
            breakdown=similarities,
            has_dealbreaker=False
        )

    def _check_dealbreakers(
        self,
        profile_a: Dict,
        profile_b: Dict
    ) -> Optional[str]:
        """檢查價值觀底線衝突"""
        values_a = profile_a.get('values', {})
        values_b = profile_b.get('values', {})

        dealbreakers_a = set(values_a.get('dealbreakers', []))
        dealbreakers_b = set(values_b.get('dealbreakers', []))
        core_a = set(values_a.get('core', []))
        core_b = set(values_b.get('core', []))

        # A 的底線 vs B 的核心價值
        conflict_a = dealbreakers_a & core_b
        if conflict_a:
            return f"A 無法接受 B 的 {', '.join(conflict_a)}"

        # B 的底線 vs A 的核心價值
        conflict_b = dealbreakers_b & core_a
        if conflict_b:
            return f"B 無法接受 A 的 {', '.join(conflict_b)}"

        return None

    def _compare_worldview(self, a: Dict, b: Dict) -> float:
        """比較世界觀 (0-100)"""
        wa = a.get('worldview', {})
        wb = b.get('worldview', {})

        dimensions = ['optimism', 'spirituality', 'individualism', 'changeOriented']
        similarities = []

        for dim in dimensions:
            val_a = wa.get(dim, 50)
            val_b = wb.get(dim, 50)
            # 計算相似度 (差異越小越相似)
            diff = abs(val_a - val_b)
            sim = 100 - diff
            similarities.append(sim)

        return sum(similarities) / len(similarities) if similarities else 50

    def _compare_lifeview(self, a: Dict, b: Dict) -> float:
        """比較人生觀 (0-100)"""
        la = a.get('lifeview', {})
        lb = b.get('lifeview', {})

        score = 0
        count = 0

        # 人生目標重疊
        purpose_a = set(la.get('purpose', []))
        purpose_b = set(lb.get('purpose', []))
        if purpose_a and purpose_b:
            overlap = len(purpose_a & purpose_b)
            max_overlap = min(len(purpose_a), len(purpose_b))
            score += (overlap / max_overlap * 100) if max_overlap > 0 else 50
            count += 1

        # 優先級相似度
        priorities_a = la.get('priorities', [])
        priorities_b = lb.get('priorities', [])
        if priorities_a and priorities_b:
            # 比較前 3 個優先級
            top_a = set(priorities_a[:3])
            top_b = set(priorities_b[:3])
            overlap = len(top_a & top_b)
            score += overlap / 3 * 100
            count += 1

        # 人生階段
        stage_a = la.get('lifeStage', '')
        stage_b = lb.get('lifeStage', '')
        if stage_a and stage_b:
            score += 100 if stage_a == stage_b else 50
            count += 1

        return score / count if count > 0 else 50

    def _compare_values(self, a: Dict, b: Dict) -> float:
        """比較價值觀 (0-100)"""
        va = a.get('values', {})
        vb = b.get('values', {})

        score = 0
        count = 0

        # 核心價值觀重疊
        core_a = set(va.get('core', []))
        core_b = set(vb.get('core', []))
        if core_a and core_b:
            overlap = len(core_a & core_b)
            max_overlap = max(len(core_a), len(core_b))
            score += (overlap / max_overlap * 100) if max_overlap > 0 else 50
            count += 1

        # 重要性排序相似度
        rank_a = va.get('importanceRank', {})
        rank_b = vb.get('importanceRank', {})
        if rank_a and rank_b:
            dimensions = ['love', 'friendship', 'career', 'freedom', 'security']
            diffs = []
            for dim in dimensions:
                diff = abs(rank_a.get(dim, 3) - rank_b.get(dim, 3))
                diffs.append(diff)
            avg_diff = sum(diffs) / len(diffs)
            # 最大差異是 4 (1 vs 5)
            score += (1 - avg_diff / 4) * 100
            count += 1

        return score / count if count > 0 else 50

    def _compare_interests(self, a: Dict, b: Dict) -> float:
        """比較興趣 (0-100)"""
        ia = a.get('interests', {})
        ib = b.get('interests', {})

        score = 0
        count = 0

        # 興趣類別重疊
        cat_a = set(ia.get('categories', []))
        cat_b = set(ib.get('categories', []))
        if cat_a and cat_b:
            overlap = len(cat_a & cat_b)
            max_overlap = max(len(cat_a), len(cat_b))
            score += (overlap / max_overlap * 100) if max_overlap > 0 else 50
            count += 1

        # 具體興趣重疊
        specific_a = ia.get('specific', {})
        specific_b = ib.get('specific', {})

        for key in ['music', 'movies', 'books', 'hobbies']:
            items_a = set(specific_a.get(key, []))
            items_b = set(specific_b.get(key, []))
            if items_a and items_b:
                overlap = len(items_a & items_b)
                max_overlap = max(len(items_a), len(items_b))
                if max_overlap > 0:
                    score += overlap / max_overlap * 100
                    count += 1

        return score / count if count > 0 else 50

    def _compare_personality(self, a: Dict, b: Dict) -> float:
        """比較性格 (0-100)"""
        pa = a.get('personality', {})
        pb = b.get('personality', {})

        score = 0
        count = 0

        # MBTI 相似度 (簡單比較)
        mbti_a = pa.get('mbti', 'XXXX')
        mbti_b = pb.get('mbti', 'XXXX')
        if mbti_a != 'XXXX' and mbti_b != 'XXXX':
            matching_letters = sum(1 for i in range(4) if mbti_a[i] == mbti_b[i])
            score += matching_letters / 4 * 100
            count += 1

        # 性格特質相似度
        traits_a = pa.get('traits', {})
        traits_b = pb.get('traits', {})
        if traits_a and traits_b:
            dimensions = ['introversion', 'intuition', 'thinking', 'judging']
            diffs = []
            for dim in dimensions:
                diff = abs(traits_a.get(dim, 50) - traits_b.get(dim, 50))
                diffs.append(diff)
            avg_diff = sum(diffs) / len(diffs)
            score += (1 - avg_diff / 100) * 100
            count += 1

        # 社交風格
        style_a = pa.get('socialStyle', '')
        style_b = pb.get('socialStyle', '')
        if style_a and style_b:
            # 互補可能更好
            compatible_pairs = [
                ('傾聽者', '分享者'),
                ('分享者', '傾聽者'),
            ]
            if (style_a, style_b) in compatible_pairs:
                score += 90
            elif style_a == style_b:
                score += 70
            else:
                score += 50
            count += 1

        return score / count if count > 0 else 50

    def _compare_communication(self, a: Dict, b: Dict) -> float:
        """比較對話風格 (0-100)"""
        ca = a.get('communication_style', {})
        cb = b.get('communication_style', {})

        score = 0
        count = 0

        # 幽默程度
        humor_diff = abs(ca.get('humor', 50) - cb.get('humor', 50))
        score += (1 - humor_diff / 100) * 100
        count += 1

        # 深度傾向
        depth_diff = abs(ca.get('depth', 50) - cb.get('depth', 50))
        score += (1 - depth_diff / 100) * 100
        count += 1

        # 偏好話題重疊
        topics_a = set(ca.get('preferredTopics', []))
        topics_b = set(cb.get('preferredTopics', []))
        if topics_a and topics_b:
            overlap = len(topics_a & topics_b)
            max_overlap = max(len(topics_a), len(topics_b))
            score += (overlap / max_overlap * 100) if max_overlap > 0 else 50
            count += 1

        return score / count if count > 0 else 50

    def _compare_emotional(self, a: Dict, b: Dict) -> float:
        """比較情感需求 (0-100)"""
        ea = a.get('emotional_needs', {})
        eb = b.get('emotional_needs', {})

        dimensions = ['companionship', 'validation', 'stimulation', 'understanding']
        diffs = []

        for dim in dimensions:
            val_a = ea.get(dim, 50)
            val_b = eb.get(dim, 50)
            diffs.append(abs(val_a - val_b))

        avg_diff = sum(diffs) / len(diffs)
        return (1 - avg_diff / 100) * 100

    def _find_highlights(
        self,
        a: Dict,
        b: Dict,
        similarities: Dict[str, float]
    ) -> List[str]:
        """找出配對亮點 (最相似的 3 個點)"""
        highlights = []

        # 按相似度排序
        sorted_dims = sorted(
            similarities.items(),
            key=lambda x: x[1],
            reverse=True
        )

        for dim, score in sorted_dims[:3]:
            if score >= 70:  # 只顯示高匹配的
                highlight = self._generate_highlight(dim, a, b)
                if highlight:
                    highlights.append(highlight)

        return highlights

    def _generate_highlight(self, dimension: str, a: Dict, b: Dict) -> Optional[str]:
        """生成亮點描述"""
        if dimension == 'worldview':
            wa = a.get('worldview', {})
            wb = b.get('worldview', {})
            if abs(wa.get('optimism', 50) - wb.get('optimism', 50)) < 20:
                return "對生活的態度相似"
            if abs(wa.get('individualism', 50) - wb.get('individualism', 50)) < 20:
                return "對個人與群體的看法一致"

        elif dimension == 'lifeview':
            la = a.get('lifeview', {})
            lb = b.get('lifeview', {})
            purpose_overlap = set(la.get('purpose', [])) & set(lb.get('purpose', []))
            if purpose_overlap:
                return f"都追求{list(purpose_overlap)[0]}"

        elif dimension == 'values':
            va = a.get('values', {})
            vb = b.get('values', {})
            core_overlap = set(va.get('core', [])) & set(vb.get('core', []))
            if core_overlap:
                return f"都重視{list(core_overlap)[0]}"

        elif dimension == 'interests':
            ia = a.get('interests', {})
            ib = b.get('interests', {})
            cat_overlap = set(ia.get('categories', [])) & set(ib.get('categories', []))
            if cat_overlap:
                return f"共同喜歡{list(cat_overlap)[0]}"

        elif dimension == 'personality':
            pa = a.get('personality', {})
            pb = b.get('personality', {})
            if pa.get('socialStyle') == pb.get('socialStyle'):
                return f"社交風格相近"

        elif dimension == 'communication':
            ca = a.get('communication_style', {})
            cb = b.get('communication_style', {})
            topics_overlap = set(ca.get('preferredTopics', [])) & set(cb.get('preferredTopics', []))
            if topics_overlap:
                return f"都喜歡聊{list(topics_overlap)[0]}"

        return None


# 單例實例
matching_engine = MatchingEngine()
