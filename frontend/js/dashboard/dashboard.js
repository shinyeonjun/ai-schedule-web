// MUFI Dashboard JavaScript
console.log('🎯 MUFI Dashboard 로드됨');

// 대시보드 객체
const dashboard = {
    // 초기화
    init() {
        console.log('🚀 대시보드 초기화 시작');
        this.checkAuth();
        this.setupEventListeners();
        this.loadUserInfo();
        this.setupNavigation();
        console.log('✅ 대시보드 초기화 완료');
    },

    // 인증 상태 확인
    async checkAuth() {
        const token = localStorage.getItem('mufi_token');
        
        // URL에서 토큰 확인 (OAuth 콜백 후)
        const urlParams = new URLSearchParams(window.location.search);
        const urlToken = urlParams.get('token');
        
        if (urlToken) {
            console.log('🎫 URL에서 토큰 발견, localStorage에 저장');
            localStorage.setItem('mufi_token', urlToken);
            
            // URL에서 토큰 파라미터 제거
            const url = new URL(window.location);
            url.searchParams.delete('token');
            window.history.replaceState({}, document.title, url.pathname);
        }
        
        const finalToken = localStorage.getItem('mufi_token');
        
        if (!finalToken) {
            console.log('❌ 토큰 없음, 로그인 페이지로 리다이렉트');
            
            // 토큰이 없어도 인증 완료 이벤트 발생 (로그인 페이지로 리다이렉트 전)
            document.dispatchEvent(new CustomEvent('mufi-auth-completed', {
                detail: { userData: null }
            }));
            
            window.location.href = '/login';
            return;
        }

        try {
            console.log('🔍 토큰 검증 중...');
            
            const response = await fetch('/oauth/verify', {
                headers: {
                    'Authorization': `Bearer ${finalToken}`
                }
            });
            
            const data = await response.json();
            
            if (!data.valid) {
                console.log('❌ 유효하지 않은 토큰, 로그인 페이지로 리다이렉트');
                localStorage.removeItem('mufi_token');
                window.location.href = '/login';
                return;
            }
            
            console.log('✅ 인증 성공');
            
            // 인증 완료 후 이벤트 발생
            document.dispatchEvent(new CustomEvent('mufi-auth-completed', {
                detail: { userData: data.user }
            }));
            
        } catch (error) {
            console.error('❌ 토큰 검증 실패:', error);
            localStorage.removeItem('mufi_token');
            window.location.href = '/login';
        }
    },

    // 이벤트 리스너 설정
    setupEventListeners() {
        console.log('📝 이벤트 리스너 설정 중...');
        
        // 네비게이션 링크들
        const navLinks = document.querySelectorAll('.nav-link');
        console.log(`📋 네비게이션 링크 개수: ${navLinks.length}`);
        
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.dataset.section;
                console.log(`🖱️ 네비게이션 클릭: ${section}`);
                this.switchSection(section);
            });
        });

        // 로그아웃 버튼
        const logoutBtn = document.querySelector('.logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                this.handleLogout();
            });
        }

        // 사용자 메뉴 토글
        const userMenuToggle = document.querySelector('.user-menu-toggle');
        const userMenu = document.querySelector('.user-menu');
        
        if (userMenuToggle && userMenu) {
            userMenuToggle.addEventListener('click', () => {
                userMenu.classList.toggle('show');
            });

            // 메뉴 외부 클릭 시 닫기
            document.addEventListener('click', (e) => {
                if (!userMenuToggle.contains(e.target) && !userMenu.contains(e.target)) {
                    userMenu.classList.remove('show');
                }
            });
        }
    },

    // 섹션 전환
    switchSection(sectionName) {
        console.log(`🔄 섹션 전환: ${sectionName}`);
        
        // 로딩 오버레이 숨기기
        this.hideLoadingOverlay();
        
        // 모든 섹션 숨기기
        const sections = document.querySelectorAll('.content-section');
        sections.forEach(section => {
            section.classList.remove('active');
            section.style.display = 'none';
        });
        
        // 모든 네비게이션 링크 비활성화
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.classList.remove('active');
        });
        
        // 선택된 섹션 활성화
        const targetSection = document.getElementById(`${sectionName}-section`);
        const targetLink = document.querySelector(`[data-section="${sectionName}"]`);
        
        if (targetSection) {
            targetSection.classList.add('active');
            targetSection.style.display = 'block';
            console.log(`✅ 섹션 활성화: ${sectionName}-section`);
            
            // 그룹 섹션이 활성화되면 데이터 로드 (중복 방지)
            if (sectionName === 'group' && window.groupSection) {
                console.log('🔄 그룹 섹션 활성화 - 데이터 로드');
                // 이미 로드 중이거나 최근에 로드했다면 스킵
                if (window.groupSection.isLoading) {
                    console.log('⚠️ 그룹 데이터 로드 중이므로 스킵');
                    return;
                }
                
                setTimeout(() => {
                    if (window.groupSection) {
                        // 초기화가 안 되어 있으면 먼저 초기화
                        if (!window.groupSection.initialized) {
                            window.groupSection.init();
                        }
                        // 데이터 로드
                        if (typeof window.groupSection.loadData === 'function') {
                            window.groupSection.loadData();
                        } else if (typeof window.groupSection.loadMyGroups === 'function') {
                            window.groupSection.loadMyGroups();
                        }
                    }
                }, 100);
            }
        } else {
            console.log(`❌ 섹션을 찾을 수 없음: ${sectionName}-section`);
        }
        
        if (targetLink) {
            targetLink.classList.add('active');
            console.log(`✅ 네비게이션 링크 활성화: ${sectionName}`);
        }
    },

    // 사용자 정보 로드
    async loadUserInfo() {
        try {
            const token = localStorage.getItem('mufi_token');
            console.log('🔍 사용자 정보 로드 시작, 토큰:', token ? '존재함' : '없음');
            
            if (!token) {
                console.log('❌ 토큰이 없어서 사용자 정보를 가져올 수 없습니다');
                return;
            }
            
            const response = await fetch('/oauth/user', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            console.log('📡 사용자 정보 응답 상태:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ 사용자 정보 요청 실패:', response.status, errorText);
                return;
            }
            
            const userData = await response.json();
            console.log('✅ 사용자 정보 로드 성공:', userData);
            
            // 사용자 정보 표시
            this.updateUserInfo(userData);
            
            // Google 토큰 동기화 (JWT 세션과 함께)
            this.syncGoogleTokens();
            
        } catch (error) {
            console.error('❌ 사용자 정보 로드 실패:', error);
        }
    },

    // Google 토큰 동기화
    async syncGoogleTokens() {
        try {
            const token = localStorage.getItem('mufi_token');
            if (!token) return;

            console.log('🔄 Google 토큰 동기화 시작');
            
            const response = await fetch('/api/schedules/gmail-auth-status', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            const result = await response.json();
            
            if (result.success && result.data.success) {
                console.log('✅ Google 토큰 동기화 완료');
            } else {
                console.log('⚠️ Google 토큰 동기화 필요 - 다음 Gmail 사용 시 자동 처리됨');
            }
            
        } catch (error) {
            console.log('⚠️ Google 토큰 동기화 확인 실패:', error);
        }
    },

    // 로딩 오버레이 표시
    showLoadingOverlay(message = 'AI가 통화 내용을 분석 중입니다...') {
        const overlay = document.getElementById('loadingOverlay');
        const loadingText = overlay?.querySelector('.loading-text');
        
        if (overlay) {
            if (loadingText) {
                loadingText.textContent = message;
            }
            overlay.style.display = 'flex';
            console.log('🔄 로딩 오버레이 표시:', message);
        }
    },

    // 로딩 오버레이 숨기기
    hideLoadingOverlay() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
            console.log('✅ 로딩 오버레이 숨김');
        }
    },

    // 사용자 정보 업데이트
    updateUserInfo(userData) {
        const userName = document.getElementById('userName');
        const userEmail = document.getElementById('userEmail');
        const userAvatar = document.getElementById('userAvatar');
        const avatarPlaceholder = document.querySelector('.avatar-placeholder');
        const userInitials = document.getElementById('userInitials');
        
        console.log('🖼️ 사용자 정보 업데이트:', userData);
        
        if (userName && userData.name) {
            userName.textContent = userData.name;
            console.log('✅ 사용자 이름 업데이트:', userData.name);
        }
        
        if (userEmail && userData.email) {
            userEmail.textContent = userData.email;
            console.log('✅ 사용자 이메일 업데이트:', userData.email);
        }
        
        if (userAvatar && userData.picture) {
            userAvatar.src = userData.picture;
            userAvatar.alt = userData.name || '사용자';
            userAvatar.style.display = 'block';
            
            if (avatarPlaceholder) {
                avatarPlaceholder.style.display = 'none';
            }
            
            console.log('✅ 프로필 사진 업데이트:', userData.picture);
        } else if (userData.name && userInitials) {
            // 프로필 사진이 없으면 이니셜 표시
            userInitials.textContent = userData.name.charAt(0).toUpperCase();
            if (avatarPlaceholder) {
                avatarPlaceholder.style.display = 'flex';
            }
            if (userAvatar) {
                userAvatar.style.display = 'none';
            }
            console.log('✅ 이니셜 표시:', userData.name.charAt(0).toUpperCase());
        }
    },

    // 네비게이션 설정
    setupNavigation() {
        console.log('🧭 네비게이션 설정 중...');
        
        // 기본적으로 분석 섹션 활성화
        this.switchSection('analysis');
    },

    // 분석 섹션은 별도 파일로 분리됨 (analysis.js)

    // 로그아웃 처리
    handleLogout() {
        console.log('🚪 로그아웃 처리 중...');
        
        // 로컬 스토리지에서 토큰 제거
        localStorage.removeItem('mufi_token');
        
        // 로그인 페이지로 리다이렉트
        window.location.href = '/login';
    },

    // 로그아웃 함수 (호환성)
    logout() {
        this.handleLogout();
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
    dashboard.init();
});

// 전역 객체로 노출
window.dashboard = dashboard;