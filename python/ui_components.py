"""
Zeniji Emotion Simul - UI Components
UI 컴포넌트 생성 (차트, 모달 등)
"""

import logging
from typing import Dict, Optional
import plotly.graph_objects as go

logger = logging.getLogger("UIComponents")


class UIComponents:
    """UI 컴포넌트 생성 클래스"""
    
    @staticmethod
    def create_radar_chart(stats: Dict[str, float], deltas: Optional[Dict[str, float]] = None, labels: Optional[Dict[str, any]] = None) -> go.Figure:
        """6축 수치를 위한 radar chart 생성"""
        keys = ['P', 'A', 'D', 'I', 'T', 'Dep']
        default_categories = ['P (쾌락)', 'A (각성)', 'D (지배)', 'I (친밀)', 'T (신뢰)', 'Dep (의존)']
        categories = (labels or {}).get("categories", default_categories)
        current_name = (labels or {}).get("current_name", "현재 수치")
        delta_name = (labels or {}).get("delta_name", "변화 후")
        
        values = [stats.get(key, 0.0) for key in keys]
        
        fig = go.Figure()
        
        # 메인 값
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=current_name,
            line_color='rgb(32, 201, 151)',
            fillcolor='rgba(32, 201, 151, 0.3)'
        ))
        
        # Delta가 있으면 표시
        if deltas:
            delta_values = [deltas.get(key, 0.0) for key in keys]
            # Delta를 현재 값에 더한 값으로 표시 (변화량 시각화)
            delta_display = [values[i] + delta_values[i] for i in range(len(values))]
            fig.add_trace(go.Scatterpolar(
                r=delta_display,
                theta=categories,
                fill='toself',
                name=delta_name,
                line_color='rgb(255, 99, 71)',
                fillcolor='rgba(255, 99, 71, 0.2)',
                line_dash='dash'
            ))
        
        fig.update_layout(
            polar=dict(
                domain=dict(x=[0.05, 0.95], y=[0.05, 0.95]),  # 차트 본체를 미세하게 축소
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(size=9)
                ),
                angularaxis=dict(
                    tickfont=dict(size=10)
                )
            ),
            showlegend=False,
            height=320,
            width=320,  # 세로가 긴 박스라면 가로폭도 명시적으로 지정
            margin=dict(l=50, r=50, t=40, b=40)  # 좌우 여백을 더 확보
        )
        
        return fig
    
    @staticmethod
    def create_single_notification(event_type: str, event_data: dict, top_offset: int = 20) -> str:
        """단일 이벤트 알림 HTML 생성"""
        emoji_map = {
            "jackpot": "🎰",
            "surprise": "✨",
            "badge": "🏆",
            "Lover": "💕",
            "Partner": "💍",
            "Divorce": "💔",
            "Tempted": "😈",
            "slave": "🔗",
            "master": "👑",
            "fiancee": "💐",
            "breakup": "😢"
        }
        
        title_map = {
            "jackpot": "극진한 반응!",
            "surprise": "놀라운 반응!",
            "badge": "뱃지 획득!",
            "Lover": "관계 발전!",
            "Partner": "결혼!",
            "Divorce": "이혼",
            "Tempted": "유혹",
            "slave": "노예",
            "master": "주인",
            "fiancee": "약혼",
            "breakup": "이별"
        }
        
        emoji = emoji_map.get(event_type, "🎉")
        title = title_map.get(event_type, "이벤트 발생!")
        
        if event_type == "badge":
            message = f"<strong>{event_data.get('badge_name', '')}</strong> 뱃지를 획득했습니다!"
        elif isinstance(event_type, str) and event_type.lower() in ["lover", "partner", "fiancee", "tempted", "slave", "master"]:
            message = f"관계가 <strong>{event_data.get('new_status', event_type)}</strong>로 발전했습니다!"
        elif isinstance(event_type, str) and event_type.lower() in ["divorce", "breakup"]:
            message = f"관계가 <strong>{event_data.get('new_status', event_type)}</strong>로 변경되었습니다."
        else:
            message = event_data.get('message', '특별한 이벤트가 발생했습니다!')
        
        # 뱃지는 더 강조된 색상 사용
        if event_type == "badge":
            background = "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
        else:
            background = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        
        notification_html = f"""
        <div class="event-notification" style="
            position: fixed;
            top: {top_offset}px;
            right: 20px;
            background: {background};
            color: white;
            padding: 25px 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            max-width: 400px;
            animation: slideInRight 0.5s ease-out, fadeOut 0.5s ease-in 7.5s;
            animation-fill-mode: forwards;
        ">
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="font-size: 48px; line-height: 1;">{emoji}</div>
                <div style="flex: 1;">
                    <h3 style="margin: 0 0 8px 0; font-size: 20px; font-weight: bold;">{title}</h3>
                    <p style="margin: 0; font-size: 14px; opacity: 0.95; line-height: 1.4;">{message}</p>
                </div>
            </div>
        </div>
        """
        return notification_html
    
    @staticmethod
    def create_event_notification(event_type: str, event_data: dict) -> str:
        """이벤트 알림 HTML 생성 (단일 알림, 하위 호환성용)"""
        return UIComponents.create_multiple_notifications([(event_type, event_data)])
    
    @staticmethod
    def create_multiple_notifications(events: list) -> str:
        """여러 이벤트 알림 HTML 생성 (각각 다른 위치에 배치)"""
        if not events:
            return ""
        
        notifications = []
        top_offset = 20  # 첫 번째 알림의 top 위치
        
        for event_type, event_data in events:
            notification = UIComponents.create_single_notification(event_type, event_data, top_offset)
            notifications.append(notification)
            top_offset += 180  # 다음 알림을 아래로 배치 (알림 높이 + 간격)
        
        # CSS는 한 번만 포함
        style_html = """
        <style>
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            @keyframes fadeOut {
                from {
                    opacity: 1;
                    transform: translateX(0);
                }
                to {
                    opacity: 0;
                    transform: translateX(100%);
                }
            }
        </style>
        """
        
        return style_html + "".join(notifications)

