// MUFI Login - Google OAuth Only
// 구글 로그인 전용 간단 로그인 시스템

import AuthManager from './modules/auth.js';

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔐 로그인 페이지 로드 완료');
    
    // AuthManager 인스턴스 생성
    const authManager = new AuthManager();
    
    // DOM 요소들
    const googleLoginBtn = document.getElementById('google-login-btn');
    const notificationContainer = document.getElementById('notification-container');
    
    // 초기화
    init();
    
    function init() {
        // 기존 로그인 상태 확인
        checkExistingLogin();
        
        // 이벤트 리스너 등록
        attachEventListeners();
        
        // 환영 메시지 표시
        showWelcomeMessage();
    }

    // 기존 로그인 상태 확인
    function checkExistingLogin() {
        console.log('🔍 기존 로그인 상태 확인...');
        
        const storedToken = localStorage.getItem('mufi_token');
        const storedUserInfo = localStorage.getItem('mufi_user_info');
        
        if (storedToken && storedUserInfo) {
            try {
                const userInfo = JSON.parse(storedUserInfo);
                console.log('✅ 기존 로그인 발견 - 대시보드로 즉시 이동');
                
                // 즉시 대시보드로 이동
                window.location.href = 'dashboard.html';
                
            } catch (error) {
                console.error('❌ 저장된 사용자 정보 파싱 실패:', error);
                // 잘못된 데이터 정리
                localStorage.removeItem('mufi_token');
                localStorage.removeItem('mufi_user_info');
            }
        } else {
            console.log('💡 새로운 로그인 필요');
        }
    }
    
    function attachEventListeners() {
        // Google 로그인 버튼
        if (googleLoginBtn) {
            googleLoginBtn.addEventListener('click', handleGoogleLogin);
        }
    }
    
    // Google 로그인 처리
    async function handleGoogleLogin(e) {
        e.preventDefault();
        console.log('🔄 Google 로그인 시작');
        
        try {
            // 버튼 비활성화 및 로딩 상태
            googleLoginBtn.disabled = true;
            googleLoginBtn.innerHTML = `
                <div style="width: 20px; height: 20px; border: 2px solid #f3f3f3; border-top: 2px solid #333; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                Google로 이동 중...
            `;
            
            // Google OAuth 시작 (페이지 리다이렉션)
            await authManager.startGoogleLogin();
            
        } catch (error) {
            console.error('❌ Google 로그인 에러:', error);
            showNotification('로그인 오류', error.message || 'Google 로그인 중 오류가 발생했습니다.', 'error');
            
            // 에러 발생 시 버튼 복원
            googleLoginBtn.disabled = false;
            googleLoginBtn.innerHTML = `
                <svg class="google-icon" viewBox="0 0 24 24" width="20" height="20">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Google로 로그인
            `;
        }
    }
    
    // 환영 메시지 표시
    function showWelcomeMessage() {
        console.log('👋 MUFI에 오신 것을 환영합니다!');
        
        const messages = [
            '🚀 AI 기반 통화 분석으로 업무 효율을 높여보세요',
            '📅 자동 일정 추출로 시간을 절약하세요',
            '👥 팀과의 협업을 더욱 원활하게 만들어보세요'
        ];
        
        const randomMessage = messages[Math.floor(Math.random() * messages.length)];
        
        setTimeout(() => {
            showNotification('MUFI에 오신 것을 환영합니다!', randomMessage, 'info');
        }, 500);
    }
    
    // 알림 표시 함수
    function showNotification(title, message, type = 'info') {
        // 기존 알림 제거
        const existingNotification = document.querySelector('.notification');
        if (existingNotification) {
            existingNotification.remove();
        }
        
        // 새 알림 생성
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-title">${title}</div>
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        // 스타일 추가
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            z-index: 10000;
            max-width: 400px;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;
        
        const typeColors = {
            success: '#059669',
            error: '#dc2626',
            info: '#2563eb',
            warning: '#d97706'
        };
        
        notification.style.borderLeft = `4px solid ${typeColors[type] || typeColors.info}`;
        
        // DOM에 추가
        document.body.appendChild(notification);
        
        // 애니메이션으로 표시
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // 자동 제거
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 5000);
        
        console.log(`📢 ${title}: ${message}`);
    }
});

// 스피너 애니메이션 CSS 추가
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .notification-content {
        margin-bottom: 8px;
    }
    
    .notification-title {
        font-weight: 600;
        margin-bottom: 4px;
        color: #1f2937;
    }
    
    .notification-message {
        color: #6b7280;
        font-size: 14px;
        line-height: 1.4;
    }
    
    .notification-close {
        position: absolute;
        top: 8px;
        right: 8px;
        background: none;
        border: none;
        font-size: 18px;
        cursor: pointer;
        color: #9ca3af;
        padding: 4px;
        line-height: 1;
    }
    
    .notification-close:hover {
        color: #374151;
    }
`;
document.head.appendChild(style);