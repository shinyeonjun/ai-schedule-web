// MUFI 로그인 JavaScript
console.log('🔐 MUFI 로그인 페이지 로드됨');

// 로그인 객체
const login = {
    // 초기화
    init() {
        console.log('🚀 로그인 초기화 시작');
        this.setupEventListeners();
        this.checkAuthStatus();
        console.log('✅ 로그인 초기화 완료');
    },

    // 이벤트 리스너 설정
    setupEventListeners() {
        console.log('📝 이벤트 리스너 설정 중...');
        
        // 구글 로그인 버튼
        const googleLoginBtn = document.getElementById('google-login-btn');
        if (googleLoginBtn) {
            googleLoginBtn.addEventListener('click', () => {
                console.log('🖱️ 구글 로그인 버튼 클릭');
                this.handleGoogleLogin();
            });
        }

        // 페이지 로드 시 토큰 확인
        window.addEventListener('load', () => {
            this.checkUrlToken();
        });
    },

    // URL에서 토큰 확인 (OAuth 콜백 후)
    checkUrlToken() {
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');
        const inviteToken = urlParams.get('invite_token');
        
        // 초대 토큰 저장
        if (inviteToken) {
            console.log('🎫 초대 토큰 발견:', inviteToken);
            localStorage.setItem('pending_invite_token', inviteToken);
        }
        
        if (token) {
            console.log('🎫 URL에서 토큰 발견');
            this.handleAuthSuccess(token);
        }
    },

    // 구글 로그인 처리
    async handleGoogleLogin() {
        try {
            console.log('🔐 구글 로그인 시작');
            
            // 로딩 상태 표시
            this.showLoading('구글 로그인 중...');
            
            // 백엔드에서 구글 로그인 URL 가져오기
            const response = await fetch('/oauth/google/login');
            const data = await response.json();
            
            if (data.auth_url) {
                console.log('🔗 구글 인증 URL로 리다이렉트');
                window.location.href = data.auth_url;
            } else {
                throw new Error('인증 URL을 가져올 수 없습니다');
            }
            
        } catch (error) {
            console.error('❌ 구글 로그인 실패:', error);
            this.hideLoading();
            this.showNotification('로그인에 실패했습니다. 다시 시도해주세요.', 'error');
        }
    },

    // 인증 성공 처리
    handleAuthSuccess(token) {
        console.log('✅ 인증 성공');
        
        // 토큰을 로컬 스토리지에 저장
        localStorage.setItem('mufi_token', token);
        
        // URL에서 토큰 파라미터 제거
        const url = new URL(window.location);
        url.searchParams.delete('token');
        window.history.replaceState({}, document.title, url.pathname);
        
        // 대시보드로 리다이렉트
        this.redirectToDashboard();
    },

    // 대시보드로 리다이렉트
    redirectToDashboard() {
        // 초대 토큰이 있으면 초대 페이지로 리다이렉트
        const inviteToken = localStorage.getItem('pending_invite_token');
        if (inviteToken) {
            console.log('🎫 초대 토큰 발견, 초대 페이지로 리다이렉트');
            localStorage.removeItem('pending_invite_token');
            window.location.href = `/invite/${inviteToken}`;
            return;
        }
        
        console.log('📊 대시보드로 리다이렉트');
        window.location.href = '/dashboard';
    },

    // 인증 상태 확인
    async checkAuthStatus() {
        const token = localStorage.getItem('mufi_token');
        
        if (token) {
            try {
                console.log('🔍 토큰 검증 중...');
                
                const response = await fetch('/oauth/verify', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                const data = await response.json();
                
                if (data.valid) {
                    console.log('✅ 유효한 토큰 발견, 대시보드로 리다이렉트');
                    this.redirectToDashboard();
                } else {
                    console.log('❌ 유효하지 않은 토큰, 로컬 스토리지에서 제거');
                    localStorage.removeItem('mufi_token');
                }
                
            } catch (error) {
                console.error('❌ 토큰 검증 실패:', error);
                localStorage.removeItem('mufi_token');
            }
        }
    },

    // 로딩 표시
    showLoading(message = '처리 중...') {
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = `
            <div class="loading-content">
                <div class="loading-spinner"></div>
                <div class="loading-text">${message}</div>
            </div>
        `;
        
        document.body.appendChild(loadingOverlay);
        
        // CSS 스타일 추가
        const style = document.createElement('style');
        style.textContent = `
            .loading-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
            }
            
            .loading-content {
                background: #ffffff;
                padding: 30px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            }
            
            .loading-spinner {
                width: 40px;
                height: 40px;
                border: 3px solid #f3f3f3;
                border-top: 3px solid #000000;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 15px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .loading-text {
                font-size: 16px;
                font-weight: 500;
                color: #000000;
            }
        `;
        
        document.head.appendChild(style);
    },

    // 로딩 숨기기
    hideLoading() {
        const loadingOverlay = document.querySelector('.loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.remove();
        }
    },

    // 알림 표시
    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        if (!container) return;
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        container.appendChild(notification);
        
        // 5초 후 자동 제거
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
};

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM 로드 완료');
    login.init();
});

// 전역 객체로 노출
window.login = login;
