/**
 * MUFI 대시보드 - 프리미엄 통화 분석 시스템
 * 사용자 친화적인 인터페이스와 완전한 백엔드 연동
 */

class MUFIDashboard {
    constructor() {
        console.log('🎯 대시보드 생성자 호출');
        
        // DOM이 준비되면 즉시 초기화
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
        this.init();
        }
    }

    init() {
        console.log('🚀 대시보드 초기화 시작');
        this.initializeDashboard();
    }

    initializeDashboard() {
        console.log('📋 DOM 요소들 바인딩 시작...');
        
        try {
            // DOM 요소들
            this.elements = {
                // 네비게이션
                navLinks: document.querySelectorAll('.nav-link'),
                sections: document.querySelectorAll('.content-section'),
                
                // 탭 시스템
                tabButtons: document.querySelectorAll('.tab-button'),
                tabContents: document.querySelectorAll('.tab-content'),
                
                // 파일 업로드
                uploadArea: document.getElementById('uploadArea'),
                fileInput: document.getElementById('fileInput'),
                uploadBtn: document.getElementById('uploadBtn'),
                fileInfo: document.getElementById('fileInfo'),
                fileName: document.getElementById('fileName'),
                fileSize: document.getElementById('fileSize'),
                removeFileBtn: document.getElementById('removeFileBtn'),
                
                // 텍스트 입력
                textContent: document.getElementById('textContent'),
                analyzeTextBtn: document.getElementById('analyzeTextBtn'),
                
                // 결과 표시
                analysisResults: document.getElementById('analysisResults'),
                analysisContent: document.getElementById('analysisContent'),
                
                // 사용자 프로필
                userProfile: document.getElementById('userProfile'),
                userAvatar: document.getElementById('userAvatar'),
                userInitials: document.getElementById('userInitials'),
                userName: document.getElementById('userName'),
                userEmail: document.getElementById('userEmail'),
                
                // 인원 관리
                addMemberBtn: document.getElementById('addMemberBtn'),
                membersContainer: document.getElementById('membersContainer'),
                rolesGrid: document.getElementById('rolesGrid'),
                
                // 로딩 & 모달
                loadingOverlay: document.getElementById('loadingOverlay'),
                modal: document.getElementById('modal'),
                modalTitle: document.getElementById('modalTitle'),
                modalBody: document.getElementById('modalBody'),
                modalClose: document.getElementById('modalClose')
            };
            
            console.log('✅ DOM 요소 바인딩 완료');
            
            // 누락된 요소 확인
            const missingElements = [];
            Object.entries(this.elements).forEach(([key, element]) => {
                if (!element || (element.length !== undefined && element.length === 0)) {
                    missingElements.push(key);
                }
            });
            
            if (missingElements.length > 0) {
                console.warn('⚠️ 누락된 DOM 요소들:', missingElements);
            }

            // 상태 관리
            this.state = {
                selectedFile: null,
                isAnalyzing: false,
                currentSection: 'analysis',
                currentTab: 'file-upload',
                members: []
            };

            // 설정
            this.config = {
                maxFileSize: 10 * 1024 * 1024, // 10MB
                allowedTypes: ['.txt'],
                apiBaseUrl: window.location.origin // FastAPI 서버 URL
            };

            console.log('🔧 이벤트 바인딩 시작...');
            this.bindEvents();
            this.updateButtonStates();
            
            // 사용자 정보 로드
            console.log('👤 사용자 정보 로드 시작...');
            this.loadUserInfo();
            
            // Google 인증 콜백 체크
            this.checkGoogleAuthCallback();
            
            this.hideLoading();
            console.log('🎉 대시보드 초기화 완료!');
            this.showToast('환영합니다! MUFI에서 통화 내용을 스마트하게 분석해보세요 🚀', 'info');
            
        } catch (error) {
            console.error('❌ 대시보드 초기화 실패:', error);
            // 로딩 오버레이 숨기기
            const loadingOverlay = document.getElementById('loadingOverlay');
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
        }
    }



    bindEvents() {
        // 네비게이션 이벤트
        // 네비게이션 이벤트 바인딩
        console.log('🔗 네비게이션 링크 개수:', this.elements.navLinks.length);
        this.elements.navLinks.forEach((link, index) => {
            console.log(`🔗 네비게이션 링크 ${index}:`, link.dataset.section, link.textContent.trim());
            link.addEventListener('click', (e) => {
                console.log('🖱️ 네비게이션 클릭됨:', e.currentTarget.dataset.section);
                this.handleNavigation(e);
            });
        });

        // 탭 이벤트
        this.elements.tabButtons.forEach(button => {
            button.addEventListener('click', (e) => this.handleTabSwitch(e));
        });

        // 파일 업로드 이벤트
        this.elements.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        this.elements.uploadBtn.addEventListener('click', () => this.handleFileUpload());
        if (this.elements.removeFileBtn) {
            this.elements.removeFileBtn.addEventListener('click', () => this.removeFile());
        }

        // 드래그 앤 드롭
        this.elements.uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.elements.uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.elements.uploadArea.addEventListener('drop', (e) => this.handleDrop(e));
        this.elements.uploadArea.addEventListener('click', () => this.elements.fileInput.click());

        // 텍스트 입력 이벤트
        this.elements.textContent.addEventListener('input', () => this.updateButtonStates());
        this.elements.analyzeTextBtn.addEventListener('click', () => this.handleTextAnalysis());

        // 모달 이벤트
        this.elements.modalClose.addEventListener('click', () => this.hideModal());
        this.elements.modal.addEventListener('click', (e) => {
            if (e.target === this.elements.modal) this.hideModal();
        });

        // 인원 관리 이벤트
        if (this.elements.addMemberBtn) {
            this.elements.addMemberBtn.addEventListener('click', () => this.showAddMemberModal());
        }

        // 키보드 단축키
        document.addEventListener('keydown', (e) => this.handleKeydown(e));
    }

    // 인증된 요청을 위한 헬퍼 메서드
    async authenticatedFetch(url, options = {}) {
        // URL 파라미터에서 토큰 가져오기 (fallback)
        let token = null;
        if (window.authManager && window.authManager.getToken) {
            token = window.authManager.getToken();
        } else {
            // URL 파라미터에서 토큰 추출
            const urlParams = new URLSearchParams(window.location.search);
            token = urlParams.get('token');
            
            // userInfo에서도 시도
            if (!token && this.userInfo && this.userInfo.token) {
                token = this.userInfo.token;
            }
        }
        
        const headers = {
            ...options.headers
        };
        
        // FormData가 아닌 경우에만 Content-Type 설정
        if (!(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
        }
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(url, {
            ...options,
            headers
        });
        
        // 401 오류 시 로그아웃 처리
        if (response.status === 401) {
            console.log('🔒 인증 토큰 만료 - 로그인 페이지로 이동');
            if (window.authManager && window.authManager.logout) {
                window.authManager.logout();
            } else {
                window.location.href = '/login.html';
            }
            throw new Error('인증이 필요합니다');
        }
        
        return response;
    }

    // 네비게이션 처리
    handleNavigation(e) {
        console.log('🎯 handleNavigation 호출됨');
        e.preventDefault();
        const targetSection = e.currentTarget.dataset.section;
        console.log('🎯 목표 섹션:', targetSection);
        
        // 네비게이션 업데이트
        this.elements.navLinks.forEach(link => link.classList.remove('active'));
        e.currentTarget.classList.add('active');
        
        // 섹션 전환
        this.elements.sections.forEach(section => section.classList.remove('active'));
        const targetElement = document.getElementById(`${targetSection}-section`);
        console.log('🎯 목표 엘리먼트:', targetElement);
        if (targetElement) {
            targetElement.classList.add('active');
            this.state.currentSection = targetSection;
            console.log('✅ 섹션 전환 완료:', targetSection);
        }

        // 일정 관리 섹션인 경우 일정 목록 로드
        if (targetSection === 'schedules') {
            console.log('🔍 [DEBUG] 일정 관리 탭 클릭됨 - loadSchedules 호출');
            this.loadSchedules();
        }
    }

    // 탭 전환 처리
    handleTabSwitch(e) {
                e.preventDefault();
        const targetTab = e.currentTarget.dataset.tab;
        
        // 탭 버튼 업데이트
        this.elements.tabButtons.forEach(button => button.classList.remove('active'));
        e.currentTarget.classList.add('active');
        
        // 탭 컨텐츠 전환
        this.elements.tabContents.forEach(content => content.classList.remove('active'));
        const targetContent = document.getElementById(targetTab);
        if (targetContent) {
            targetContent.classList.add('active');
            this.state.currentTab = targetTab;
        }
        
        // 탭 전환 시 버튼 상태 업데이트
        this.updateButtonStates();
        
        console.log(`탭 전환: ${targetTab}`);
    }

    // 파일 선택 처리
    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.validateAndSetFile(file);
        }
    }

    // 파일 검증 및 설정
    validateAndSetFile(file) {
        // 파일 형식 검증
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        if (!this.config.allowedTypes.includes(fileExtension)) {
            this.showToast('⚠️ 지원하지 않는 파일 형식입니다. .txt 파일만 업로드 가능합니다.', 'error');
            return;
        }

        // 파일 크기 검증
        if (file.size > this.config.maxFileSize) {
            this.showToast('⚠️ 파일 크기가 너무 큽니다. 10MB 이하의 파일만 업로드 가능합니다.', 'error');
            return;
        }

        // 파일 설정
        this.state.selectedFile = file;
        this.displayFileInfo(file);
        this.updateButtonStates();
        this.showToast('✅ 파일이 선택되었습니다. 이제 분석을 시작할 수 있습니다!', 'success');
    }

    // 파일 정보 표시
    displayFileInfo(file) {
        this.elements.fileName.textContent = file.name;
        this.elements.fileSize.textContent = this.formatFileSize(file.size);
        this.elements.fileInfo.classList.add('show');
    }

    // 파일 크기 포맷팅
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // 파일 제거
    removeFile() {
        this.state.selectedFile = null;
        this.elements.fileInput.value = '';
        this.elements.fileInfo.classList.remove('show');
        this.updateButtonStates();
        this.showToast('파일이 제거되었습니다.', 'info');
    }

    // 드래그 오버
    handleDragOver(e) {
        e.preventDefault();
        this.elements.uploadArea.classList.add('dragover');
    }

    // 드래그 리브
    handleDragLeave(e) {
        e.preventDefault();
        this.elements.uploadArea.classList.remove('dragover');
    }

    // 드롭 처리
    handleDrop(e) {
        e.preventDefault();
        this.elements.uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.validateAndSetFile(files[0]);
        }
    }

    // 파일 업로드 및 분석
    async handleFileUpload() {
        if (!this.state.selectedFile || this.state.isAnalyzing) return;

        this.state.isAnalyzing = true;
        this.showLoading('📄 파일을 읽는 중입니다...');
        this.updateButtonStates();

        try {
            const formData = new FormData();
            formData.append('file', this.state.selectedFile);
            
            const response = await this.authenticatedFetch(`${this.config.apiBaseUrl}/api/analyze/file`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`서버 오류: ${response.status}`);
            }

            this.showLoading('🤖 AI가 통화 내용을 꼼꼼히 분석하고 있습니다...');
            
            const result = await response.json();
            
            if (result.success) {
                this.displayAnalysisResults(result.data);
                this.showToast('🎉 분석이 완료되었습니다! 결과를 확인해보세요.', 'success');
            } else {
                throw new Error(result.message || '분석 중 오류가 발생했습니다.');
            }
            
        } catch (error) {
            console.error('파일 업로드 오류:', error);
            this.showToast(`❌ 분석 실패: ${error.message}`, 'error');
        } finally {
            this.state.isAnalyzing = false;
            this.hideLoading();
            this.updateButtonStates();
        }
    }

    // 텍스트 분석
    async handleTextAnalysis() {
        const content = this.elements.textContent.value.trim();
        if (!content || this.state.isAnalyzing) return;

        this.state.isAnalyzing = true;
        this.showLoading('🤖 AI가 입력하신 내용을 세심하게 분석하고 있습니다...');
        this.updateButtonStates();

        try {
            const response = await this.authenticatedFetch(`${this.config.apiBaseUrl}/api/analyze/text`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content })
            });
            
            if (!response.ok) {
                throw new Error(`서버 오류: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.displayAnalysisResults(result.data);
                this.showToast('🎉 텍스트 분석이 완료되었습니다! 결과를 확인해보세요.', 'success');
            } else {
                throw new Error(result.message || '분석 중 오류가 발생했습니다.');
            }
            
        } catch (error) {
            console.error('텍스트 분석 오류:', error);
            this.showToast(`❌ 분석 실패: ${error.message}`, 'error');
        } finally {
            this.state.isAnalyzing = false;
            this.hideLoading();
            this.updateButtonStates();
        }
    }

    // 분석 결과 표시
    displayAnalysisResults(data) {
        console.log('🎯 분석 결과 표시:', data);
        
        // 현재 분석 결과를 상태에 저장
        this.state.currentAnalysisData = data;
        
        let html = `
            <div class="analysis-results-container">
                <div class="results-header">
                    <h2><i class="fas fa-chart-line"></i> 분석 결과</h2>
                </div>
        `;


        
        // 단체일정과 개인일정 분리
        const groupSchedules = data.schedules ? data.schedules.filter(s => s.type === 'group' || !s.type) : [];
        const personalSchedules = data.schedules ? data.schedules.filter(s => s.type === 'personal') : [];
        
        // 단체일정
        if (groupSchedules.length > 0) {
            html += `
                <div class="result-section">
                    <h3><i class="fas fa-users"></i> 단체일정 (${groupSchedules.length}개)</h3>
                    <div class="schedules-list">
                        ${groupSchedules.map((schedule, index) => {
                            const originalIndex = data.schedules.indexOf(schedule);
                            return `
                            <div class="schedule-item" data-index="${originalIndex}">
                                <div class="schedule-header">
                                    <div class="schedule-title editable-content" onclick="window.dashboard.editScheduleField(this, 'title', ${originalIndex})">
                                        ${this.escapeHtml(schedule.title || '제목 없음')}
                                    </div>
                                    <button class="btn-icon btn-danger" onclick="window.dashboard.removeSchedule(${originalIndex})" title="일정 삭제">
                                        <i class="fas fa-times"></i>
                                    </button>
                                </div>
                                <div class="schedule-details">
                                    ${schedule.participants && schedule.participants.length > 0 ? `
                                        <div class="schedule-field">
                                            <i class="fas fa-users"></i>
                                            <span class="schedule-participants">
                                                ${schedule.participants.map(p => typeof p === 'string' ? p : p.name || p).join(', ')}
                                            </span>
                                        </div>
                                    ` : ''}
                                    ${schedule.location ? `
                                        <div class="schedule-field">
                                            <i class="fas fa-map-marker-alt"></i>
                                            <span class="editable-content" onclick="window.dashboard.editScheduleField(this, 'location', ${originalIndex})">
                                                ${this.escapeHtml(schedule.location)}
                                            </span>
                                        </div>
                                    ` : ''}
                                    ${schedule.start_datetime ? `
                                        <div class="schedule-field">
                                            <i class="fas fa-clock"></i>
                                            <span class="editable-content" onclick="window.dashboard.editScheduleField(this, 'start_datetime', ${originalIndex})">
                                                ${this.formatDateTime(schedule.start_datetime)}
                                            </span>
                                        </div>
                                    ` : ''}
                                    ${schedule.end_datetime ? `
                                        <div class="schedule-field">
                                            <i class="fas fa-clock"></i>
                                            <span class="editable-content" onclick="window.dashboard.editScheduleField(this, 'end_datetime', ${originalIndex})">
                                                ${this.formatDateTime(schedule.end_datetime)}
                                            </span>
                                        </div>
                                    ` : ''}
                                </div>
                            </div>
                            `;
                        }).join('')}
                    </div>
                    <button class="btn btn-secondary btn-small" onclick="window.dashboard.addSchedule('group')">
                        <i class="fas fa-plus"></i> 단체일정 추가
                    </button>
                </div>
            `;
        }
        
        // 개인일정
        if (personalSchedules.length > 0) {
            html += `
                <div class="result-section">
                    <h3><i class="fas fa-user"></i> 개인일정 (${personalSchedules.length}개)</h3>
                    <div class="schedules-list personal-schedules">
                        ${personalSchedules.map((schedule, index) => {
                            const originalIndex = data.schedules.indexOf(schedule);
                            return `
                            <div class="schedule-item personal-schedule" data-index="${originalIndex}">
                                <div class="schedule-header">
                                    <div class="schedule-title editable-content" onclick="window.dashboard.editScheduleField(this, 'title', ${originalIndex})">
                                        ${this.escapeHtml(schedule.title || '제목 없음')}
                                    </div>
                                    <button class="btn-icon btn-danger" onclick="window.dashboard.removeSchedule(${originalIndex})" title="일정 삭제">
                                        <i class="fas fa-times"></i>
                                    </button>
                                </div>
                                <div class="schedule-details">
                                    ${schedule.participants && schedule.participants.length > 0 ? `
                                        <div class="schedule-field">
                                            <i class="fas fa-user"></i>
                                            <span class="schedule-participants">
                                                담당자: ${schedule.participants.map(p => typeof p === 'string' ? p : p.name || p).join(', ')}
                                            </span>
                                        </div>
                                    ` : ''}
                                    ${schedule.description ? `
                                        <div class="schedule-field">
                                            <i class="fas fa-info-circle"></i>
                                            <span class="editable-content" onclick="window.dashboard.editScheduleField(this, 'description', ${originalIndex})">
                                                ${this.escapeHtml(schedule.description)}
                                            </span>
                                        </div>
                                    ` : ''}
                                    ${schedule.start_datetime ? `
                                        <div class="schedule-field">
                                            <i class="fas fa-clock"></i>
                                            <span class="editable-content" onclick="window.dashboard.editScheduleField(this, 'start_datetime', ${originalIndex})">
                                                ${this.formatDateTime(schedule.start_datetime)}
                                            </span>
                                        </div>
                                    ` : ''}
                                    ${schedule.end_datetime ? `
                                        <div class="schedule-field">
                                            <i class="fas fa-clock"></i>
                                            <span class="editable-content" onclick="window.dashboard.editScheduleField(this, 'end_datetime', ${originalIndex})">
                                                ${this.formatDateTime(schedule.end_datetime)}
                                            </span>
                                        </div>
                                    ` : ''}
                                </div>
                            </div>
                            `;
                        }).join('')}
                    </div>
                    <button class="btn btn-secondary btn-small" onclick="window.dashboard.addSchedule('personal')">
                        <i class="fas fa-plus"></i> 개인일정 추가
                    </button>
                </div>
            `;
        }
        


        // 저장 버튼
        html += `
                <div class="result-actions">
                    <button class="btn btn-primary btn-large" onclick="window.dashboard.saveAnalysisResults()">
                        <i class="fas fa-save"></i> 분석 결과 저장
                    </button>
                    <button class="btn btn-secondary" onclick="window.dashboard.clearResults()">
                        <i class="fas fa-broom"></i> 결과 지우기
                    </button>
                </div>
            </div>
        `;

        this.elements.analysisResults.innerHTML = html;
        this.elements.analysisResults.style.display = 'block';
        
        // 결과로 스크롤
        this.elements.analysisResults.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        console.log('✅ 분석 결과 표시 완료');
    }

    // ICS 파일 생성 및 다운로드
    async generateICS() {
        try {
            this.showLoading('📅 캘린더 파일을 생성하는 중입니다...');
            
            const response = await this.authenticatedFetch(`${this.config.apiBaseUrl}/api/schedules/generate-ics`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error('ICS 파일 생성에 실패했습니다.');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `MUFI_일정_${new Date().getTime()}.ics`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            this.showToast('📥 캘린더 파일이 다운로드되었습니다!', 'success');
            
        } catch (error) {
            console.error('ICS 생성 오류:', error);
            this.showToast('❌ 캘린더 파일 생성에 실패했습니다.', 'error');
        } finally {
            this.hideLoading();
        }
    }

    // 버튼 상태 업데이트
    updateButtonStates() {
        const hasFile = !!this.state.selectedFile;
        const hasText = this.elements.textContent.value.trim().length > 0;
        const isAnalyzing = this.state.isAnalyzing;

        // 파일 업로드 버튼
        this.elements.uploadBtn.disabled = !hasFile || isAnalyzing;
        
        // 텍스트 관련 버튼
        this.elements.analyzeTextBtn.disabled = !hasText || isAnalyzing;

        // 분석 중일 때 버튼 텍스트 변경
        if (isAnalyzing) {
            this.elements.uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 분석 중...';
            this.elements.analyzeTextBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 분석 중...';
        } else {
            this.elements.uploadBtn.innerHTML = '<i class="fas fa-search"></i> 분석 시작';
            this.elements.analyzeTextBtn.innerHTML = '<i class="fas fa-search"></i> 분석 시작';
        }
    }

    // 키보드 단축키 처리
    handleKeydown(e) {
        // Ctrl + Enter: 분석 실행
        if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            if (this.elements.textContent.value.trim()) {
                this.handleTextAnalysis();
            }
        }
        
        // Escape: 모달 닫기
        if (e.key === 'Escape') {
            this.hideModal();
        }
    }

    // 로딩 표시
    showLoading(message = 'AI가 열심히 분석하고 있습니다...') {
        this.elements.loadingOverlay.querySelector('.loading-text').textContent = message;
        this.elements.loadingOverlay.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    // 로딩 숨기기
    hideLoading() {
        this.elements.loadingOverlay.style.display = 'none';
        document.body.style.overflow = '';
    }

    // 모달 표시
    showModal(title, content) {
        this.elements.modalTitle.textContent = title;
        this.elements.modalBody.innerHTML = content;
        this.elements.modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    // 모달 숨기기
    hideModal() {
        this.elements.modal.classList.remove('show');
        document.body.style.overflow = '';
    }

    // Toast 알림 표시
    showToast(message, type = 'info') {
        // 기존 toast 제거
        const existingToast = document.querySelector('.toast');
        if (existingToast) {
            existingToast.remove();
        }

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-message">${message}</div>
                <button class="toast-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
                </div>
        `;

        document.body.appendChild(toast);

        // 애니메이션으로 표시
        setTimeout(() => toast.classList.add('show'), 100);

        // 자동 제거 (5초 후)
        setTimeout(() => {
            if (toast.parentNode) {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }
        }, 5000);
    }

    // 사용자 정보 로드
    loadUserInfo() {
        try {
            // URL 파라미터에서 사용자 정보 추출
            const urlParams = new URLSearchParams(window.location.search);
            const name = decodeURIComponent(urlParams.get('name') || '사용자');
            const email = decodeURIComponent(urlParams.get('email') || '');
            const picture = decodeURIComponent(urlParams.get('picture') || '');
            const token = urlParams.get('token');
            const userId = urlParams.get('user_id');
            const googleCredentials = urlParams.get('google_credentials');

            console.log('📋 사용자 정보:', { name, email, picture: !!picture, userId, hasGoogleCredentials: !!googleCredentials });

            // Google Calendar 토큰이 있으면 저장
            if (googleCredentials) {
                try {
                    const credentials = JSON.parse(decodeURIComponent(googleCredentials));
                    this.setGoogleCredentials(credentials);
                    console.log('✅ Google Calendar 토큰 자동 저장 완료');
                } catch (error) {
                    console.error('❌ Google Calendar 토큰 파싱 실패:', error);
                }
            }

            // 사용자 정보를 전역에 저장
            this.userInfo = { name, email, picture, token, user_id: userId };

            // 사용자 이름 표시
            this.elements.userName.textContent = name;
            this.elements.userEmail.textContent = email;

            // 프로필 이미지 처리
            if (picture && picture !== 'undefined') {
                this.elements.userAvatar.src = picture;
                this.elements.userAvatar.style.display = 'block';
                this.elements.userAvatar.nextElementSibling.style.display = 'none';
            } else {
                // 이니셜 표시
                const initials = name.split(' ').map(word => word.charAt(0)).join('').substring(0, 2).toUpperCase();
                this.elements.userInitials.textContent = initials;
                this.elements.userAvatar.style.display = 'none';
                this.elements.userAvatar.nextElementSibling.style.display = 'flex';
            }

            // URL 파라미터 정리 (토큰 정보 제거)
            if (urlParams.has('google_credentials') || urlParams.has('token')) {
                const cleanUrl = window.location.pathname;
                window.history.replaceState({}, document.title, cleanUrl);
            }

            console.log('✅ 사용자 정보 로드 완료');

        } catch (error) {
            console.error('❌ 사용자 정보 로드 실패:', error);
            this.elements.userName.textContent = '사용자';
            this.elements.userEmail.textContent = '정보 로드 실패';
        }
    }

    // 로그아웃
    logout() {
        try {
            console.log('🚪 로그아웃 시작...');
            
            // 로컬 저장소 정리
            localStorage.clear();
            sessionStorage.clear();
            
            // 쿠키 정리
            document.cookie.split(";").forEach(cookie => {
                const eqPos = cookie.indexOf("=");
                const name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
                document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
            });
            
            this.showToast('로그아웃되었습니다.', 'info');
            
            // 로그인 페이지로 리다이렉트
            setTimeout(() => {
                window.location.href = '/login.html';
            }, 1000);
            
        } catch (error) {
            console.error('❌ 로그아웃 실패:', error);
            // 실패해도 강제 리다이렉트
            window.location.href = '/login.html';
        }
    }

    // 인원 관리 - 멤버 추가 모달 표시
    showAddMemberModal() {
        const modalContent = `
            <form id="addMemberForm">
                <div class="form-group">
                    <label for="memberName">이름</label>
                    <input type="text" id="memberName" class="form-control" placeholder="멤버 이름을 입력하세요" required>
                </div>
                <div class="form-group">
                    <label for="memberEmail">이메일</label>
                    <input type="email" id="memberEmail" class="form-control" placeholder="example@email.com" required>
                </div>
                <div class="form-group">
                    <label for="memberRole">역할</label>
                    <select id="memberRole" class="form-control" required>
                        <option value="">역할을 선택하세요</option>
                        <option value="프로젝트 매니저">프로젝트 매니저</option>
                        <option value="개발자">개발자</option>
                        <option value="디자이너">디자이너</option>
                        <option value="분석가">분석가</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="memberDepartment">부서</label>
                    <input type="text" id="memberDepartment" class="form-control" placeholder="부서명 (선택사항)">
                </div>
                <div class="modal-buttons">
                    <button type="button" class="btn btn-secondary" onclick="dashboard.hideModal()">취소</button>
                    <button type="submit" class="btn btn-primary">추가</button>
                </div>
            </form>
        `;

        this.showModal('새 멤버 추가', modalContent);

        // 폼 이벤트 바인딩
        const form = document.getElementById('addMemberForm');
        if (form) {
            form.addEventListener('submit', (e) => this.handleAddMember(e));
        }
    }

    // 인원 관리 - 멤버 추가 처리
    handleAddMember(e) {
        e.preventDefault();
        
        const name = document.getElementById('memberName').value.trim();
        const email = document.getElementById('memberEmail').value.trim();
        const role = document.getElementById('memberRole').value;
        const department = document.getElementById('memberDepartment').value.trim();

        if (!name || !email || !role) {
            this.showToast('필수 정보를 모두 입력해주세요.', 'error');
            return;
        }

        // 이메일 중복 체크
        if (this.state.members.some(member => member.email === email)) {
            this.showToast('이미 등록된 이메일입니다.', 'error');
            return;
        }

        // 멤버 추가
        const newMember = {
            id: Date.now().toString(),
            name,
            email,
            role,
            department: department || '미지정',
            joinDate: new Date().toLocaleDateString('ko-KR'),
            status: 'active'
        };

        this.state.members.push(newMember);
        this.updateMembersDisplay();
        this.updateRoleCounts();
        this.hideModal();
        
        this.showToast(`${name}님이 팀에 추가되었습니다.`, 'success');
    }

    // 인원 관리 - 멤버 목록 업데이트
    updateMembersDisplay() {
        if (!this.elements.membersContainer) return;

        if (this.state.members.length === 0) {
            this.elements.membersContainer.innerHTML = `
                <div class="placeholder-content">
                    <div class="placeholder-icon">
                        <i class="fas fa-users"></i>
                    </div>
                    <h3>등록된 멤버가 없습니다</h3>
                    <p>새 멤버를 추가하여 팀을 구성해보세요.</p>
                </div>
            `;
            return;
        }

        const membersHtml = this.state.members.map(member => `
            <div class="member-card" data-member-id="${member.id}">
                <div class="member-avatar">
                    <div class="avatar-placeholder">
                        <span>${member.name.charAt(0).toUpperCase()}</span>
                    </div>
                </div>
                <div class="member-info">
                    <h4>${this.escapeHtml(member.name)}</h4>
                    <p class="member-email">${this.escapeHtml(member.email)}</p>
                    <p class="member-role">${this.escapeHtml(member.role)} • ${this.escapeHtml(member.department)}</p>
                    <p class="member-date">가입일: ${member.joinDate}</p>
                </div>
                <div class="member-actions">
                    <button class="btn-icon" onclick="dashboard.editMember('${member.id}')" title="수정">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-icon btn-danger" onclick="dashboard.removeMember('${member.id}')" title="삭제">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');

        this.elements.membersContainer.innerHTML = membersHtml;
    }

    // 인원 관리 - 역할별 인원 수 업데이트
    updateRoleCounts() {
        const roleCounts = {
            '프로젝트 매니저': 0,
            '개발자': 0,
            '디자이너': 0,
            '분석가': 0
        };

        this.state.members.forEach(member => {
            if (roleCounts.hasOwnProperty(member.role)) {
                roleCounts[member.role]++;
            }
        });

        const roleCards = this.elements.rolesGrid.querySelectorAll('.role-card');
        roleCards.forEach((card, index) => {
            const roles = Object.keys(roleCounts);
            if (index < roles.length) {
                const role = roles[index];
                const countElement = card.querySelector('.role-count');
                if (countElement) {
                    countElement.textContent = `${roleCounts[role]}명`;
                }
            }
        });
    }

    // 인원 관리 - 멤버 삭제
    removeMember(memberId) {
        const member = this.state.members.find(m => m.id === memberId);
        if (!member) return;

        if (confirm(`${member.name}님을 팀에서 제거하시겠습니까?`)) {
            this.state.members = this.state.members.filter(m => m.id !== memberId);
            this.updateMembersDisplay();
            this.updateRoleCounts();
            this.showToast(`${member.name}님이 팀에서 제거되었습니다.`, 'info');
        }
    }

    // 분석 결과 편집 관련 메서드들
    saveAnalysisResults() {
        if (!this.currentAnalysisData) {
            this.showToast('저장할 분석 결과가 없습니다.', 'error');
            return;
        }

        // 여기서 백엔드 API 호출하여 분석 결과 저장
        this.showToast('분석 결과가 저장되었습니다.', 'success');
    }

    editScheduleField(scheduleIndex, field) {
        const schedule = this.currentAnalysisData.schedules[scheduleIndex];
        if (!schedule) return;

        const currentValue = schedule[field] || '';
        const newValue = prompt(`${field} 편집:`, currentValue);
        
        if (newValue !== null && newValue !== currentValue) {
            schedule[field] = newValue;
            this.displayAnalysisResults(this.currentAnalysisData);
            this.showToast('일정이 수정되었습니다.', 'success');
        }
    }

    removeSchedule(scheduleIndex) {
        if (confirm('이 일정을 삭제하시겠습니까?')) {
            this.currentAnalysisData.schedules.splice(scheduleIndex, 1);
            this.displayAnalysisResults(this.currentAnalysisData);
            this.showToast('일정이 삭제되었습니다.', 'info');
        }
    }

    addSchedule(type = 'group') {
        const newSchedule = {
            title: type === 'group' ? '새 단체일정' : '새 개인일정',
            description: '',
            location: type === 'group' ? '' : undefined, // 개인일정은 location 불필요
            start_datetime: new Date().toISOString(),
            end_datetime: new Date(Date.now() + 3600000).toISOString(), // 1시간 후
            type: type,
            participants: type === 'group' ? ['참여자1', '참여자2'] : ['담당자']
        };

        if (!this.state.currentAnalysisData.schedules) {
            this.state.currentAnalysisData.schedules = [];
        }
        
        this.state.currentAnalysisData.schedules.push(newSchedule);
        this.displayAnalysisResults(this.state.currentAnalysisData);
        
        const typeName = type === 'group' ? '단체일정' : '개인일정';
        this.showToast(`새 ${typeName}이 추가되었습니다.`, 'success');
    }

    editActionField(actionIndex, field) {
        const action = this.currentAnalysisData.actions[actionIndex];
        if (!action) return;

        const currentValue = action[field] || '';
        const newValue = prompt(`${field} 편집:`, currentValue);
        
        if (newValue !== null && newValue !== currentValue) {
            action[field] = newValue;
            this.displayAnalysisResults(this.currentAnalysisData);
            this.showToast('개인일정이 수정되었습니다.', 'success');
        }
    }

    removeAction(actionIndex) {
        if (confirm('이 개인일정을 삭제하시겠습니까?')) {
            this.currentAnalysisData.actions.splice(actionIndex, 1);
            this.displayAnalysisResults(this.currentAnalysisData);
            this.showToast('개인일정이 삭제되었습니다.', 'info');
        }
    }

    addAction() {
        const newAction = {
            assignee: '담당자',
            description: '새 개인일정',
            deadline: new Date().toISOString().split('T')[0]
        };

        if (!this.currentAnalysisData.actions) {
            this.currentAnalysisData.actions = [];
        }
        
        this.currentAnalysisData.actions.push(newAction);
        this.displayAnalysisResults(this.currentAnalysisData);
        this.showToast('새 개인일정이 추가되었습니다.', 'success');
    }



    // 인원 관리 - 멤버 편집
    editMember(memberId) {
        const member = this.state.members.find(m => m.id === memberId);
        if (!member) return;

        const modalContent = `
            <form id="editMemberForm">
                <div class="form-group">
                    <label for="editMemberName">이름</label>
                    <input type="text" id="editMemberName" class="form-control" value="${this.escapeHtml(member.name)}" required>
                </div>
                <div class="form-group">
                    <label for="editMemberEmail">이메일</label>
                    <input type="email" id="editMemberEmail" class="form-control" value="${this.escapeHtml(member.email)}" required>
                </div>
                <div class="form-group">
                    <label for="editMemberRole">역할</label>
                    <select id="editMemberRole" class="form-control" required>
                        <option value="프로젝트 매니저" ${member.role === '프로젝트 매니저' ? 'selected' : ''}>프로젝트 매니저</option>
                        <option value="개발자" ${member.role === '개발자' ? 'selected' : ''}>개발자</option>
                        <option value="디자이너" ${member.role === '디자이너' ? 'selected' : ''}>디자이너</option>
                        <option value="분석가" ${member.role === '분석가' ? 'selected' : ''}>분석가</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="editMemberDepartment">부서</label>
                    <input type="text" id="editMemberDepartment" class="form-control" value="${this.escapeHtml(member.department)}">
                </div>
                <div class="modal-buttons">
                    <button type="button" class="btn btn-secondary" onclick="dashboard.hideModal()">취소</button>
                    <button type="submit" class="btn btn-primary">수정</button>
                </div>
            </form>
        `;

        this.showModal('멤버 정보 수정', modalContent);

        // 폼 이벤트 바인딩
        const form = document.getElementById('editMemberForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                
                const name = document.getElementById('editMemberName').value.trim();
                const email = document.getElementById('editMemberEmail').value.trim();
                const role = document.getElementById('editMemberRole').value;
                const department = document.getElementById('editMemberDepartment').value.trim();

                if (!name || !email || !role) {
                    this.showToast('필수 정보를 모두 입력해주세요.', 'error');
                    return;
                }

                // 이메일 중복 체크 (본인 제외)
                if (this.state.members.some(m => m.email === email && m.id !== memberId)) {
                    this.showToast('이미 등록된 이메일입니다.', 'error');
                    return;
                }

                // 멤버 정보 업데이트
                member.name = name;
                member.email = email;
                member.role = role;
                member.department = department || '미지정';

                this.updateMembersDisplay();
                this.updateRoleCounts();
                this.hideModal();
                
                this.showToast(`${name}님의 정보가 수정되었습니다.`, 'success');
            });
        }
    }

    // 유틸리티 함수들
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ko-KR');
    }

    formatDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ko-KR') + ' ' + date.toLocaleTimeString('ko-KR', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }

    // 결과 지우기
    clearResults() {
        if (confirm('분석 결과를 지우시겠습니까?')) {
            this.elements.analysisResults.style.display = 'none';
            this.elements.analysisResults.innerHTML = '';
            this.state.currentAnalysisData = null;
        }
    }
}

// 대시보드 클래스 정의 완료 - HTML에서 인스턴스 생성

// AuthManager를 전역에서 접근 가능하도록 설정
window.authManager = window.authManager || null;

// 추가 CSS 스타일을 동적으로 추가
const additionalStyles = `
    /* 분석 결과 메인 컨테이너 */
    .analysis-results-container {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 32px;
        margin-top: 24px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
        animation: slideInUp 0.3s ease-out;
    }
    
    .results-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 32px;
        padding-bottom: 24px;
        border-bottom: 2px solid #f3f4f6;
    }
    
    .results-header h2 {
        font-size: 28px;
        font-weight: 700;
        color: #111827;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .results-header h2 i {
        color: #3b82f6;
        font-size: 24px;
    }
    
    .source-info {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 4px;
    }
    
    .source-type {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
    }
    
    .source-name {
        font-size: 14px;
        color: #6b7280;
        font-weight: 500;
    }

    .result-section {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        transition: all 0.2s ease;
    }
    
    .result-section:hover {
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transform: translateY(-1px);
    }
    
    .result-section h3 {
        font-size: 20px;
        font-weight: 600;
        color: #111827;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .result-section h3 i {
        color: #3b82f6;
        font-size: 18px;
    }

    .result-item {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 16px;
        transition: all 0.2s ease;
    }

    .result-item:hover {
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transform: translateY(-1px);
    }

    /* 요약 섹션 스타일 */
    .summary-content {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 20px;
        font-size: 15px;
        line-height: 1.7;
        color: #374151;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .summary-content:hover {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }

    /* 참석자 리스트 스타일 */
    .participants-list {
        display: grid;
        gap: 12px;
    }
    
    .participant-item {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.2s ease;
    }
    
    .participant-item:hover {
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .participant-info {
        display: flex;
        align-items: center;
        gap: 12px;
        flex: 1;
    }
    
    .participant-name {
        font-weight: 600;
        color: #111827;
        font-size: 15px;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 4px;
        transition: all 0.2s ease;
    }
    
    .participant-name:hover {
        background: #eff6ff;
        color: #1d4ed8;
    }
    
    .participant-role {
        background: #f3f4f6;
        color: #6b7280;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .participant-role:hover {
        background: #e5e7eb;
        color: #374151;
    }

    /* 일정 리스트 스타일 */
    .schedules-list {
        display: grid;
        gap: 16px;
    }

    .schedule-item {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 20px;
        transition: all 0.2s ease;
        overflow: hidden;
    }

    .schedule-item:hover {
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transform: translateY(-1px);
    }

    .schedule-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 16px;
    }

    .schedule-title {
        font-size: 18px;
        font-weight: 600;
        color: #111827;
        cursor: pointer;
        padding: 6px 10px;
        border-radius: 6px;
        transition: all 0.2s ease;
        flex: 1;
        margin-right: 12px;
    }

    .schedule-title:hover {
        background: #f3f4f6;
        color: #1d4ed8;
    }

    .schedule-details {
        display: grid;
        gap: 8px;
        margin-bottom: 12px;
    }

    .schedule-details .detail-item {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 14px;
        color: #6b7280;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 4px;
        transition: all 0.2s ease;
    }

    .schedule-details .detail-item:hover {
        background: #f9fafb;
        color: #374151;
    }

    .schedule-details .detail-item i {
        width: 16px;
        color: #9ca3af;
        font-size: 13px;
    }

    .schedule-description {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 12px;
        margin-top: 12px;
        font-size: 14px;
        color: #374151;
        line-height: 1.6;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .schedule-description:hover {
        border-color: #d1d5db;
        background: #f3f4f6;
    }

    /* 개인일정 스타일 */
    .actions-list {
        display: grid;
        gap: 12px;
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .action-item {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.2s ease;
    }

    .action-item:hover {
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .action-info {
        display: flex;
        flex-direction: column;
        gap: 6px;
        flex: 1;
    }

    .action-text {
        font-size: 15px;
        color: #111827;
        font-weight: 500;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 4px;
        transition: all 0.2s ease;
    }

    .action-text:hover {
        background: #f3f4f6;
        color: #1d4ed8;
    }

    .action-assignee {
        font-size: 13px;
        color: #6b7280;
        cursor: pointer;
        padding: 2px 6px;
        border-radius: 4px;
        transition: all 0.2s ease;
    }

    .action-assignee:hover {
        background: #f9fafb;
        color: #374151;
    }

    .action-due-date {
        background: #fef3c7;
        color: #d97706;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .action-due-date:hover {
        background: #fde68a;
        color: #b45309;
    }

    /* 버튼 스타일 개선 */
    .schedule-actions {
        display: flex;
        gap: 12px;
        justify-content: center;
        margin-top: 32px;
        padding-top: 24px;
        border-top: 2px solid #f3f4f6;
    }

    .btn {
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.2s ease;
        border: none;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }

    .btn-primary {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
    }

    .btn-primary:hover {
        background: linear-gradient(135deg, #1d4ed8, #1e40af);
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.4);
    }

    .btn-secondary {
        background: #f3f4f6;
        color: #374151;
        border: 1px solid #d1d5db;
    }

    .btn-secondary:hover {
        background: #e5e7eb;
        color: #111827;
        transform: translateY(-1px);
    }

    .btn-icon {
        padding: 8px;
        border-radius: 6px;
        border: none;
        cursor: pointer;
        transition: all 0.2s ease;
        background: none;
        color: #6b7280;
    }

    .btn-icon:hover {
        background: #f3f4f6;
        color: #374151;
    }

    .btn-danger {
        color: #dc2626;
    }

    .btn-danger:hover {
        background: #fef2f2;
        color: #b91c1c;
    }

    .toast-content {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
    }

    .toast-message {
        flex: 1;
        font-size: 14px;
        color: #333333;
        font-weight: 500;
    }

    .toast-close {
        background: none;
        border: none;
        color: #999999;
        cursor: pointer;
        padding: 4px;
        border-radius: 50%;
        transition: all 0.2s ease;
    }

    .toast-close:hover {
        background: rgba(0, 0, 0, 0.1);
        color: #666666;
    }

    .placeholder-content {
        text-align: center;
        padding: 60px 20px;
        color: #666666;
    }

    .placeholder-icon {
        font-size: 64px;
        margin-bottom: 20px;
        opacity: 0.5;
    }

    .placeholder-content h3 {
        font-size: 20px;
        margin-bottom: 8px;
        color: #333333;
    }

    .placeholder-content p {
        font-size: 14px;
        color: #888888;
    }

    /* 인원 관리 스타일 */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 1px solid rgba(0, 0, 0, 0.1);
    }

    .members-container {
        display: grid;
        gap: 16px;
        margin-bottom: 20px;
    }

    .member-card {
        display: flex;
        align-items: center;
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 8px;
        padding: 16px;
        transition: all 0.2s ease;
    }

    .member-card:hover {
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        transform: translateY(-1px);
    }

    .member-avatar {
        margin-right: 16px;
    }

    .member-avatar .avatar-placeholder {
        width: 48px;
        height: 48px;
        background: #2563eb;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        font-size: 18px;
    }

    .member-info {
        flex: 1;
    }

    .member-info h4 {
        margin: 0 0 4px 0;
        font-size: 16px;
        font-weight: 600;
        color: #000000;
    }

    .member-email {
        margin: 0 0 4px 0;
        font-size: 14px;
        color: #666666;
    }

    .member-role {
        margin: 0 0 4px 0;
        font-size: 13px;
        color: #888888;
    }

    .member-date {
        margin: 0;
        font-size: 12px;
        color: #999999;
    }

    .member-actions {
        display: flex;
        gap: 8px;
    }

    .btn-icon {
        background: none;
        border: none;
        padding: 8px;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.2s ease;
        color: #666666;
    }

    .btn-icon:hover {
        background: rgba(0, 0, 0, 0.1);
        color: #333333;
    }

    .btn-icon.btn-danger:hover {
        background: rgba(220, 53, 69, 0.1);
        color: #dc3545;
    }

    .roles-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
    }

    .role-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 8px;
        padding: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s ease;
    }

    .role-card:hover {
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    }

    .role-info h4 {
        margin: 0 0 4px 0;
        font-size: 14px;
        font-weight: 600;
        color: #000000;
    }

    .role-info p {
        margin: 0;
        font-size: 12px;
        color: #888888;
        line-height: 1.4;
    }

    .role-count {
        font-size: 18px;
        font-weight: 600;
        color: #2563eb;
    }

    .form-group {
        margin-bottom: 16px;
    }

    .form-group label {
        display: block;
        margin-bottom: 6px;
        font-weight: 500;
        color: #333333;
        font-size: 14px;
    }

    .form-control {
        width: 100%;
        padding: 10px 12px;
        border: 1px solid #ddd;
        border-radius: 6px;
        font-size: 14px;
        transition: border-color 0.2s ease;
    }

    .form-control:focus {
        outline: none;
        border-color: #2563eb;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }

    .modal-buttons {
        display: flex;
        gap: 12px;
        justify-content: flex-end;
        margin-top: 24px;
        padding-top: 20px;
        border-top: 1px solid rgba(0, 0, 0, 0.1);
    }

    /* 분석 결과 편집 스타일 */
    .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        padding: 16px;
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 8px;
    }

    .result-title {
        margin: 0;
        font-size: 20px;
        font-weight: 600;
        color: #000000;
    }

    .result-actions {
        display: flex;
        gap: 8px;
    }

    .result-item-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }

    .result-item-header h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        color: #000000;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .btn-edit {
        background: none;
        border: none;
        color: #666666;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 4px;
        transition: all 0.2s ease;
        font-size: 12px;
    }

    .btn-edit:hover {
        background: rgba(0, 0, 0, 0.1);
        color: #333333;
    }

    .editable-field {
        cursor: pointer;
        padding: 2px 4px;
        border-radius: 3px;
        transition: background-color 0.2s ease;
        display: inline-block;
    }

    .editable-field:hover {
        background-color: rgba(37, 99, 235, 0.1);
        color: #2563eb;
    }

    .editable-title {
        cursor: pointer;
        transition: color 0.2s ease;
    }

    .editable-title:hover {
        color: #2563eb;
    }

    .schedule-card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 12px;
    }

    .schedule-card-header h4 {
        margin: 0;
        flex: 1;
    }

    .btn-small {
        padding: 4px 6px;
        font-size: 11px;
        border: none;
        border-radius: 3px;
        cursor: pointer;
        transition: all 0.2s ease;
        margin-left: 8px;
    }

    .btn-small.btn-danger {
        background: rgba(220, 53, 69, 0.1);
        color: #dc3545;
    }

    .btn-small.btn-danger:hover {
        background: #dc3545;
        color: white;
    }

    .btn-sm {
        padding: 6px 12px;
        font-size: 12px;
        margin-top: 12px;
    }

    .participants-list li,
    .actions-list li {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    }

    .participants-list li:last-child,
    .actions-list li:last-child {
        border-bottom: none;
    }

    /* 파일 정보 표시 개선 */
    .file-info {
        margin-top: 16px;
        display: none;
    }

    .file-info.show {
        display: block;
    }

    .file-preview {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 1px solid #0ea5e9;
        border-radius: 8px;
        gap: 12px;
    }

    .file-preview .file-icon {
        color: #0ea5e9;
        font-size: 18px;
        min-width: 18px;
    }

    .file-preview .file-details {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .file-preview .file-name {
        font-weight: 500;
        color: #0c4a6e;
        font-size: 14px;
    }

    .file-preview .file-size {
        font-size: 12px;
        color: #0369a1;
        opacity: 0.8;
    }

    .file-preview .btn-remove {
        background: none;
        border: none;
        color: #ef4444;
        cursor: pointer;
        padding: 6px;
        border-radius: 4px;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .file-preview .btn-remove:hover {
        background: rgba(239, 68, 68, 0.1);
        color: #dc2626;
    }
        background: none;
        border: none;
        color: #999999;
        cursor: pointer;
        padding: 6px;
        border-radius: 4px;
        transition: all 0.2s ease;
        font-size: 12px;
    }

    .btn-remove:hover {
        background: rgba(220, 53, 69, 0.1);
        color: #dc3545;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;

// 스타일 추가
const styleElement = document.createElement('style');
styleElement.textContent = additionalStyles;
document.head.appendChild(styleElement);

class MUFIDashboardExtension extends MUFIDashboard {
    // 분석 결과를 저장하는 함수
    async saveAnalysisResults() {
        console.log('💾 분석 결과 저장 중...');
        console.log('현재 분석 데이터:', this.state.currentAnalysisData);
        
        if (!this.state.currentAnalysisData) {
            this.showToast('❌ 저장할 분석 결과가 없습니다.', 'error');
            return;
        }

        try {
            this.showLoading('💾 분석 결과를 저장하는 중입니다...');
            

            
            const saveData = {
                // GPT 새 구조를 백엔드 호환 구조로 변환
                user_id: (() => {
                    const urlParams = new URLSearchParams(window.location.search);
                    return urlParams.get('user_id') || this.userInfo?.user_id || 'anonymous';
                })(),
                source_name: this.state.currentAnalysisData.source_name || '통화 분석',
                source_type: this.state.currentAnalysisData.source_type || 'text',
                summary: '', // 더이상 사용하지 않음
                schedules: [
                    ...(this.state.currentAnalysisData.group || this.state.currentAnalysisData.schedules || []),
                    ...(this.state.currentAnalysisData.personal || [])
                ],
                participants: [], // 각 일정별로 participants가 포함되어 있으므로 전체 participants는 빈 배열
                actions: []  // personal 데이터는 schedules에 포함시켰으므로 빈 배열
            };

            
            const response = await this.authenticatedFetch(`${this.config.apiBaseUrl}/api/save`, {
                method: 'POST',
                body: JSON.stringify(saveData)
            });
            
            if (!response.ok) {
                throw new Error(`저장 오류: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('✅ 분석 결과가 성공적으로 저장되었습니다!', 'success');
            } else {
                throw new Error(result.message || '저장에 실패했습니다.');
            }
            
        } catch (error) {
            console.error('저장 오류:', error);
            this.showToast(`❌ 저장 실패: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    // 일정 편집 함수들

    editScheduleField(element, field, index) {
        const schedule = this.state.currentAnalysisData.schedules[index];
        const currentValue = schedule[field] || '';
        
        let input;
        if (field === 'start_datetime' || field === 'end_datetime') {
            input = document.createElement('input');
            input.type = 'datetime-local';
            input.value = currentValue ? new Date(currentValue).toISOString().slice(0, 16) : '';
        } else {
            input = document.createElement('input');
            input.type = 'text';
            input.value = currentValue;
        }
        
        input.className = 'inline-edit-input';
        input.style.width = '100%';
        input.style.padding = '4px 8px';
        input.style.border = '2px solid #2563eb';
        input.style.borderRadius = '4px';
        input.style.fontSize = 'inherit';
        input.style.fontFamily = 'inherit';
        
        const saveEdit = () => {
            const newValue = input.value.trim();
            if (field === 'start_datetime' || field === 'end_datetime') {
                schedule[field] = newValue ? new Date(newValue).toISOString() : null;
                element.textContent = newValue ? this.formatDateTime(schedule[field]) : '';
            } else {
                schedule[field] = newValue;
                element.textContent = newValue;
            }
        };
        
        input.addEventListener('blur', saveEdit);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                saveEdit();
            } else if (e.key === 'Escape') {
                element.textContent = field === 'start_datetime' || field === 'end_datetime' 
                    ? this.formatDateTime(currentValue) : currentValue;
            }
        });
        
        element.textContent = '';
        element.appendChild(input);
        input.focus();
    }

    editActionField(element, field, index) {
        const action = this.state.currentAnalysisData.actions[index];
        const currentValue = action[field] || '';
        
        let input;
        if (field === 'due_date') {
            input = document.createElement('input');
            input.type = 'date';
            input.value = currentValue;
        } else {
            input = document.createElement('input');
            input.type = 'text';
            input.value = currentValue;
        }
        
        input.className = 'inline-edit-input';
        input.style.width = '100%';
        input.style.padding = '4px 8px';
        input.style.border = '2px solid #2563eb';
        input.style.borderRadius = '4px';
        input.style.fontSize = 'inherit';
        input.style.fontFamily = 'inherit';
        
        const saveEdit = () => {
            const newValue = input.value.trim();
            action[field] = newValue;
            element.textContent = field === 'due_date' ? this.formatDate(newValue) : newValue;
        };
        
        input.addEventListener('blur', saveEdit);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                saveEdit();
            } else if (e.key === 'Escape') {
                element.textContent = field === 'due_date' ? this.formatDate(currentValue) : currentValue;
            }
        });
        
        element.textContent = '';
        element.appendChild(input);
        input.focus();
    }



    // 항목 제거 함수들
    removeSchedule(index) {
        if (confirm('이 일정을 삭제하시겠습니까?')) {
            this.state.currentAnalysisData.schedules.splice(index, 1);
            this.displayAnalysisResults(this.state.currentAnalysisData);
        }
    }

    removeAction(index) {
        if (confirm('이 개인일정을 삭제하시겠습니까?')) {
            this.state.currentAnalysisData.actions.splice(index, 1);
            this.displayAnalysisResults(this.state.currentAnalysisData);
        }
    }

    // 항목 추가 함수들 (addSchedule은 위에서 이미 정의됨)

    addAction() {
        if (!this.state.currentAnalysisData.actions) {
            this.state.currentAnalysisData.actions = [];
        }
        const newAction = {
            text: '새 개인일정',
            assignee: '',
            due_date: null
        };
        this.state.currentAnalysisData.actions.push(newAction);
        this.displayAnalysisResults(this.state.currentAnalysisData);
    }

    // 결과 지우기
    clearResults() {
        if (confirm('분석 결과를 지우시겠습니까?')) {
            this.elements.analysisResults.style.display = 'none';
            this.elements.analysisResults.innerHTML = '';
            this.state.currentAnalysisData = null;
        }
    }

    // 일정 관리 기능들
    async loadSchedules() {
        console.log('🚀 [START] loadSchedules 함수 시작!');
        
        try {
            const urlParams = new URLSearchParams(window.location.search);
            let userId = urlParams.get('user_id') || this.userInfo?.user_id;
            
            // 테스트용: DB에 실제 데이터가 있는 user_id 사용
            if (!userId) {
                userId = '5e462ae0-b67a-4f47-942f-81485142bb51'; // 테스트용 고정 ID
                console.log('🔍 [DEBUG] 테스트용 고정 user_id 사용:', userId);
            }
            
            console.log('🔍 [DEBUG] loadSchedules 호출됨');
            console.log('🔍 [DEBUG] URL params:', Object.fromEntries(urlParams));
            console.log('🔍 [DEBUG] this.userInfo:', this.userInfo);
            console.log('🔍 [DEBUG] 최종 userId:', userId);
            
            if (!userId) {
                this.showToast('사용자 정보를 찾을 수 없습니다.', 'error');
                return;
            }

            this.showLoading('일정 목록을 불러오는 중...');

            const apiUrl = `${this.config.apiBaseUrl}/api/schedules?user_id=${userId}`;
            console.log('🔍 [DEBUG] API 호출 URL:', apiUrl);

            const response = await this.authenticatedFetch(apiUrl);
            
            console.log('🔍 [DEBUG] API 응답 상태:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.log('🔍 [DEBUG] API 에러 응답:', errorText);
                throw new Error(`일정 목록 조회 실패: ${response.status} - ${errorText}`);
            }

            const data = await response.json();
            console.log('🔍 [DEBUG] API 응답 데이터:', data);
            
            if (data.success) {
                console.log('🔍 [DEBUG] 조회된 일정 개수:', data.schedules?.length || 0);
                console.log('🔍 [DEBUG] 그룹화된 통화 개수:', data.grouped_schedules?.length || 0);
                
                // 그룹화된 데이터가 있으면 사용, 없으면 기존 방식
                if (data.grouped_schedules && data.grouped_schedules.length > 0) {
                    this.displayGroupedSchedules(data.grouped_schedules);
                } else {
                    this.displaySchedules(data.schedules);
                }
                
                // 디버그 정보가 있으면 콘솔에 출력
                if (data.debug_info) {
                    console.log('🔍 [DEBUG] 서버 디버그 정보:', data.debug_info);
                }
            } else {
                throw new Error(data.message || '일정 목록 조회에 실패했습니다.');
            }

        } catch (error) {
            console.error('❌ [ERROR] 일정 목록 로드 오류:', error);
            this.showToast(`일정 목록 로드 실패: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    displaySchedules(schedules) {
        const scheduleSection = document.getElementById('schedules-section');
        if (!scheduleSection) {
            console.error('❌ schedules-section 엘리먼트를 찾을 수 없습니다!');
            return;
        }
        console.log('✅ schedules-section 엘리먼트 찾음:', scheduleSection);

        if (!schedules || schedules.length === 0) {
            scheduleSection.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📅</div>
                    <h3>저장된 일정이 없습니다</h3>
                    <p>통화 분석을 통해 일정을 생성해보세요.</p>
                </div>
            `;
            return;
        }

        const schedulesHtml = schedules.map(schedule => this.createScheduleCard(schedule)).join('');
        
        scheduleSection.innerHTML = `
            <div class="schedules-header">
                <h2><i class="fas fa-calendar-alt"></i> 일정 관리</h2>
                <div class="schedules-stats">
                    <span class="stat-item">
                        <i class="fas fa-list"></i>
                        총 ${schedules.length}개 일정
                    </span>
                </div>
            </div>
            <div class="schedules-grid">
                ${schedulesHtml}
            </div>
        `;
    }

    displayGroupedSchedules(groupedSchedules) {
        const scheduleSection = document.getElementById('schedules-section');
        if (!scheduleSection) {
            console.error('❌ schedules-section 엘리먼트를 찾을 수 없습니다!');
            return;
        }
        console.log('✅ schedules-section 엘리먼트 찾음:', scheduleSection);

        if (!groupedSchedules || groupedSchedules.length === 0) {
            scheduleSection.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📅</div>
                    <h3>저장된 일정이 없습니다</h3>
                    <p>통화 분석을 통해 일정을 생성해보세요.</p>
                </div>
            `;
            return;
        }

        const totalSchedules = groupedSchedules.reduce((sum, group) => sum + group.schedule_count, 0);
        const groupsHtml = groupedSchedules.map(group => this.createScheduleGroup(group)).join('');
        
        scheduleSection.innerHTML = `
            <div class="schedules-header">
                <h2><i class="fas fa-calendar-alt"></i> 일정 관리</h2>
                <div class="schedules-stats">
                    <span class="stat-item">
                        <i class="fas fa-phone"></i>
                        총 ${groupedSchedules.length}개 통화
                    </span>
                    <span class="stat-item">
                        <i class="fas fa-list"></i>
                        총 ${totalSchedules}개 일정
                    </span>
                </div>
            </div>
            <div class="schedules-groups">
                ${groupsHtml}
            </div>
        `;
    }

    createScheduleGroup(group) {
        const createdDate = group.created_at ? new Date(group.created_at).toLocaleDateString('ko-KR') : '';
        const createdTime = group.created_at ? new Date(group.created_at).toLocaleTimeString('ko-KR', {hour: '2-digit', minute: '2-digit'}) : '';
        
        const schedulesHtml = group.schedules.map(schedule => this.createScheduleCard(schedule)).join('');
        
        return `
            <div class="schedule-group" data-analysis-id="${group.analysis_id}">
                <div class="schedule-group-header" onclick="window.dashboard.toggleScheduleGroup('${group.analysis_id}')">
                    <div class="group-info">
                        <div class="group-title">
                            <i class="fas fa-phone"></i>
                            <span class="group-name">${this.escapeHtml(group.source_name)}</span>
                            <span class="group-count">(${group.schedule_count}개 일정)</span>
                        </div>
                        <div class="group-date">${createdDate} ${createdTime}</div>
                    </div>
                    <div class="group-toggle">
                        <i class="fas fa-chevron-down"></i>
                    </div>
                </div>
                
                <div class="schedule-group-content expanded">
                    <div class="schedules-grid">
                        ${schedulesHtml}
                    </div>
                    <div class="group-actions">
                        <button class="btn btn-outline btn-small" onclick="window.dashboard.downloadGroupICS('${group.analysis_id}')">
                            <i class="fas fa-download"></i>
                            전체 ICS 다운로드
                        </button>
                        <button class="btn btn-outline btn-small" onclick="window.dashboard.shareGroup('${group.analysis_id}')">
                            <i class="fas fa-share-alt"></i>
                            그룹 공유
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    toggleScheduleGroup(analysisId) {
        const groupElement = document.querySelector(`[data-analysis-id="${analysisId}"]`);
        if (!groupElement) return;

        const content = groupElement.querySelector('.schedule-group-content');
        const toggle = groupElement.querySelector('.group-toggle i');
        
        if (content.classList.contains('expanded')) {
            content.classList.remove('expanded');
            toggle.classList.remove('fa-chevron-down');
            toggle.classList.add('fa-chevron-right');
        } else {
            content.classList.add('expanded');
            toggle.classList.remove('fa-chevron-right');
            toggle.classList.add('fa-chevron-down');
        }
    }

    async downloadGroupICS(analysisId) {
        try {
            this.showLoading('그룹 ICS 파일을 준비하는 중...');
            // TODO: 그룹 전체 ICS 다운로드 구현
            this.showToast('그룹 ICS 다운로드 기능 구현 예정입니다.', 'info');
        } catch (error) {
            console.error('그룹 ICS 다운로드 오류:', error);
            this.showToast(`그룹 ICS 다운로드 실패: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async shareGroup(analysisId) {
        try {
            this.showLoading('그룹 공유 링크를 생성하는 중...');
            // TODO: 그룹 공유 기능 구현
            this.showToast('그룹 공유 기능 구현 예정입니다.', 'info');
        } catch (error) {
            console.error('그룹 공유 오류:', error);
            this.showToast(`그룹 공유 실패: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    createScheduleCard(schedule) {
        console.log('🔍 [DEBUG] createScheduleCard 호출 - schedule:', schedule);
        
        // participants 처리 (문자열 배열 또는 객체 배열 대응)
        let participantsText = '참여자 없음';
        if (schedule.participants && Array.isArray(schedule.participants) && schedule.participants.length > 0) {
            // 문자열 배열인 경우
            if (typeof schedule.participants[0] === 'string') {
                participantsText = schedule.participants.join(', ');
            } 
            // 객체 배열인 경우 (name 필드 추출)
            else if (typeof schedule.participants[0] === 'object' && schedule.participants[0].name) {
                participantsText = schedule.participants.map(p => p.name).join(', ');
            }
        }
        
        const typeIcon = schedule.type === 'group' ? '👥' : '👤';
        const typeText = schedule.type === 'group' ? '단체일정' : '개인일정';
        
        const startDate = schedule.start_datetime ? new Date(schedule.start_datetime).toLocaleDateString('ko-KR') : '';
        const startTime = schedule.start_datetime ? new Date(schedule.start_datetime).toLocaleTimeString('ko-KR', {hour: '2-digit', minute: '2-digit'}) : '';

        console.log('🔍 [DEBUG] 카드 생성 정보 - 제목:', schedule.title, '참여자:', participantsText, '타입:', typeText);

        return `
            <div class="schedule-card" data-schedule-id="${schedule.id}">
                <div class="schedule-card-header">
                    <div class="schedule-type">
                        <span class="type-icon">${typeIcon}</span>
                        <span class="type-text">${typeText}</span>
                    </div>
                    <div class="schedule-date">
                        ${startDate} ${startTime}
                    </div>
                </div>
                
                <div class="schedule-card-body">
                    <h3 class="schedule-title">${this.escapeHtml(schedule.title)}</h3>
                    <p class="schedule-description">${this.escapeHtml(schedule.description || '')}</p>
                    
                    <div class="schedule-details">
                        ${schedule.location && schedule.location !== '미정' ? `
                            <div class="schedule-detail">
                                <i class="fas fa-map-marker-alt"></i>
                                <span>${this.escapeHtml(schedule.location)}</span>
                            </div>
                        ` : ''}
                        
                        <div class="schedule-detail">
                            <i class="fas fa-users"></i>
                            <span>${this.escapeHtml(participantsText)}</span>
                        </div>
                    </div>
                </div>
                
                <div class="schedule-card-actions">
                    <button class="btn btn-primary btn-small" onclick="window.dashboard.addToGoogleCalendar('${schedule.id}')">
                        <i class="fas fa-calendar-plus"></i>
                        캘린더 추가
                    </button>
                    <button class="btn btn-secondary btn-small" onclick="window.dashboard.sendScheduleEmail('${schedule.id}')">
                        <i class="fas fa-envelope"></i>
                        메일 보내기
                    </button>
                    <button class="btn btn-outline btn-small" onclick="window.dashboard.shareSchedule('${schedule.id}')">
                        <i class="fas fa-share-alt"></i>
                        공유
                    </button>
                </div>
            </div>
        `;
    }

    // Google Calendar에 일정 추가
    async addToGoogleCalendar(scheduleId) {
        try {
            // Google 인증 상태 확인
            const googleCredentials = this.getGoogleCredentials();
            
            if (!googleCredentials) {
                // Google 인증이 필요한 경우
                this.showGoogleAuthModal(scheduleId);
                return;
            }

            this.showLoading('Google Calendar에 추가하는 중...');

            const response = await this.authenticatedFetch(`${this.config.apiBaseUrl}/api/calendar/add-schedule`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    schedule_id: scheduleId,
                    user_id: this.userInfo.user_id,
                    google_credentials: googleCredentials,
                    calendar_id: 'primary'  // 기본 캘린더
                })
            });
            
            if (!response.ok) {
                throw new Error(`Calendar 추가 실패: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.success) {
                this.showToast('Google Calendar에 일정이 추가되었습니다!', 'success');
            } else {
                throw new Error(result.error || 'Calendar 추가 실패');
            }

        } catch (error) {
            console.error('❌ Google Calendar 추가 실패:', error);
            
            // 인증 오류인 경우 재인증 유도
            if (error.message.includes('인증') || error.message.includes('401')) {
                this.clearGoogleCredentials();
                this.showGoogleAuthModal(scheduleId);
            } else if (error.message.includes('파싱')) {
                // 파싱 오류인 경우 명확한 메시지
                this.showToast('ICS 파일 형식이 올바르지 않습니다. 일정 데이터를 확인해주세요.', 'error');
            } else {
                this.showToast(`Calendar 추가 실패: ${error.message}`, 'error');
            }
        } finally {
            this.hideLoading();
        }
    }

    // Google 인증 정보 가져오기
    getGoogleCredentials() {
        try {
            const credentials = localStorage.getItem('google_credentials');
            return credentials ? JSON.parse(credentials) : null;
        } catch (error) {
            console.error('Google 인증 정보 로드 실패:', error);
            return null;
        }
    }

    // Google 인증 정보 저장
    setGoogleCredentials(credentials) {
        try {
            localStorage.setItem('google_credentials', JSON.stringify(credentials));
        } catch (error) {
            console.error('Google 인증 정보 저장 실패:', error);
        }
    }

    // Google 인증 정보 삭제
    clearGoogleCredentials() {
        try {
            localStorage.removeItem('google_credentials');
        } catch (error) {
            console.error('Google 인증 정보 삭제 실패:', error);
        }
    }

    // Google 인증 모달 표시
    showGoogleAuthModal(scheduleId) {
        const modalContent = `
            <div class="google-auth-modal">
                <div class="google-auth-icon">
                    <i class="fab fa-google"></i>
                </div>
                <h3>Google Calendar 연동</h3>
                <p>일정을 Google Calendar에 추가하려면 Google 계정과 연동이 필요합니다.</p>
                <div class="modal-buttons">
                    <button type="button" class="btn btn-secondary" onclick="dashboard.hideModal()">취소</button>
                    <button type="button" class="btn btn-primary" onclick="dashboard.startGoogleAuth('${scheduleId}')">
                        <i class="fab fa-google"></i>
                        Google 연동하기
                    </button>
                </div>
            </div>
        `;

        this.showModal('Google Calendar 연동', modalContent);
    }

    // Google 인증 시작
    async startGoogleAuth(scheduleId) {
        try {
            this.hideModal();
            this.showLoading('Google 인증 페이지로 이동 중...');

            // 일정 ID를 임시 저장 (인증 완료 후 사용)
            if (scheduleId) {
                localStorage.setItem('pending_schedule_id', scheduleId);
            }

            // Google 인증 URL로 리다이렉트
            const authUrl = `${this.config.apiBaseUrl}/api/auth/google?user_id=${this.userInfo.user_id}`;
            window.location.href = authUrl;

        } catch (error) {
            console.error('Google 인증 시작 실패:', error);
            this.showToast(`Google 인증 실패: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    // 페이지 로드 시 Google 인증 완료 체크
    checkGoogleAuthCallback() {
        const urlParams = new URLSearchParams(window.location.search);
        const googleAuth = urlParams.get('google_auth');
        
        if (googleAuth === 'success') {
            // Google 인증 성공
            this.showToast('Google Calendar 연동이 완료되었습니다!', 'success');
            
            // 대기 중인 일정이 있으면 처리
            const pendingScheduleId = localStorage.getItem('pending_schedule_id');
            if (pendingScheduleId) {
                localStorage.removeItem('pending_schedule_id');
                
                // 잠시 후 캘린더 추가 재시도
                setTimeout(() => {
                    this.addToGoogleCalendar(pendingScheduleId);
                }, 1000);
            }
            
            // URL 파라미터 정리
            const newUrl = window.location.pathname;
            window.history.replaceState({}, document.title, newUrl);
        }
    }

    // 일정 이메일 발송
    async sendScheduleEmail(scheduleId) {
        const emails = prompt('이메일 주소를 입력하세요 (여러 개인 경우 쉼표로 구분):');
        if (!emails) return;

        try {
            this.showLoading('이메일을 발송하는 중...');

            const emailList = emails.split(',').map(email => email.trim()).filter(email => email);
            
            const response = await this.authenticatedFetch(`${this.config.apiBaseUrl}/api/schedules/${scheduleId}/send-email`, {
                method: 'POST',
                body: JSON.stringify({
                    recipients: emailList
                })
            });
            
            if (!response.ok) {
                throw new Error(`이메일 발송 실패: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                this.showToast(data.message, 'success');
            } else {
                throw new Error(data.message || '이메일 발송에 실패했습니다.');
            }

        } catch (error) {
            console.error('이메일 발송 오류:', error);
            this.showToast(`이메일 발송 실패: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    // 일정 공유
    async shareSchedule(scheduleId) {
        try {
            this.showLoading('공유 링크를 생성하는 중...');

            const response = await this.authenticatedFetch(`${this.config.apiBaseUrl}/api/schedules/${scheduleId}/share`, {
                method: 'POST',
                body: JSON.stringify({
                    share_type: 'link'
                })
            });
            
            if (!response.ok) {
                throw new Error(`공유 실패: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                // 공유 링크를 클립보드에 복사
                const shareUrl = `${window.location.origin}${data.share_url}`;
                navigator.clipboard.writeText(shareUrl).then(() => {
                    this.showToast('공유 링크가 클립보드에 복사되었습니다!', 'success');
                }).catch(() => {
                    this.showToast(`공유 링크: ${shareUrl}`, 'info');
                });
            } else {
                throw new Error(data.message || '공유에 실패했습니다.');
            }

        } catch (error) {
            console.error('공유 오류:', error);
            this.showToast(`공유 실패: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    // 파일 다운로드 헬퍼 함수
    downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
}

export default MUFIDashboardExtension;
