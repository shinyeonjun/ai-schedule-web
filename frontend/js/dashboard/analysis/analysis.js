class AnalysisSection {
    constructor() {
        this.selectedFile = null;
        this.editingStates = new Map(); // 편집 상태 관리
        this.originalData = new Map(); // 원본 데이터 백업
        this.analysisSourceName = '통화 분석';
        this.init();
    }

    init() {
        this.setupAnalysisTabs();
        this.setupFileUpload();
        this.setupTextAnalysis();
        this.setupKeyboardShortcuts();
    }

    // 키보드 단축키 설정
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+Enter: 카드 전체 편집 완료만 지원
            if (e.ctrlKey && e.key === 'Enter') {
                const editingCard = document.querySelector('.result-card.editing');
                if (editingCard) {
                    const type = editingCard.dataset.scheduleType;
                    const index = editingCard.dataset.scheduleIndex;
                    this.completeEdit(type, index);
                }
            }
            
            // Escape: 카드 전체 편집 취소만 지원
            if (e.key === 'Escape') {
                const editingCard = document.querySelector('.result-card.editing');
                if (editingCard) {
                    const type = editingCard.dataset.scheduleType;
                    const index = editingCard.dataset.scheduleIndex;
                    this.cancelEdit(type, index);
                }
            }
        });
    }

    // 분석 탭 설정
    setupAnalysisTabs() {
        const tabButtons = document.querySelectorAll('#analysis-section .analysis-tabs .tab-button');
        const tabContents = document.querySelectorAll('#analysis-section .tab-content');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTab = button.dataset.tab;

                // 모든 탭 버튼 비활성화
                tabButtons.forEach(btn => btn.classList.remove('active'));
                
                // 모든 탭 콘텐츠 숨기기
                tabContents.forEach(content => {
                    content.classList.remove('active');
                    content.style.setProperty('display', 'none', 'important');
                    content.style.setProperty('visibility', 'hidden', 'important');
                    content.style.setProperty('opacity', '0', 'important');
                    content.style.setProperty('height', '0', 'important');
                    content.style.setProperty('overflow', 'hidden', 'important');
                });

                // 선택된 탭 활성화
                button.classList.add('active');
                
                const targetContent = document.getElementById(targetTab);
                if (targetContent) {
                    targetContent.classList.add('active');
                    targetContent.style.setProperty('display', 'block', 'important');
                    targetContent.style.setProperty('visibility', 'visible', 'important');
                    targetContent.style.setProperty('opacity', '1', 'important');
                    targetContent.style.setProperty('height', 'auto', 'important');
                    targetContent.style.setProperty('overflow', 'visible', 'important');
                }
            });
        });
    }

    // 파일 업로드 기능 설정
    setupFileUpload() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const uploadBtn = document.getElementById('uploadBtn');
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const removeFileBtn = document.getElementById('removeFileBtn');

        if (!uploadArea || !fileInput || !uploadBtn) {
            return;
        }

        // 드래그 앤 드롭 이벤트
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        });

        // 클릭으로 파일 선택
        uploadArea.addEventListener('click', () => {
            // 파일이 이미 업로드된 상태면 클릭 무시
            if (this.selectedFile) {
                this.showNotification('이미 파일이 업로드되어 있습니다. 기존 파일을 제거한 후 새 파일을 업로드해주세요.', 'error');
                return;
            }
            fileInput.click();
        });

        // 파일 선택 이벤트
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelect(e.target.files[0]);
            }
        });

        // 파일 제거 버튼
        if (removeFileBtn) {
            removeFileBtn.addEventListener('click', () => {
                this.removeFile();
            });
        }

        // 분석 시작 버튼
        if (uploadBtn) {
            uploadBtn.addEventListener('click', () => {
                this.analyzeFile();
            });
        }
    }

    // 파일 선택 처리
    handleFileSelect(file) {
        // 파일 타입 검증
        if (!file.name.toLowerCase().endsWith('.txt')) {
            this.showNotification('텍스트 파일(.txt)만 업로드 가능합니다.', 'error');
            return;
        }

        // 파일 크기 검증 (10MB)
        if (file.size > 10 * 1024 * 1024) {
            this.showNotification('파일 크기는 10MB를 초과할 수 없습니다.', 'error');
            return;
        }

        // 이미 파일이 업로드된 상태인지 확인
        if (this.selectedFile) {
            this.showNotification('이미 파일이 업로드되어 있습니다. 기존 파일을 제거한 후 새 파일을 업로드해주세요.', 'error');
            return;
        }

        // 파일 정보 표시
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const uploadBtn = document.getElementById('uploadBtn');
        const uploadArea = document.getElementById('uploadArea');

        if (fileName) fileName.textContent = file.name;
        if (fileSize) fileSize.textContent = this.formatFileSize(file.size);
        if (fileInfo) fileInfo.classList.add('show');
        if (uploadBtn) uploadBtn.disabled = false;
        
        // 업로드 영역 비활성화
        if (uploadArea) {
            uploadArea.classList.add('disabled');
            uploadArea.style.pointerEvents = 'none';
        }

        // 선택된 파일 저장
        this.selectedFile = file;
    }

    // 파일 제거
    removeFile() {
        const fileInfo = document.getElementById('fileInfo');
        const uploadBtn = document.getElementById('uploadBtn');
        const fileInput = document.getElementById('fileInput');
        const uploadArea = document.getElementById('uploadArea');

        if (fileInfo) fileInfo.classList.remove('show');
        if (uploadBtn) uploadBtn.disabled = true;
        if (fileInput) fileInput.value = '';
        
        // 업로드 영역 다시 활성화
        if (uploadArea) {
            uploadArea.classList.remove('disabled');
            uploadArea.style.pointerEvents = 'auto';
        }

        this.selectedFile = null;
    }

    // 파일 크기 포맷팅
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // 파일 분석 실행
    async analyzeFile() {
        if (!this.selectedFile) {
            this.showNotification('분석할 파일을 선택해주세요.', 'error');
            return;
        }

        try {
            // 로딩 오버레이 표시
            if (window.dashboard && window.dashboard.showLoadingOverlay) {
                window.dashboard.showLoadingOverlay('AI가 파일을 분석 중입니다...');
            }
            
            const formData = new FormData();
            formData.append('file', this.selectedFile);

            const token = localStorage.getItem('mufi_token');
            const response = await fetch('/api/analysis/upload-file', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            const result = await response.json();
            
            if (response.ok) {
                this.showNotification('파일 분석이 완료되었습니다.', 'success');
                this.displayAnalysisResults(result.data);
            } else {
                this.showNotification(result.detail || '분석 중 오류가 발생했습니다.', 'error');
            }

        } catch (error) {
            this.showNotification('분석 중 오류가 발생했습니다.', 'error');
        } finally {
            // 로딩 오버레이 숨기기
            if (window.dashboard && window.dashboard.hideLoadingOverlay) {
                window.dashboard.hideLoadingOverlay();
            }
        }
    }

    // 텍스트 분석 기능 설정
    setupTextAnalysis() {
        const textContent = document.getElementById('textContent');
        const analyzeTextBtn = document.getElementById('analyzeTextBtn');

        if (!textContent || !analyzeTextBtn) return;

        // 텍스트 입력 시 버튼 활성화
        textContent.addEventListener('input', () => {
            analyzeTextBtn.disabled = !textContent.value.trim();
        });

        // 분석 시작 버튼
        analyzeTextBtn.addEventListener('click', () => {
            this.analyzeText();
        });
    }

    // 텍스트 분석 실행
    async analyzeText() {
        const textContent = document.getElementById('textContent');
        const content = textContent.value.trim();

        if (!content) {
            this.showNotification('분석할 내용을 입력해주세요.', 'error');
            return;
        }

        try {
            // 로딩 오버레이 표시
            if (window.dashboard && window.dashboard.showLoadingOverlay) {
                window.dashboard.showLoadingOverlay('AI가 텍스트를 분석 중입니다...');
            }
            
            const formData = new FormData();
            formData.append('content', content);

            const token = localStorage.getItem('mufi_token');
            const response = await fetch('/api/analysis/analyze-text', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            const result = await response.json();
            
            if (response.ok) {
                this.showNotification('텍스트 분석이 완료되었습니다.', 'success');
                this.displayAnalysisResults(result.data);
            } else {
                this.showNotification(result.detail || '분석 중 오류가 발생했습니다.', 'error');
            }

        } catch (error) {
            this.showNotification('분석 중 오류가 발생했습니다.', 'error');
        } finally {
            // 로딩 오버레이 숨기기
            if (window.dashboard && window.dashboard.hideLoadingOverlay) {
                window.dashboard.hideLoadingOverlay();
            }
        }
    }

    // 분석 결과 표시
    displayAnalysisResults(data) {
        const resultsContainer = document.getElementById('analysisResults');
        const resultsContent = document.getElementById('analysisContent');
        
        if (!resultsContainer || !resultsContent) {
            return;
        }
        
        // 결과 컨테이너 표시
        resultsContainer.classList.add('show');
        
        // 백엔드에서 반환하는 데이터 구조에 맞게 수정
        let groupSchedules = [];
        let personalSchedules = [];
        
        // schedules 배열을 처리
        if (data.schedules && Array.isArray(data.schedules)) {
            // 모든 일정을 그룹 일정으로 처리 (임시)
            groupSchedules = data.schedules.map(schedule => ({...schedule, type: 'group'}));
        }
        
        // GPT가 반환한 group과 personal 배열도 지원 (이전 버전 호환)
        if (data.group && Array.isArray(data.group)) {
            groupSchedules = data.group.map(schedule => ({...schedule, type: 'group'}));
        }
        
        if (data.personal && Array.isArray(data.personal)) {
            personalSchedules = data.personal.map(schedule => ({...schedule, type: 'personal'}));
        }
        
        // 일정 배열을 인스턴스 변수로 저장
        this.groupSchedules = groupSchedules;
        this.personalSchedules = personalSchedules;
        
        // 결과 내용 생성
        let html = `
            <div class="results-header">
                <div>
                    <h2 class="results-title">분석 결과</h2>
                    <p class="results-subtitle">통화 내용에서 추출된 일정 정보입니다. 각 필드를 클릭하여 편집할 수 있습니다.</p>
                </div>
                <div class="results-actions">
                    <button class="btn btn-primary" onclick="window.analysisSection.saveAllChanges()">
                        <i class="fas fa-save"></i> 저장
                    </button>
                </div>
            </div>
        `;
        
        // 그룹 일정 섹션 (항상 표시)
        html += `
            <div class="results-section">
                <div class="results-section-header">
                    <h3 class="results-section-title">
                        <i class="fas fa-users"></i>
                        그룹 일정 (${groupSchedules.length}개)
                    </h3>
                    <button class="add-schedule-btn" onclick="window.analysisSection.addNewSchedule('group')">
                        <i class="fas fa-plus"></i>
                        새 일정 추가
                    </button>
                </div>
                <div class="results-cards">
        `;
        
        if (groupSchedules.length > 0) {
            groupSchedules.forEach((schedule, index) => {
                html += this.createScheduleCard(schedule, 'group', index);
            });
        } else {
            html += `
                <div class="empty-results">
                    <i class="fas fa-calendar-times"></i>
                    <h3>그룹 일정이 없습니다</h3>
                    <p>통화 내용에서 그룹 일정을 찾을 수 없습니다.</p>
                </div>
            `;
        }
        
        html += `
                </div>
            </div>
        `;
        
        // 개인 일정 섹션 (항상 표시)
        html += `
            <div class="results-section">
                <div class="results-section-header">
                    <h3 class="results-section-title">
                        <i class="fas fa-user"></i>
                        개인 일정 (${personalSchedules.length}개)
                    </h3>
                    <button class="add-schedule-btn" onclick="window.analysisSection.addNewSchedule('personal')">
                        <i class="fas fa-plus"></i>
                        새 일정 추가
                    </button>
                </div>
                <div class="results-cards">
        `;
        
        if (personalSchedules.length > 0) {
            personalSchedules.forEach((schedule, index) => {
                html += this.createScheduleCard(schedule, 'personal', index);
            });
        } else {
            html += `
                <div class="empty-results">
                    <i class="fas fa-calendar-times"></i>
                    <h3>개인 일정이 없습니다</h3>
                    <p>통화 내용에서 개인 일정을 찾을 수 없습니다.</p>
                </div>
            `;
        }
        
        html += `
                </div>
            </div>
        `;
        
        resultsContent.innerHTML = html;
        
        // 편집 이벤트 리스너 설정
        this.setupEditEventListeners();
    }

    // 일정 카드 생성
    createScheduleCard(schedule, type, index) {
        const startDate = new Date(schedule.start_datetime);
        const endDate = new Date(schedule.end_datetime);
        
        const formatDateTime = (date) => {
            // 유효한 날짜인지 확인
            if (!(date instanceof Date) || isNaN(date.getTime())) {
                return '날짜 오류';
            }
            
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            return `${year}/${month}/${day} - ${hours}:${minutes}`;
        };
        
        return `
            <div class="result-card" data-schedule-index="${index}" data-schedule-type="${type}">
                <div class="card-header">
                    <span class="card-type">${type === 'group' ? '그룹' : '개인'}</span>
                    <h4 class="card-title editable-field" data-field="title" data-type="${type}" data-index="${index}">${schedule.title}</h4>
                    <div class="card-actions">
                        <button class="action-btn edit-action-btn" onclick="window.analysisSection.editSchedule('${type}', ${index})" title="편집">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="action-btn delete-action-btn" onclick="window.analysisSection.deleteSchedule('${type}', ${index})" title="삭제">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="card-content">
                    <div class="card-description editable-field" data-field="description" data-type="${type}" data-index="${index}">
                        ${schedule.description || '설명 없음'}
                    </div>
                    <div class="card-details">
                        <div class="card-detail">
                            <i class="fas fa-clock"></i>
                            <span class="editable-field" data-field="start_datetime" data-type="${type}" data-index="${index}">
                                ${formatDateTime(startDate)}
                            </span>
                            ~
                            <span class="editable-field" data-field="end_datetime" data-type="${type}" data-index="${index}">
                                ${formatDateTime(endDate)}
                            </span>
                        </div>
                        <div class="card-detail">
                            <i class="fas fa-map-marker-alt"></i>
                            <span class="editable-field" data-field="location" data-type="${type}" data-index="${index}">
                                ${schedule.location || '장소 미정'}
                            </span>
                        </div>
                    </div>
                    <div class="card-participants">
                        <div class="participants-title">참여자</div>
                        <div class="participants-list">
                            <span class="editable-field" data-field="participants" data-type="${type}" data-index="${index}">
                                ${schedule.participants && schedule.participants.length > 0 
                                    ? schedule.participants.join(', ') 
                                    : '참여자 없음'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // 편집 이벤트 리스너 설정
    setupEditEventListeners() {
        // 편집 모드가 아닐 때는 필드 클릭 이벤트 비활성화
        const editableFields = document.querySelectorAll('.editable-field');
        editableFields.forEach(field => {
            field.addEventListener('click', (e) => {
                // 입력 요소를 클릭한 경우에는 기본 동작 유지 (편집 재시작 금지)
                const insideEditor = e.target.closest('input, textarea, select');
                if (insideEditor) {
                    return;
                }
                e.stopPropagation();
                // 편집 모드일 때만 필드 편집 허용 (이미 편집 중인 필드는 재시작 금지)
                const card = field.closest('.result-card');
                if (card && card.classList.contains('editing') && !field.classList.contains('editing-field')) {
                    this.startFieldEdit(field);
                }
            });
        });
    }

    // 알림 표시
    showNotification(message, type = 'info') {
        // 기존 알림이 있으면 제거
        const existingNotification = document.querySelector('.notification');
        if (existingNotification) {
            existingNotification.remove();
        }

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // 3초 후 자동 제거
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 3000);
    }

    // 편집 시작/완료/취소
    editSchedule(type, index) {
        const key = `${type}:${index}`;
        const card = document.querySelector(`.result-card[data-schedule-type="${type}"][data-schedule-index="${index}"]`);
        if (!card) return;
        if (this.editingStates.get(key)) {
            this.completeEdit(type, index);
            return;
        }
        const schedule = this._getSchedule(type, index);
        if (!schedule) return;
        if (!this.originalData.has(key)) {
            this.originalData.set(key, JSON.parse(JSON.stringify(schedule)));
        }
        this.editingStates.set(key, true);
        card.classList.add('editing');
        // 편집 모드 진입 시 모든 편집 가능한 필드를 즉시 입력 필드로 전환
        const fields = card.querySelectorAll('.editable-field');
        fields.forEach(f => this.startFieldEdit(f));
    }

    cancelEdit(type, index) {
        const key = `${type}:${index}`;
        const original = this.originalData.get(key);
        if (original) {
            const schedule = this._getSchedule(type, index);
            if (schedule) Object.assign(schedule, original);
        }
        this.originalData.delete(key);
        this.editingStates.delete(key);
        this._rebuildResultsUI();
    }

    completeEdit(type, index) {
        const key = `${type}:${index}`;
        const schedule = this._getSchedule(type, index);
        if (!schedule) return;
        const card = document.querySelector(`.result-card[data-schedule-type="${type}"][data-schedule-index="${index}"]`);
        if (card) {
            const titleEl = card.querySelector('.card-title');
            const descEl = card.querySelector('.card-description');
            const locEl = card.querySelector('[data-field="location"]');
            const startEl = card.querySelector('[data-field="start_datetime"]');
            const endEl = card.querySelector('[data-field="end_datetime"]');
            const partEl = card.querySelector('[data-field="participants"]');

            const readEditedValue = (container) => {
                if (!container) return null;
                const input = container.querySelector('input, textarea');
                return input ? input.value : null; // 입력 필드가 없으면 변경 없음
            };

            const original = this.originalData.get(key) || {};

            const newTitle = readEditedValue(titleEl)?.trim();
            if (typeof newTitle === 'string' && newTitle !== original.title) schedule.title = newTitle;

            const newDesc = readEditedValue(descEl)?.trim();
            if (typeof newDesc === 'string' && newDesc !== original.description) schedule.description = newDesc;

            const newLoc = readEditedValue(locEl)?.trim();
            if (typeof newLoc === 'string' && newLoc !== original.location) schedule.location = newLoc;

            const newStart = readEditedValue(startEl)?.trim();
            const newEnd = readEditedValue(endEl)?.trim();
            if (newStart) {
                const isoStart = this._fromLocalToISO(newStart);
                if (!this._areSameMinute(isoStart, original.start_datetime)) {
                    schedule.start_datetime = isoStart;
                }
            }
            if (newEnd) {
                const isoEnd = this._fromLocalToISO(newEnd);
                if (!this._areSameMinute(isoEnd, original.end_datetime)) {
                    schedule.end_datetime = isoEnd;
                }
            }

            const newPart = readEditedValue(partEl)?.trim();
            if (typeof newPart === 'string') {
                const nextParts = newPart ? newPart.split(',').map(s => s.trim()).filter(Boolean) : [];
                const prevParts = Array.isArray(original.participants) ? original.participants : [];
                if (JSON.stringify(nextParts) !== JSON.stringify(prevParts)) {
                    schedule.participants = nextParts;
                }
            }
        }
        this.originalData.delete(key);
        this.editingStates.delete(key);
        this._rebuildResultsUI();
        this.showNotification('변경사항이 적용되었습니다.', 'success');
    }

    // 일정 삭제/추가
    deleteSchedule(type, index) {
        const list = type === 'group' ? this.groupSchedules : this.personalSchedules;
        if (!Array.isArray(list) || index < 0 || index >= list.length) return;
        if (!confirm('이 일정을 삭제하시겠습니까?')) return;
        list.splice(index, 1);
        this._rebuildResultsUI();
        this.showNotification('일정이 삭제되었습니다.', 'success');
    }

    addNewSchedule(type) {
        const now = new Date();
        const end = new Date(now.getTime() + 60 * 60 * 1000);
        const newSchedule = {
            title: '새 일정',
            description: '',
            location: '',
            start_datetime: now.toISOString(),
            end_datetime: end.toISOString(),
            participants: [],
            type: type,
        };
        if (type === 'group') {
            this.groupSchedules = Array.isArray(this.groupSchedules) ? this.groupSchedules : [];
            this.groupSchedules.push(newSchedule);
            this._rebuildResultsUI();
            this.editSchedule('group', this.groupSchedules.length - 1);
        } else {
            this.personalSchedules = Array.isArray(this.personalSchedules) ? this.personalSchedules : [];
            this.personalSchedules.push(newSchedule);
            this._rebuildResultsUI();
            this.editSchedule('personal', this.personalSchedules.length - 1);
        }
    }

    // 전체 저장 API 연동
    async saveAllChanges() {
        try {
            const token = localStorage.getItem('mufi_token');
            if (!token) {
                this.showNotification('로그인이 필요합니다.', 'error');
                return;
            }

            // 저장 전 세션 제목 입력 모달 표시 (취소 시 중단)
            const providedName = await this.showTitleInputModal(this.analysisSourceName || '');
            if (providedName === null) {
                return; // 사용자가 취소하면 저장 자체를 하지 않음
            }
            this.analysisSourceName = providedName;

            // 여기서부터 실제 저장 시작 → 로딩 오버레이 표시
            if (window.dashboard && window.dashboard.showLoadingOverlay) {
                window.dashboard.showLoadingOverlay('변경사항을 저장 중입니다...');
            }

            const normalize = (s) => ({
                title: s.title || '',
                description: s.description || '',
                location: s.location || '',
                start_datetime: this._ensureISO(s.start_datetime),
                end_datetime: this._ensureISO(s.end_datetime),
                participants: Array.isArray(s.participants) ? s.participants : (typeof s.participants === 'string' && s.participants ? s.participants.split(',').map(x => x.trim()).filter(Boolean) : []),
            });
            const payload = {
                analysis_source_name: (this.analysisSourceName && this.analysisSourceName.trim()) ? this.analysisSourceName.trim() : '통화 분석',
                group: (this.groupSchedules || []).map(normalize),
                personal: (this.personalSchedules || []).map(normalize)
            };
            const res = await fetch('/api/analysis/save-all-changes', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            const json = await res.json();
            if (!res.ok) {
                this.showNotification((json && (json.detail || json.message)) || '저장에 실패했습니다.', 'error');
                return;
            }
            this.showNotification(json.message || '저장되었습니다.', 'success');
            if (window.dashboard && typeof window.dashboard.switchSection === 'function') {
                window.dashboard.switchSection('schedules');
            }
            if (window.schedulesSection && typeof window.schedulesSection.loadAnalysisSessions === 'function') {
                window.schedulesSection.loadAnalysisSessions();
            }
        } catch (e) {
            this.showNotification(`저장 중 오류가 발생했습니다. ${e?.message || ''}`.trim(), 'error');
        } finally {
            if (window.dashboard && window.dashboard.hideLoadingOverlay) {
                window.dashboard.hideLoadingOverlay();
            }
        }
    }

    // 필드 인라인 편집 시작
    startFieldEdit(fieldEl) {
        if (!fieldEl || fieldEl.classList.contains('editing-field')) return;
        const type = fieldEl.dataset.type;
        const index = parseInt(fieldEl.dataset.index, 10);
        const field = fieldEl.dataset.field;
        const schedule = this._getSchedule(type, index);
        if (!schedule) return;
        fieldEl.classList.add('editing-field');
        if (field === 'description') {
            const val = typeof schedule.description === 'string' ? schedule.description : '';
            fieldEl.innerHTML = `<textarea class="edit-textarea" rows="3">${val}</textarea>`;
            return;
        }
        if (field === 'start_datetime' || field === 'end_datetime') {
            const iso = field === 'start_datetime' ? schedule.start_datetime : schedule.end_datetime;
            const local = this._toLocalInputValue(iso);
            fieldEl.innerHTML = `<input type="datetime-local" class="edit-input" value="${local}">`;
            return;
        }
        if (field === 'participants') {
            const val = Array.isArray(schedule.participants) ? schedule.participants.join(', ') : (schedule.participants || '');
            fieldEl.innerHTML = `<input type="text" class="edit-input" value="${val}">`;
            return;
        }
        const text = (schedule[field] ?? '').toString();
        fieldEl.innerHTML = `<input type="text" class="edit-input" value="${text}">`;
    }

    // 헬퍼들
    _getSchedule(type, index) {
        const list = type === 'group' ? this.groupSchedules : this.personalSchedules;
        if (!Array.isArray(list)) return null;
        return list[index] || null;
    }

    _toLocalInputValue(iso) {
        try {
            const d = new Date(iso);
            if (isNaN(d.getTime())) return '';
            const y = d.getFullYear();
            const m = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            const h = String(d.getHours()).padStart(2, '0');
            const min = String(d.getMinutes()).padStart(2, '0');
            return `${y}-${m}-${day}T${h}:${min}`;
        } catch { return ''; }
    }

    _fromLocalToISO(localVal) {
        try {
            const d = new Date(localVal);
            if (isNaN(d.getTime())) return localVal;
            return d.toISOString();
        } catch { return localVal; }
    }

    _ensureISO(val) {
        if (!val) return new Date().toISOString();
        const d = new Date(val);
        return isNaN(d.getTime()) ? val : d.toISOString();
    }

    _areSameMinute(isoA, isoB) {
        try {
            const a = new Date(isoA);
            const b = new Date(isoB);
            if (isNaN(a.getTime()) || isNaN(b.getTime())) return false;
            const ma = Math.floor(a.getTime() / 60000);
            const mb = Math.floor(b.getTime() / 60000);
            return ma === mb;
        } catch { return false; }
    }

    _rebuildResultsUI() {
        const data = { group: this.groupSchedules || [], personal: this.personalSchedules || [] };
        this.displayAnalysisResults(data);
    }

    // 저장 전 세션 제목 입력 모달 표시
    showTitleInputModal(defaultValue = '') {
        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.className = 'modal-overlay';
            overlay.innerHTML = `
                <div class="modal-content title-input-modal">
                    <div class="modal-header">
                        <h3>세션 제목 입력</h3>
                        <button class="modal-close" title="닫기">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>일정 이름(세션 제목)</label>
                            <input type="text" class="form-control" id="sessionTitleInput" placeholder="예: 9월 2주차 고객 미팅 정리" value="${defaultValue || ''}">
                            <div class="form-text">저장 시 이 이름으로 분석 세션이 생성됩니다.</div>
                            <div id="sessionTitleError" class="form-text" style="color:#ef4444; display:none;">제목을 입력하세요.</div>
                        </div>
                    </div>
                    <div class="modal-footer" style="display:flex; gap:8px; justify-content:flex-end;">
                        <button class="btn btn-secondary" id="sessionTitleCancel">취소</button>
                        <button class="btn btn-primary" id="sessionTitleConfirm"><i class="fas fa-save"></i> 저장</button>
                    </div>
                </div>
            `;

            const close = () => { overlay.remove(); };
            overlay.querySelector('.modal-close').addEventListener('click', () => { close(); resolve(null); });
            overlay.addEventListener('click', (e) => { if (e.target === overlay) { close(); resolve(null); } });
            overlay.querySelector('#sessionTitleCancel').addEventListener('click', () => { close(); resolve(null); });
            overlay.querySelector('#sessionTitleConfirm').addEventListener('click', () => {
                const input = overlay.querySelector('#sessionTitleInput');
                const error = overlay.querySelector('#sessionTitleError');
                const value = (input.value || '').trim();
                if (!value) {
                    error.style.display = 'block';
                    input.focus();
                    return;
                }
                close();
                resolve(value);
            });
            document.body.appendChild(overlay);
            const input = overlay.querySelector('#sessionTitleInput');
            input.focus();
            input.select();
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    overlay.querySelector('#sessionTitleConfirm').click();
                } else if (e.key === 'Escape') {
                    overlay.querySelector('#sessionTitleCancel').click();
                }
            });
        });
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    // 인증 완료 후 초기화
    document.addEventListener('mufi-auth-completed', () => {
        window.analysisSection = new AnalysisSection();
    });
});