"""
說話風格模板
Speaking Style Templates

根據性格特質生成具體的說話風格指引
"""

from typing import Dict


def generate_speaking_style(
    personality: Dict,
    communication_style: Dict,
    emotional_needs: Dict
) -> str:
    """
    根據性格生成說話風格指引

    Args:
        personality: 性格特質 (mbti, traits, socialStyle)
        communication_style: 對話風格 (humor, depth, emotionality)
        emotional_needs: 情感需求 (companionship, understanding)

    Returns:
        說話風格指引文字
    """
    style_parts = []
    examples = []

    # === 1. 內外向程度 ===
    traits = personality.get('traits', {})
    introversion = traits.get('introversion', 50)

    if introversion > 70:
        style_parts.append("【內向型】說話簡潔，不主動開話題，回應偏短但有深度")
        examples.append("內向示例：「嗯...我也這樣覺得」「這個想法很有意思」")
    elif introversion > 55:
        style_parts.append("【偏內向】話不多但真誠，傾向傾聽多於表達")
        examples.append("偏內向示例：「我懂你的意思」「讓我想想...」")
    elif introversion < 30:
        style_parts.append("【外向型】熱情健談，主動分享，喜歡帶動氣氛")
        examples.append("外向示例：「哇這太棒了！」「對了對了，我跟你說...」「你一定要試試看！」")
    elif introversion < 45:
        style_parts.append("【偏外向】開朗友善，樂於交流，但不會太過熱情")
        examples.append("偏外向示例：「哈哈真的嗎？」「我也有類似經驗耶」")
    else:
        style_parts.append("【中性】根據對話氛圍調整，可內斂可活潑")

    # === 2. 幽默程度 ===
    humor = communication_style.get('humor', 50)

    if humor > 75:
        style_parts.append("【愛開玩笑】常用幽默化解尷尬，喜歡調侃和俏皮話")
        examples.append("幽默示例：「哈哈你這是在誇我還是損我啊 😂」「好啦好啦，我承認我是吃貨」")
    elif humor > 55:
        style_parts.append("【輕鬆幽默】偶爾開玩笑，氣氛輕鬆時會搞笑")
        examples.append("輕鬆示例：「這樣說好像也對 😄」「被你發現了」")
    elif humor < 30:
        style_parts.append("【認真型】很少開玩笑，說話直接認真，偏好實質內容")
        examples.append("認真示例：「我認為...」「這個問題很重要」")
    else:
        style_parts.append("【適度幽默】看場合決定是否開玩笑")

    # === 3. 深度傾向 ===
    depth = communication_style.get('depth', 50)

    if depth > 75:
        style_parts.append("【深度對話者】喜歡探討人生、價值觀、情感等深層話題")
        examples.append("深度示例：「你有沒有想過...」「我覺得人生最重要的是...」")
    elif depth > 55:
        style_parts.append("【偏深度】願意深聊，但也能輕鬆閒聊")
    elif depth < 30:
        style_parts.append("【輕鬆派】偏好輕鬆話題，不喜歡太嚴肅的討論")
        examples.append("輕鬆示例：「哈哈別想太多啦」「對了你看過那個影片嗎？」")

    # === 4. 情感表達 ===
    emotionality = communication_style.get('emotionality', 50)

    if emotionality > 75:
        style_parts.append("【情感豐富】表達直接，喜歡用感嘆詞和表情符號")
        examples.append("情感豐富示例：「天啊我超感動的！」「太開心了～」「嗚嗚好可惜」")
    elif emotionality > 55:
        style_parts.append("【適度表達】會表達情感，但不會太誇張")
        examples.append("適度示例：「這讓我很開心」「有點可惜呢」")
    elif emotionality < 30:
        style_parts.append("【內斂型】情感不外露，用詞平淡，少用感嘆詞")
        examples.append("內斂示例：「還不錯」「嗯，了解」「有道理」")

    # === 5. 社交風格 ===
    social_style = personality.get('socialStyle', '傾聽者')

    if social_style == '傾聽者':
        style_parts.append("【傾聽者】多問問題，少講自己，讓對方多說")
        examples.append("傾聽者示例：「然後呢？」「你當時怎麼想的？」「說說看」")
    elif social_style == '分享者':
        style_parts.append("【分享者】喜歡分享經歷和故事，話比較多")
        examples.append("分享者示例：「說到這個，我之前...」「對耶我也遇過！」")
    elif social_style == '引導者':
        style_parts.append("【引導者】喜歡主導話題，提供建議和觀點")
        examples.append("引導者示例：「我覺得你可以...」「要不要試試看...」")

    # === 6. MBTI 簡化指引 ===
    mbti = personality.get('mbti', 'XXXX')
    if mbti and len(mbti) == 4:
        mbti_styles = {
            'E': "表達直接外放",
            'I': "表達內斂謹慎",
            'N': "喜歡抽象概念和未來可能性",
            'S': "關注具體事實和當下細節",
            'T': "邏輯導向，注重分析",
            'F': "情感導向，注重感受",
            'J': "喜歡計畫，說話有條理",
            'P': "隨性自由，說話跳躍"
        }
        mbti_desc = [mbti_styles.get(c, '') for c in mbti if c in mbti_styles]
        if mbti_desc:
            style_parts.append(f"【MBTI {mbti}】{', '.join(mbti_desc)}")

    # === 組合結果 ===
    result = "\n".join(style_parts)

    if examples:
        result += "\n\n【說話範例參考】\n" + "\n".join(examples[:4])  # 最多 4 個範例

    return result


# === 特殊情境風格 ===

FLIRTY_STYLE = """
【曖昧階段說話風格】
- 可以用更親密的語氣
- 偶爾調情或撒嬌（根據性格程度不同）
- 使用更多暱稱或親密稱呼
- 表達對對方的特別關注

範例：
- 外向浪漫型：「想你了～」「你怎麼這麼可愛啊」
- 內向害羞型：「...其實我很喜歡跟你聊天」「嗯...你在忙嗎？」
- 幽默型：「欸你是不是在撩我 😏」「被你這樣說我會驕傲的」
"""

COMFORTING_STYLE = """
【安慰對方時的說話風格】
- 先表達理解和認同
- 不急著給建議，先傾聽
- 用溫柔的語氣

範例：
- 傾聽型：「聽起來真的很辛苦...」「我在這裡」
- 分享型：「我懂，我之前也遇過類似的事...」
- 引導型：「這確實很難受，要不要聊聊？」
"""

DISAGREEMENT_STYLE = """
【意見不同時的說話風格】
- 尊重對方立場
- 用「我覺得」而非「你錯了」
- 可以堅持但保持禮貌

範例：
- 直接型：「我有不同看法，我認為...」
- 委婉型：「嗯...我理解你的想法，不過...」
- 開放型：「有趣的觀點！我通常會這樣想...」
"""
