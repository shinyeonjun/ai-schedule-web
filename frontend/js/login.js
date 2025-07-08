// MUFI Login - Dashboard Design System
// 대시보드와 일관성 있는 로그인 기능

document.addEventListener('DOMContentLoaded', function() {
    // DOM 요소들
    const loginForm = document.getElementById('loginForm');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const rememberCheckbox = document.getElementById('remember');
    const loginBtn = document.querySelector('.login-btn');
    const notificationContainer = document.getElementById('notification-container');
    
    // 폼 검증 규칙
    const validation = {
        email: {
            required: true,
            pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
            message: '올바른 이메일 주소를 입력해주세요.'
        },
        password: {
            required: true,
            minLength: 6,
            message: '비밀번호는 최소 6자 이상이어야 합니다.'
        }
    };
    
    // 데모 계정 정보
    const demoAccounts = [
        { email: 'demo@mufi.ai', password: 'demo123', name: '데모 사용자' },
        { email: 'admin@mufi.ai', password: 'admin123', name: '관리자' },
        { email: 'test@mufi.ai', password: 'test123', name: '테스트 사용자' }
    ];
    
    // 초기화
    init();
    
    function init() {
        // 이벤트 리스너 등록
        attachEventListeners();
        
        // 저장된 로그인 정보 복원
        restoreLoginInfo();
        
        // 폼 검증 초기화
        initFormValidation();
        
        // 환영 메시지 표시
        showWelcomeMessage();
    }
    
    function attachEventListeners() {
        // 로그인 폼 제출
        loginForm.addEventListener('submit', handleLogin);
        
        // 실시간 폼 검증
        emailInput.addEventListener('input', () => validateField('email'));
        emailInput.addEventListener('blur', () => validateField('email'));
        
        passwordInput.addEventListener('input', () => validateField('password'));
        passwordInput.addEventListener('blur', () => validateField('password'));

        // 소셜 로그인 버튼들
        const socialButtons = document.querySelectorAll('.social-btn');
        socialButtons.forEach(btn => {
            btn.addEventListener('click', handleSocialLogin);
        });
        
        // 비밀번호 찾기 링크
        const forgotLink = document.querySelector('.forgot-link');
        if (forgotLink) {
            forgotLink.addEventListener('click', handleForgotPassword);
        }
        
        // 회원가입 링크
        const signupLink = document.querySelector('.signup-link');
        if (signupLink) {
            signupLink.addEventListener('click', handleSignup);
        }
        
        // 키보드 단축키
        document.addEventListener('keydown', handleKeyboardShortcuts);
    }
    
    function handleLogin(e) {
        e.preventDefault();
        
        const email = emailInput.value.trim();
        const password = passwordInput.value;
        const remember = rememberCheckbox.checked;
        
        // 폼 검증
        if (!validateForm()) {
            return;
        }
        
        // 로딩 상태 시작
        setLoadingState(true);
        
        // 로그인 시도
        attemptLogin(email, password, remember);
    }
    
    function attemptLogin(email, password, remember) {
        // 데모 계정 확인
        const demoAccount = demoAccounts.find(acc => 
            acc.email === email && acc.password === password
        );
        
        if (demoAccount) {
            // 데모 계정 로그인 성공
            handleLoginSuccess(demoAccount, remember);
                } else {
            // 실제 로그인 API 호출 (시뮬레이션)
            simulateApiLogin(email, password, remember);
        }
    }
    
    function simulateApiLogin(email, password, remember) {
        // API 호출 시뮬레이션
        setTimeout(() => {
            // 간단한 검증 (실제로는 서버에서 처리)
            if (email.includes('@') && password.length >= 6) {
                const user = {
                    email: email,
                    name: email.split('@')[0],
                    loginTime: new Date().toISOString()
                };
                handleLoginSuccess(user, remember);
            } else {
                handleLoginError('이메일 또는 비밀번호가 올바르지 않습니다.');
            }
        }, 1500); // 1.5초 지연으로 로딩 시뮬레이션
    }
    
    function handleLoginSuccess(user, remember) {
        // 로딩 상태 종료
        setLoadingState(false);
        
        // 사용자 정보 저장
        saveUserInfo(user, remember);
        
        // 성공 메시지 표시
        showNotification('로그인 성공!', `${user.name}님, 환영합니다!`, 'success');
        
        // 대시보드로 리디렉션
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 1000);
    }
    
    function handleLoginError(message) {
        // 로딩 상태 종료
        setLoadingState(false);
        
        // 에러 메시지 표시
        showNotification('로그인 실패', message, 'error');
        
        // 비밀번호 필드 포커스
        passwordInput.focus();
        passwordInput.select();
    }
    
    function validateForm() {
        let isValid = true;
        
        // 이메일 검증
        if (!validateField('email')) {
            isValid = false;
        }
        
        // 비밀번호 검증
        if (!validateField('password')) {
            isValid = false;
        }
        
        return isValid;
    }
    
    function validateField(fieldName) {
        const field = document.getElementById(fieldName);
        const rule = validation[fieldName];
        const errorElement = document.getElementById(`${fieldName}-error`);
        
        let isValid = true;
        let errorMessage = '';
        
        // 필수 입력 검증
        if (rule.required && !field.value.trim()) {
            isValid = false;
            errorMessage = `${fieldName === 'email' ? '이메일' : '비밀번호'}를 입력해주세요.`;
        }
        
        // 패턴 검증 (이메일)
        if (fieldName === 'email' && field.value.trim() && !rule.pattern.test(field.value.trim())) {
            isValid = false;
            errorMessage = rule.message;
        }
        
        // 최소 길이 검증 (비밀번호)
        if (fieldName === 'password' && field.value && field.value.length < rule.minLength) {
            isValid = false;
            errorMessage = rule.message;
        }
        
        // 에러 표시/숨김
        if (errorElement) {
            if (isValid) {
                hideError(errorElement);
            } else {
                showError(errorElement, errorMessage);
            }
        }
        
        // 필드 스타일 업데이트
        updateFieldStyle(field, isValid);
        
        return isValid;
    }
    
    function showError(errorElement, message) {
        errorElement.textContent = message;
        errorElement.classList.add('show');
    }
    
    function hideError(errorElement) {
        errorElement.classList.remove('show');
    }
    
    function updateFieldStyle(field, isValid) {
        if (isValid) {
            field.style.borderColor = 'var(--color-gray-300)';
        } else {
            field.style.borderColor = '#dc2626';
        }
    }
    
    function setLoadingState(isLoading) {
        if (isLoading) {
            loginBtn.disabled = true;
            loginBtn.textContent = '로그인 중...';
            loginBtn.style.opacity = '0.7';
        } else {
            loginBtn.disabled = false;
            loginBtn.textContent = '작업데스크 시작하기';
            loginBtn.style.opacity = '1';
        }
    }
    
    function saveUserInfo(user, remember) {
        const storage = remember ? localStorage : sessionStorage;
        
        // 사용자 정보 저장
        storage.setItem('mufi_user', JSON.stringify(user));
        
        // 로그인 상태 저장
        storage.setItem('mufi_logged_in', 'true');
        
        // 이메일 저장 (기억하기 체크된 경우)
        if (remember) {
            localStorage.setItem('mufi_remember_email', user.email);
        }
    }
    
    function restoreLoginInfo() {
        // 저장된 이메일 복원
        const savedEmail = localStorage.getItem('mufi_remember_email');
        if (savedEmail) {
            emailInput.value = savedEmail;
            rememberCheckbox.checked = true;
        }
        
        // 이미 로그인된 상태인지 확인
        const isLoggedIn = localStorage.getItem('mufi_logged_in') || 
                          sessionStorage.getItem('mufi_logged_in');
        
        if (isLoggedIn) {
            // 자동 리디렉션 (선택사항)
            // window.location.href = 'dashboard.html';
        }
    }
    
    function initFormValidation() {
        // 초기 상태에서 에러 메시지 숨김
        const errorElements = document.querySelectorAll('.form-error');
        errorElements.forEach(element => {
            element.classList.remove('show');
        });
    }
    
    function handleSocialLogin(e) {
        e.preventDefault();
        
        const provider = e.target.textContent.includes('Google') ? 'google' : 'microsoft';
        
        showNotification('소셜 로그인', `${provider} 로그인 기능은 준비 중입니다.`, 'info');
    }
    
    function handleForgotPassword(e) {
        e.preventDefault();
        
        const email = emailInput.value.trim();
        
        if (email && validation.email.pattern.test(email)) {
            showNotification('비밀번호 재설정', `${email}로 재설정 링크를 발송했습니다.`, 'success');
        } else {
            showNotification('이메일 입력', '먼저 이메일 주소를 입력해주세요.', 'info');
            emailInput.focus();
        }
    }
    
    function handleSignup(e) {
        e.preventDefault();
        
        showNotification('회원가입', '회원가입 기능은 준비 중입니다.', 'info');
    }
    
    function handleKeyboardShortcuts(e) {
        // Enter 키로 로그인 (폼 외부에서)
        if (e.key === 'Enter' && !e.target.closest('form')) {
            loginForm.dispatchEvent(new Event('submit'));
        }
        
        // Escape 키로 알림 닫기
        if (e.key === 'Escape') {
            closeAllNotifications();
        }
    }
    
    function showWelcomeMessage() {
        // 첫 방문 시 환영 메시지 (선택사항)
        const hasVisited = localStorage.getItem('mufi_has_visited');
        
        if (!hasVisited) {
            setTimeout(() => {
                showNotification('MUFI에 오신 것을 환영합니다!', 'AI 통화 분석으로 스마트한 일정 관리를 시작하세요.', 'info');
                localStorage.setItem('mufi_has_visited', 'true');
            }, 1000);
        }
    }
    
    function showNotification(title, message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        notification.innerHTML = `
            <div class="notification-title" style="font-weight: 600; margin-bottom: 4px;">${title}</div>
            <div class="notification-message" style="font-size: 0.875rem; color: var(--color-gray-600);">${message}</div>
        `;
        
        notificationContainer.appendChild(notification);

        // 애니메이션 시작
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // 자동 제거
        setTimeout(() => {
            removeNotification(notification);
        }, 5000);
        
        // 클릭으로 제거
        notification.addEventListener('click', () => {
            removeNotification(notification);
        });
    }
    
    function removeNotification(notification) {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }
    
    function closeAllNotifications() {
        const notifications = document.querySelectorAll('.notification');
        notifications.forEach(notification => {
            removeNotification(notification);
        });
    }
});

// 비밀번호 토글 함수 (HTML에서 호출)
function togglePassword() {
    const passwordInput = document.getElementById('password');
    const toggleText = document.getElementById('toggle-text');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleText.textContent = '숨기기';
    } else {
        passwordInput.type = 'password';
        toggleText.textContent = '보기';
    }
}

// 전역 유틸리티 함수들
window.MufiLogin = {
    // 로그아웃 함수
    logout: function() {
        localStorage.removeItem('mufi_user');
        localStorage.removeItem('mufi_logged_in');
        sessionStorage.removeItem('mufi_user');
        sessionStorage.removeItem('mufi_logged_in');
        
        window.location.href = 'login.html';
    },
    
    // 현재 사용자 정보 가져오기
    getCurrentUser: function() {
        const user = localStorage.getItem('mufi_user') || sessionStorage.getItem('mufi_user');
        return user ? JSON.parse(user) : null;
    },
    
    // 로그인 상태 확인
    isLoggedIn: function() {
        return !!(localStorage.getItem('mufi_logged_in') || sessionStorage.getItem('mufi_logged_in'));
    }
}; 