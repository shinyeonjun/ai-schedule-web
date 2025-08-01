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
     * 구글 로그인 시작
     */
    async startGoogleLogin() {
        try {
            // 백엔드에서 구글 OAuth URL 가져오기
            const response = await fetch(`${this.baseURL}/auth/google/login`);
            const data = await response.json();
            
            if (data.auth_url) {
                // 팝업으로 구글 로그인 창 열기
                const popup = window.open(
                    data.auth_url,
                    'googleLogin',
                    'width=500,height=600,scrollbars=yes,resizable=yes'
                );

                // 팝업에서 인증 완료 대기
                return new Promise((resolve, reject) => {
                    const checkClosed = setInterval(() => {
                        if (popup.closed) {
                            clearInterval(checkClosed);
                            // 팝업이 닫힌 후 인증 상태 확인
                            this.handleAuthCallback()
                                .then(resolve)
                                .catch(reject);
                        }
                    }, 1000);

                    // 메시지 리스너 추가 (팝업에서 메시지 받기)
                    const messageListener = (event) => {
                        if (event.origin !== window.location.origin) return;
                        
                        if (event.data.type === 'GOOGLE_AUTH_SUCCESS') {
                            clearInterval(checkClosed);
                            window.removeEventListener('message', messageListener);
                            popup.close();
                            
                            this.handleAuthSuccess(event.data.authData)
                                .then(resolve)
                                .catch(reject);
                        } else if (event.data.type === 'GOOGLE_AUTH_ERROR') {
                            clearInterval(checkClosed);
                            window.removeEventListener('message', messageListener);
                            popup.close();
                            reject(new Error(event.data.error));
                        }
                    };
                    
                    window.addEventListener('message', messageListener);
                });
            } else {
                throw new Error('Failed to get Google OAuth URL');
            }
        } catch (error) {
            console.error('Google login error:', error);
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
        localStorage.removeItem('mufi_logged_in');
        sessionStorage.removeItem('mufi_token');
        sessionStorage.removeItem('mufi_user_data');
        sessionStorage.removeItem('mufi_logged_in');
    }

    /**
     * 현재 인증 상태 확인
     */
    async checkAuthStatus() {
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

// 전역 AuthManager 인스턴스 생성
window.authManager = new AuthManager();

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