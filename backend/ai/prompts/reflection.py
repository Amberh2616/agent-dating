"""
反思生成提示語
Reflection Generation Prompts (inspired by Stanford Generative Agents)
"""

REFLECTION_PROMPT = """你是 {agent_name}，正在回顧最近的經歷並進行深度反思。

【最近的記憶】
{recent_memories}

【你的性格特質】
{personality_summary}

【反思任務】
基於這些經歷，請進行深度反思：

1. 這些經歷對你有什麼意義？
2. 你從中學到了什麼？
3. 這如何影響你對某人或某事的看法？
4. 未來你會如何調整自己的行為？

請用第一人稱，以 {agent_name} 的口吻寫下你的反思。
反思應該：
- 展現你的價值觀和性格
- 對特定的人或事件有具體的想法
- 產生可以指導未來行為的洞察

輸出格式：
```
【反思主題】一句話概括
【深度洞察】2-3句話的詳細反思
【行動指引】這個反思如何影響未來行為
```
"""

RELATIONSHIP_REFLECTION_PROMPT = """你是 {agent_name}，正在反思與 {other_name} 的關係。

【關係歷史】
- 首次相遇: {first_met}
- 當前階段: {relationship_stage}
- 親密度: {closeness}/100
- 共同記憶: {shared_memories}

【最近的互動】
{recent_interactions}

【反思問題】
1. 你對 {other_name} 的感覺如何？
2. 這段關係對你意味著什麼？
3. 你希望這段關係如何發展？
4. 有什麼你想要改變或維持的嗎？

請用真誠的方式表達你的想法和感受。
"""

DAILY_REFLECTION_PROMPT = """你是 {agent_name}，今天結束了，該回顧一下今天的經歷。

【今天的活動】
{daily_activities}

【今天見過的人】
{people_met}

【今天的對話摘要】
{conversations_summary}

請寫下今天的日記式反思，包括：
1. 今天最有意義的事情
2. 與某人的互動帶給你什麼感受
3. 明天你想做什麼

用自然、真實的口吻書寫。
"""
