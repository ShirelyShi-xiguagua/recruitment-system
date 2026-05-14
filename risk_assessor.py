import json
import streamlit as st
from api_client import call_api, parse_json_response
from typing import Dict, List, Any, Tuple


def assess_match_and_risks(talent_profile: Dict[str, Any], resume_profile: Dict[str, Any]) -> Dict[str, Any]:
    prompt = f"""请基于以下两个人才画像，评估简历与岗位的匹配度和风险。

岗位人才画像：
{json.dumps(talent_profile, ensure_ascii=False, indent=2)}

简历人才画像：
{json.dumps(resume_profile, ensure_ascii=False, indent=2)}

请严格按以下JSON格式返回（不要添加任何其他文字，只返回JSON）：

{{
    "match_score": 75,
    "match_trend": "稳定",
    "match_details": [
        {{"dimension": "技能匹配", "score": 85, "comment": "具体评价"}},
        {{"dimension": "经验匹配", "score": 70, "comment": "具体评价"}},
        {{"dimension": "教育背景", "score": 80, "comment": "具体评价"}},
        {{"dimension": "软技能匹配", "score": 75, "comment": "具体评价"}}
    ],
    "risk_level": "低",
    "risks": [{{"category": "风险类别", "description": "风险描述", "severity": "高"}}],
    "strengths": ["优势1", "优势2"],
    "recommendation": "推荐/谨慎考虑/不推荐",
    "key_concerns": ["关注点1"],
    "suggestions": ["建议1"]
}}"""

    try:
        result_text = call_api(prompt, max_tokens=2000)
        return parse_json_response(result_text)
    except json.JSONDecodeError:
        return _calculate_match_score(talent_profile, resume_profile)
    except Exception as e:
        st.warning(f"AI评估失败，使用本地评估: {e}")
        return _calculate_match_score(talent_profile, resume_profile)


def _calculate_match_score(tp: Dict, rp: Dict) -> Dict:
    details = []
    req = set(s.lower() for s in tp.get("required_skills", []))
    have = set(s.lower() for s in rp.get("skills", {}).get("technical_skills", []))
    sk = int((len(req & have) / len(req)) * 100) if req else 80
    details.append({"dimension": "技能匹配", "score": sk, "comment": f"匹配 {len(req & have)}/{len(req)} 项"})

    ry, hy = tp.get("experience_years", 0), rp.get("total_experience_years", 0)
    es = min(100, 80 + (hy - ry) * 5) if hy >= ry else max(30, int((hy / ry) * 80)) if ry else 80
    details.append({"dimension": "经验匹配", "score": es, "comment": f"{hy}年 vs 要求{ry}年"})

    details.append({"dimension": "教育背景", "score": 80, "comment": "待评估"})
    details.append({"dimension": "软技能匹配", "score": 75, "comment": "待评估"})

    final = int(sum(d["score"] * w for d, w in zip(details, [0.4, 0.3, 0.15, 0.15])))
    rl = "低" if final >= 80 else "中" if final >= 60 else "高"
    risks = [{"category": d["dimension"], "description": d["comment"], "severity": "高" if d["score"] < 50 else "中"} for d in details if d["score"] < 70]

    return {
        "match_score": final, "match_trend": "稳定", "match_details": details,
        "risk_level": rl, "risks": risks,
        "strengths": [d["comment"] for d in details if d["score"] >= 80] or ["暂未发现突出优势"],
        "recommendation": "推荐" if final >= 70 else "谨慎考虑" if final >= 50 else "不推荐",
        "key_concerns": [d["dimension"] for d in details if d["score"] < 70],
        "suggestions": []
    }
