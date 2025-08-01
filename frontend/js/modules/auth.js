/**
 * MUFI Authentication Manager
 * 구글 로그인 및 사용자 인증 관리
 */

class AuthManager {
    constructor() {
        this.baseURL = 'http://localhost:8000';
        this.token = null;
        this.user = null;
        
        // 저장된 토큰 복원
        this.loadStoredAuth();
    }

    /**
     * 저장된 인증 정보 복원
     */
    loadStoredAuth() {
        // 토큰 만료 시간 체크
        const tokenExpiry = localStorage.getItem('mufi_token_expiry') || sessionStorage.getItem('mufi_token_expiry');
        
        if (tokenExpiry) {
            const expiryTime = new Date(tokenExpiry);
            const now = new Date();
            
            if (now > expiryTime) {
                console.log('🕒 토큰이 만료되었습니다. 로그인이 필요합니다.');
                this.clearAuth();
                return;
            }
        }
        
        // localStorage 또는 sessionStorage에서 토큰 복원
        this.token = localStorage.getItem('mufi_token') || sessionStorage.getItem('mufi_token');
        
        const userStr = localStorage.getItem('mufi_user_data') || sessionStorage.getItem('mufi_user_data');
        if (userStr) {
            try {
                this.user = JSON.parse(userStr);
            } catch (e) {
                console.error('Failed to parse user data:', e);
                this.clearAuth();
            }
        }
    }

    /**
     * 구글 로그인 시작 (리다이렉션 방식)
     */
    async startGoogleLogin() {
        try {
            console.log('🔄 Google OAuth URL 요청 중...');
            
            // 백엔드에서 구글 OAuth URL 가져오기
            const response = await fetch(`${this.baseURL}/auth/google/login`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('✅ Google OAuth URL 받음:', data);
            
            if (data.auth_url) {
                // 현재 페이지에서 Google OAuth로 리다이렉션
                console.log('🔄 Google OAuth 페이지로 이동...');
                window.location.href = data.auth_url;
                
                // 리다이렉션이므로 Promise 반환 (실제로는 페이지가 이동됨)
                return new Promise((resolve) => {
                    resolve({ success: true, redirecting: true });
                });
            } else {
                throw new Error('Google OAuth URL을 받지 못했습니다.');
            }
        } catch (error) {
            console.error('❌ Google 로그인 오류:', error);
            throw error;
        }
    }

    /**
     * 인증 콜백 처리 (URL 파라미터에서 코드 확인)
     */
    async handleAuthCallback() {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        
        if (code) {
            try {
                // 백엔드에 인증 코드 전송
                const response = await fetch(`${this.baseURL}/auth/google/callback?code=${code}`);
                const authData = await response.json();
                
                if (response.ok) {
                    return this.handleAuthSuccess(authData);
                } else {
                    throw new Error(authData.detail || 'Authentication failed');
                }
            } catch (error) {
                console.error('Auth callback error:', error);
                throw error;
            }
        }
    }

    /**
     * 인증 성공 처리
     */
    async handleAuthSuccess(authData) {
        try {
            this.token = authData.access_token;
            this.user = authData.user;
            
            // 로컬 스토리지에 저장 (기억하기 기능)
            const remember = localStorage.getItem('mufi_remember_login') === 'true';
            const storage = remember ? localStorage : sessionStorage;
            
            storage.setItem('mufi_token', this.token);
            storage.setItem('mufi_user_data', JSON.stringify(this.user));
            storage.setItem('mufi_logged_in', 'true');
            
            // 이벤트 발생
            this.dispatchAuthEvent('login', { user: this.user });
            
            return {
                success: true,
                user: this.user,
                message: authData.message || 'Login successful'
            };
        } catch (error) {
            console.error('Auth success handling error:', error);
            throw error;
        }
    }

    /**
     * 로그아웃
     */
    async logout() {
        try {
            // 백엔드에 로그아웃 요청
            if (this.token) {
                await fetch(`${this.baseURL}/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.token}`,
                        'Content-Type': 'application/json'
                    }
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            this.clearAuth();
            this.dispatchAuthEvent('logout');
        }
    }

    /**
     * 인증 정보 클리어
     */
    clearAuth() {
        this.token = null;
        this.user = null;
        
        // 모든 저장소에서 제거
        localStorage.removeItem('mufi_token');
        localStorage.removeItem('mufi_user_data');
        localStorage.removeItem('mufi_token_expiry');
        localStorage.removeItem('mufi_logged_in');
        sessionStorage.removeItem('mufi_token');
        sessionStorage.removeItem('mufi_user_data');
        sessionStorage.removeItem('mufi_token_expiry');
        sessionStorage.removeItem('mufi_logged_in');
    }

    /**
     * 현재 인증 상태 확인
     */
    async checkAuthStatus() {
        // 토큰 만료 시간 재확인
        const tokenExpiry = localStorage.getItem('mufi_token_expiry') || sessionStorage.getItem('mufi_token_expiry');
        if (tokenExpiry) {
            const expiryTime = new Date(tokenExpiry);
            const now = new Date();
            
            if (now > expiryTime) {
                console.log('🕒 토큰이 만료되어 로그아웃 처리합니다.');
                this.clearAuth();
                return { authenticated: false };
            }
            
            // 만료까지 남은 시간 표시
            const timeLeft = Math.round((expiryTime - now) / (1000 * 60 * 60)); // 시간 단위
            console.log(`⏰ 로그인 유효 시간: ${timeLeft}시간 남음`);
        }
        
        if (!this.token) {
            return { authenticated: false };
        }

        try {
            const response = await fetch(`${this.baseURL}/auth/status`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            const data = await response.json();
            
            if (response.ok && data.authenticated) {
                this.user = {
                    user_id: data.user_id,
                    email: data.email,
                    name: data.name,
                    picture: data.picture
                };
                return { authenticated: true, user: this.user };
            } else {
                this.clearAuth();
                return { authenticated: false };
            }
        } catch (error) {
            console.error('Auth status check error:', error);
            this.clearAuth();
            return { authenticated: false };
        }
    }

    /**
     * API 요청에 사용할 헤더 반환
     */
    getAuthHeaders() {
        if (!this.token) {
            return {};
        }
        
        return {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
        };
    }

    /**
     * 인증된 API 요청
     */
    async authenticatedFetch(url, options = {}) {
        const headers = {
            ...this.getAuthHeaders(),
            ...options.headers
        };

        const response = await fetch(url, {
            ...options,
            headers
        });

        // 401 에러 시 로그아웃 처리
        if (response.status === 401) {
            this.clearAuth();
            this.dispatchAuthEvent('unauthorized');
            window.location.href = '/login.html';
        }

        return response;
    }

    /**
     * 로그인 상태 확인
     */
    isAuthenticated() {
        return !!(this.token && this.user);
    }

    /**
     * 현재 사용자 정보 반환
     */
    getCurrentUser() {
        return this.user;
    }

    /**
     * 인증 이벤트 발생
     */
    dispatchAuthEvent(type, data = {}) {
        const event = new CustomEvent('authStateChange', {
            detail: { type, ...data }
        });
        window.dispatchEvent(event);
    }

    /**
     * 페이지 보호 (인증되지 않은 사용자 리디렉션)
     */
    requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = '/login.html';
            return false;
        }
        return true;
    }

    /**
     * 로그인 페이지 보호 (이미 로그인된 사용자 리디렉션)
     */
    redirectIfAuthenticated() {
        if (this.isAuthenticated()) {
            window.location.href = '/dashboard.html';
            return true;
        }
        return false;
    }
}

// 인증 상태 변경 이벤트 리스너
window.addEventListener('authStateChange', (event) => {
    const { type, user } = event.detail;
    
    switch (type) {
        case 'login':
            console.log('User logged in:', user);
            break;
        case 'logout':
            console.log('User logged out');
            break;
        case 'unauthorized':
            console.log('Unauthorized access detected');
            break;
    }
});

export default AuthManager; 