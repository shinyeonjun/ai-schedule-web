// MUFI Dashboard - Minimal Black & White Design
class Dashboard {
    constructor() {
        this.analysisResults = [];
        this.emailHistory = [];
        this.currentAnalysisData = null;
        this.contacts = [];
        this.selectedRecipients = [];
        this.selectedContacts = [];
        this.selectedICS = null;
        this.schedules = []; // 기존 일정들
        this.shareableSchedules = [];
        this.selectedShareSchedules = [];
        this.shareRecipients = [];
        this.selectedShareContacts = [];
        this.receivedSchedules = [];
        this.currentReceivedSchedule = null;
        this.selectedSchedulesForShare = [];
        this.currentFile = null; // 현재 업로드된 파일 저장
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadSampleData();
        
        // 기본 입력 방식을 파일 업로드로 설정
        this.switchInputMethod('file');
    }
    
    setupEventListeners() {
        // 탭 전환
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
        
        // 입력 방식 탭 전환
        document.querySelectorAll('.input-method-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchInputMethod(e.target.closest('.input-method-tab').dataset.method);
            });
        });
        
        
        
        // 파일 업로드
        const fileInput = document.getElementById('file-input');
        const fileUpload = document.getElementById('file-upload-area');
        
        if (fileUpload && fileInput) {
        fileUpload.addEventListener('click', () => {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', (e) => {
            this.handleFileUpload(e.target.files[0]);
        });
        
        // 드래그 앤 드롭
        fileUpload.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileUpload.classList.add('drag-over');
        });
        
        fileUpload.addEventListener('dragleave', () => {
            fileUpload.classList.remove('drag-over');
        });
        
        fileUpload.addEventListener('drop', (e) => {
            e.preventDefault();
            fileUpload.classList.remove('drag-over');
                
                // 파일이 있는 경우
                if (e.dataTransfer.files.length > 0) {
            this.handleFileUpload(e.dataTransfer.files[0]);
                }
                // 텍스트가 있는 경우 (복사한 텍스트를 드래그 앤 드롭)
                else if (e.dataTransfer.getData('text/plain')) {
                    const text = e.dataTransfer.getData('text/plain');
                    this.handleTextDrop(text);
                }
            });
        }
        
        // 파일 제거 버튼
        const clearFileBtn = document.getElementById('clear-file-btn');
        if (clearFileBtn) {
            clearFileBtn.addEventListener('click', () => {
                this.clearFile();
            });
        }
        
        // 분석 버튼 이벤트
        const analyzeBtn = document.getElementById('analyze-btn');
        const textAnalyzeBtn = document.getElementById('text-analyze-btn');
        const clearAllBtn = document.getElementById('clear-all-btn');
        
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => {
                const fileInput = document.getElementById('file-input');
                const file = this.currentFile || (fileInput && fileInput.files.length > 0 ? fileInput.files[0] : null);
                if (file) {
                    this.analyzeFile(file);
                }
            });
        }
        
        if (textAnalyzeBtn) {
            textAnalyzeBtn.addEventListener('click', () => {
                this.analyzeText();
            });
        }
        
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => {
                this.clearAllInput();
            });
        }
        
        // 텍스트 입력 카운터
        const callContentTextarea = document.getElementById('call-content');
        if (callContentTextarea) {
            // 입력 이벤트 (타이핑, 붙여넣기 등)
            callContentTextarea.addEventListener('input', (e) => {
                this.updateTextCounter(e.target.value.length);
                this.updateAnalyzeButton();
            });
            
            // 붙여넣기 이벤트 (더 정확한 처리)
            callContentTextarea.addEventListener('paste', (e) => {
                // 약간의 지연을 두고 텍스트 카운터 업데이트 (붙여넣기 완료 후)
                setTimeout(() => {
                    this.updateTextCounter(e.target.value.length);
                    this.updateAnalyzeButton();
                }, 10);
            });
            
            // 드래그 앤 드롭으로 텍스트 붙여넣기
            callContentTextarea.addEventListener('drop', (e) => {
                e.preventDefault();
                e.target.classList.remove('drag-over');
                
                const text = e.dataTransfer.getData('text/plain');
                if (text) {
                    // 현재 커서 위치에 텍스트 삽입
                    const start = e.target.selectionStart;
                    const end = e.target.selectionEnd;
                    const currentValue = e.target.value;
                    const newValue = currentValue.substring(0, start) + text + currentValue.substring(end);
                    
                    // 최대 길이 체크
                    if (newValue.length <= 10000) {
                        e.target.value = newValue;
                        e.target.setSelectionRange(start + text.length, start + text.length);
                        this.updateTextCounter(newValue.length);
                        this.updateAnalyzeButton();
                        
                        // 시각적 피드백
                        e.target.classList.add('pasting');
                        setTimeout(() => {
                            e.target.classList.remove('pasting');
                        }, 500);
                    } else {
                        this.showNotification('텍스트 길이 초과', '최대 10,000자까지 입력 가능합니다.', 'error');
                    }
                }
            });
            
            // 드래그 오버 이벤트
            callContentTextarea.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.target.classList.add('drag-over');
            });
            
            callContentTextarea.addEventListener('dragleave', (e) => {
                e.target.classList.remove('drag-over');
            });
            
            // 키보드 단축키 지원
            callContentTextarea.addEventListener('keydown', (e) => {
                // Ctrl+V 또는 Cmd+V (붙여넣기)
                if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
                    // 기본 붙여넣기 동작 후 카운터 업데이트
                    setTimeout(() => {
                        const newLength = e.target.value.length;
                        if (newLength > 10000) {
                            e.target.value = e.target.value.substring(0, 10000);
                            this.showNotification('텍스트 길이 초과', '최대 10,000자까지만 입력됩니다.', 'warning');
                        }
                        this.updateTextCounter(e.target.value.length);
                        this.updateAnalyzeButton();
                    }, 10);
                }
                
                // Ctrl+A 또는 Cmd+A (전체 선택)
                if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
                    // 기본 전체 선택 동작 허용
                }
            });
        }
        
        // 모달 클로즈
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });
    }
    
    switchTab(tabName) {
        // 모든 탭 비활성화
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        // 선택된 탭 활성화
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }
    
    switchInputMethod(method) {
        // 모든 입력 방식 탭 비활성화
        document.querySelectorAll('.input-method-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        
        document.querySelectorAll('.input-section').forEach(section => {
            section.classList.remove('active');
        });
        
        // 선택된 입력 방식 활성화
        document.querySelector(`[data-method="${method}"]`).classList.add('active');
        document.getElementById(`${method}-input-section`).classList.add('active');
        
        // 버튼 상태 업데이트
        this.updateAnalyzeButton();
    }
    

    
    updateTextCounter(length) {
        const textCount = document.getElementById('text-count');
        const textCounter = document.querySelector('.text-counter');
        const maxLength = 10000;
        
        if (textCount) {
            textCount.textContent = length.toLocaleString();
            
            // 색상 변경
            textCounter.classList.remove('warning', 'error');
            if (length > maxLength * 0.9) {
                textCounter.classList.add('error');
            } else if (length > maxLength * 0.8) {
                textCounter.classList.add('warning');
            }
        }
    }
    
    updateAnalyzeButton() {
        const activeMethod = document.querySelector('.input-method-tab.active')?.dataset.method;
        const analyzeBtn = document.getElementById('analyze-btn');
        const textAnalyzeBtn = document.getElementById('text-analyze-btn');
            const fileInput = document.getElementById('file-input');
            const callContent = document.getElementById('call-content');
        

        
        // 파일 업로드 분석 버튼 상태 (항상 체크)
        if (analyzeBtn) {
            const hasFile = this.currentFile !== null || (fileInput && fileInput.files && fileInput.files.length > 0);
            analyzeBtn.disabled = !hasFile;
        }
        
        // 텍스트 분석 버튼 상태 (항상 체크)
            if (textAnalyzeBtn) {
                        const hasContent = callContent && callContent.value.trim().length > 0;
            textAnalyzeBtn.disabled = !hasContent;
            }
        
        // 활성 탭에 따라 버튼 표시/숨김
        if (activeMethod === 'file') {
            if (analyzeBtn) analyzeBtn.style.display = 'inline-flex';
            if (textAnalyzeBtn) textAnalyzeBtn.style.display = 'none';
        } else if (activeMethod === 'text') {
            if (analyzeBtn) analyzeBtn.style.display = 'none';
            if (textAnalyzeBtn) textAnalyzeBtn.style.display = 'inline-flex';
        }
    }
    
    // 텍스트 드롭 처리 (파일 업로드 영역에서만 사용)
    handleTextDrop(text) {
        if (!text || text.trim().length === 0) return;
        
        // 텍스트 길이 체크
        if (text.length > 10000) {
            this.showNotification('텍스트 길이 초과', '최대 10,000자까지 입력 가능합니다. 직접 입력 탭을 사용해주세요.', 'error');
            return;
        }
        
        // 직접 입력 탭으로 전환하고 텍스트 설정
        this.switchInputMethod('text');
        
        // 텍스트 영역에 내용 설정
        const callContentTextarea = document.getElementById('call-content');
        if (callContentTextarea) {
            callContentTextarea.value = text;
            this.updateTextCounter(text.length);
            this.updateAnalyzeButton();
            
            // 포커스 설정
            callContentTextarea.focus();
            
            this.showNotification('텍스트 붙여넣기 완료', '직접 입력 탭으로 전환되어 텍스트가 붙여넣어졌습니다.', 'success');
        }
    }
    
    // 텍스트 파일 읽기 (미리보기용)
    readTextFile(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const text = e.target.result;
            if (text && text.trim().length > 0) {
                // 텍스트 길이 체크
                if (text.length > 10000) {
                    this.showNotification('파일 내용 확인', 'TXT 파일이 10,000자를 초과합니다. 파일 업로드 분석을 사용하여 전체 내용을 분석할 수 있습니다.', 'info');
                    return;
                }
                
                this.showNotification('TXT 파일 확인', 'TXT 파일이 업로드되었습니다. 파일 분석을 진행하거나, 직접 입력 탭에서 텍스트를 수정할 수 있습니다.', 'success');
            }
        };
        reader.onerror = () => {
            this.showNotification('파일 읽기 오류', '텍스트 파일을 읽는 중 오류가 발생했습니다.', 'error');
        };
        reader.readAsText(file, 'UTF-8');
    }

    
    handleFileUpload(file) {
        if (!file) return;
        
        // 파일 크기 체크 (10MB 제한)
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            this.showNotification('파일 크기 초과', '파일 크기는 10MB 이하여야 합니다.', 'error');
            return;
        }
        
        // 파일 형식 체크
        const allowedTypes = ['text/plain', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        if (!allowedTypes.includes(file.type) && !file.name.match(/\.(txt|pdf|docx)$/i)) {
            this.showNotification('지원하지 않는 형식', 'TXT, PDF, DOCX 파일만 업로드 가능합니다.', 'error');
            return;
        }
        
        // TXT 파일인 경우 내용을 읽어서 직접 입력 영역에도 표시
        if (file.type === 'text/plain' || file.name.toLowerCase().endsWith('.txt')) {
            this.readTextFile(file);
        }
        
        const fileUpload = document.getElementById('file-upload-area');
        const fileInfo = document.getElementById('file-info');
        const fileName = document.getElementById('file-name');
        const fileSize = document.getElementById('file-size');
        

        
        // 파일 정보 표시
        fileName.textContent = file.name;
        fileSize.textContent = `${(file.size / 1024 / 1024).toFixed(2)}MB`;
        
        // UI 업데이트
        fileUpload.style.display = 'none';
        fileInfo.style.display = 'flex';
        
        // 현재 파일 저장
        this.currentFile = file;
        
        // 분석 버튼 활성화
        this.updateAnalyzeButton();
        
        this.showNotification('파일 업로드 완료', `${file.name} 파일이 업로드되었습니다.`);
    }
    
    async analyzeFile(file) {
        const analyzeBtn = document.getElementById('analyze-btn');
        
        try {
            // 분석 시작 상태로 변경
            this.setAnalysisState('analyzing');
        analyzeBtn.textContent = '분석 중...';
        analyzeBtn.disabled = true;
        
            // FormData 생성
            const formData = new FormData();
            formData.append('file', file);
            
            // 새로운 API 엔드포인트 사용 (DB 저장)
            const response = await fetch('/api/analyze/file', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '파일 분석에 실패했습니다.');
            }
            
            const result = await response.json();
            
            // 분석 결과 표시 (새로운 형식)
            if (result.success && result.data) {
                this.displayAnalysisResultFromDB(result.data);
                this.showNotification('분석 완료', '통화 내용 분석이 완료되고 저장되었습니다.');
            } else {
                throw new Error(result.message || '분석 결과를 받을 수 없습니다.');
            }
            
        } catch (error) {
            console.error('파일 분석 오류:', error);
            this.setAnalysisState('error');
            this.showNotification('분석 오류', `파일 분석 중 오류가 발생했습니다: ${error.message}`, 'error');
        } finally {
            analyzeBtn.textContent = '분석 시작';
            this.updateAnalyzeButton();
        }
    }
    
    async analyzeText() {
        const textAnalyzeBtn = document.getElementById('text-analyze-btn');
        const callContent = document.getElementById('call-content');
        
        if (!callContent.value.trim()) {
            this.showNotification('내용 없음', '분석할 통화 내용을 입력해주세요.', 'error');
            return;
        }
        
        try {
            // 분석 시작 상태로 변경
            this.setAnalysisState('analyzing');
            textAnalyzeBtn.textContent = '분석 중...';
            textAnalyzeBtn.disabled = true;
            
            // 새로운 API 엔드포인트 사용 (DB 저장)
            const response = await fetch('/api/analyze/text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: callContent.value.trim()
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '텍스트 분석에 실패했습니다.');
            }
            
            const result = await response.json();
            
            // 분석 결과 표시 (새로운 형식)
            if (result.success && result.data) {
                this.displayAnalysisResultFromDB(result.data);
                this.showNotification('분석 완료', '통화 내용 분석이 완료되고 저장되었습니다.');
            } else {
                throw new Error(result.message || '분석 결과를 받을 수 없습니다.');
            }
            
        } catch (error) {
            console.error('텍스트 분석 오류:', error);
            this.setAnalysisState('error');
            this.showNotification('분석 오류', `텍스트 분석 중 오류가 발생했습니다: ${error.message}`, 'error');
        } finally {
            textAnalyzeBtn.textContent = '분석 시작';
            this.updateAnalyzeButton();
        }
    }
    
    clearFile() {
        const fileUpload = document.getElementById('file-upload-area');
        const fileInfo = document.getElementById('file-info');
        const fileInput = document.getElementById('file-input');
        
        // UI 초기화
        if (fileUpload) fileUpload.style.display = 'block';
        if (fileInfo) fileInfo.style.display = 'none';
        if (fileInput) fileInput.value = '';
        
        // 현재 파일 초기화
        this.currentFile = null;
        
        // 분석 버튼 비활성화
        this.updateAnalyzeButton();
    }
    
    clearAllInput() {
        const activeMethod = document.querySelector('.input-method-tab.active')?.dataset.method;
        
        if (activeMethod === 'file') {
            this.clearFile();
            this.showNotification('파일 제거 완료', '업로드된 파일이 제거되었습니다.');
        } else if (activeMethod === 'text') {
            const callContent = document.getElementById('call-content');
            if (callContent) {
                callContent.value = '';
                this.updateTextCounter(0);
                this.updateAnalyzeButton();
            }
            this.showNotification('텍스트 초기화 완료', '입력된 텍스트가 초기화되었습니다.');
        }
        
        // 분석 결과 초기화
        this.clearAnalysisResults();
    }
    
    clearAnalysisResults() {
        // 분석 상태를 초기 상태로 되돌리기
        this.setAnalysisState('waiting');
        
        // 분석 결과 컨테이너 초기화
        const summaryValue = document.getElementById('summary-value');
        const descriptionValue = document.getElementById('description-value');
        const locationValue = document.getElementById('location-value');
        const startdateValue = document.getElementById('startdate-value');
        const enddateValue = document.getElementById('enddate-value');
        const participantsList = document.getElementById('participants-list');
        const actionsList = document.getElementById('actions-list');
        
        if (summaryValue) summaryValue.textContent = '분석 후 요약이 여기에 표시됩니다.';
        if (descriptionValue) descriptionValue.textContent = '분석 후 상세 설명이 여기에 표시됩니다.';
        if (locationValue) locationValue.textContent = '분석 후 장소가 여기에 표시됩니다.';
        if (startdateValue) startdateValue.textContent = '분석 후 시작일시가 여기에 표시됩니다.';
        if (enddateValue) enddateValue.textContent = '분석 후 종료일시가 여기에 표시됩니다.';
        
        // 참석자 목록 초기화
        if (participantsList) {
            participantsList.innerHTML = `
                <div class="participants-empty">
                    <span class="empty-icon">👤</span>
                    <span class="empty-text">참석자 정보가 분석되면 여기에 표시됩니다</span>
                </div>
            `;
        }
        
        // 액션 아이템 초기화
        if (actionsList) {
            actionsList.innerHTML = `
                <div class="actions-empty">
                    <span class="empty-icon">📋</span>
                    <span class="empty-text">액션 아이템이 분석되면 여기에 표시됩니다</span>
                </div>
            `;
        }
        
        // 카운터 초기화
        this.updateParticipantsCount(0);
        this.updateActionsCount(0);
    }
    
    displayAnalysisResult(type, source, apiResult = null) {
        let analysisData;
        
        if (apiResult) {
            // 실제 API 결과 사용 - DB에서 불러온 데이터 형태로 변환
            analysisData = {
                id: apiResult.id,
                summary: apiResult.summary,
                description: apiResult.description,
                location: apiResult.schedules?.[0]?.location || '',
                startdate: this.formatScheduleDateTime(apiResult.schedules?.[0]),
                enddate: this.formatScheduleEndDateTime(apiResult.schedules?.[0]),
                participants: apiResult.participants || [],
                actions: apiResult.actions || []
            };
        } else {
            // 기본값 (API 호출 실패 시)
            analysisData = {
                summary: type === 'file' ? 
                    `업로드된 파일 "${source}"에 대한 통화 분석 결과입니다. 주요 안건과 결정사항을 정리했습니다.` :
                    `통화 내용을 분석한 결과입니다. 주요 논의사항과 향후 계획을 요약했습니다.`,
                description: type === 'file' ?
                    '주요 요구사항 검토, 일정 계획 수립, 역할 분담에 대해 논의했습니다. 다음 단계 진행을 위한 구체적인 액션 아이템들이 도출되었습니다.' :
                    '프로젝트 진행 상황 점검과 향후 계획에 대해 논의했습니다. 팀 간 협업 방안과 일정 조정이 필요한 부분들을 확인했습니다.',
                location: type === 'file' ? '회의실 A (본사 3층)' : '온라인 회의 (Zoom)',
                startdate: '2024-01-22 14:00',
                enddate: '2024-01-22 15:30',
                participants: [
                    { name: "김대리", email: "kim@company.com", role: "개발팀" },
                    { name: "이과장", email: "lee@company.com", role: "기획팀" }
                ],
                actions: [
                    { 
                        text: "프로젝트 일정 검토 및 마일스톤 설정", 
                        assignee: "김대리", 
                        due_date: "2024-01-25",
                        is_completed: false
                    },
                    { 
                        text: "클라이언트 요구사항 문서 작성", 
                        assignee: "이과장", 
                        due_date: "2024-01-26",
                        is_completed: false
                    }
                ]
            };
        }
        
        this.renderNewAnalysisResult(analysisData);
        
        // 분석 결과 저장
        this.currentAnalysisData = analysisData;
        this.analysisResults.push({
            type: type,
            source: type === 'file' ? source : '직접 입력',
            timestamp: new Date(),
            data: analysisData
        });
    }
    
    renderNewAnalysisResult(data) {
        // 분석 상태를 완료로 변경
        this.setAnalysisState('complete');
        
        // 각 섹션별로 데이터 업데이트
        this.updateSummarySection(data.summary);
        this.updateScheduleSection(data);
        this.updateDescriptionSection(data.description);
        this.updateParticipantsSection(data.participants);
        this.updateActionsSection(data.actions);
        
        // 수정 버튼 활성화
        this.enableEditButtons();
    }
    
    setAnalysisState(state) {
        const emptyState = document.getElementById('analysis-empty-state');
        const loadingState = document.getElementById('analysis-loading-state');
        const completeState = document.getElementById('analysis-complete-state');
        const statusBadge = document.querySelector('.analysis-status .status-badge');
        
        // 모든 상태 숨기기
        if (emptyState) emptyState.style.display = 'none';
        if (loadingState) loadingState.style.display = 'none';
        if (completeState) completeState.style.display = 'none';
        
        // 상태에 따라 표시
        switch(state) {
            case 'waiting':
                if (emptyState) emptyState.style.display = 'flex';
                if (statusBadge) {
                    statusBadge.className = 'status-badge status-waiting';
                    statusBadge.textContent = '분석 대기중';
                }
                break;
            case 'analyzing':
                if (loadingState) loadingState.style.display = 'flex';
                if (statusBadge) {
                    statusBadge.className = 'status-badge status-analyzing';
                    statusBadge.textContent = '분석 진행중';
                }
                break;
            case 'complete':
                if (completeState) completeState.style.display = 'flex';
                if (statusBadge) {
                    statusBadge.className = 'status-badge status-complete';
                    statusBadge.textContent = '분석 완료';
                }
                break;
            case 'error':
                if (emptyState) emptyState.style.display = 'flex';
                if (statusBadge) {
                    statusBadge.className = 'status-badge status-error';
                    statusBadge.textContent = '분석 실패';
                }
                break;
        }
    }
    
    updateSummarySection(summary) {
        const summaryValue = document.getElementById('summary-value');
        if (summaryValue) {
            summaryValue.textContent = summary;
        }
    }
    
    updateScheduleSection(data) {
        const locationValue = document.getElementById('location-value');
        const startdateValue = document.getElementById('startdate-value');
        const enddateValue = document.getElementById('enddate-value');
        
        if (locationValue) locationValue.textContent = data.location;
        if (startdateValue) startdateValue.textContent = this.formatDateTime(data.startdate);
        if (enddateValue) enddateValue.textContent = this.formatDateTime(data.enddate);
    }
    
    updateDescriptionSection(description) {
        const descriptionValue = document.getElementById('description-value');
        if (descriptionValue) {
            descriptionValue.textContent = description;
        }
    }
    
    updateParticipantsSection(participants) {
        const participantsList = document.getElementById('participants-list');
        if (!participantsList || !participants || participants.length === 0) {
            return;
        }
        
        participantsList.innerHTML = participants.map(participant => `
            <div class="participant-item">
                            <div class="participant-info">
                    <div class="participant-avatar">
                        ${participant.name.charAt(0)}
                            </div>
                    <div class="participant-details">
                        <div class="participant-name">${participant.name}</div>
                        ${participant.role ? `<div class="participant-role">${participant.role}</div>` : ''}
                    </div>
                </div>
                ${participant.email ? `<div class="participant-email">${participant.email}</div>` : ''}
            </div>
        `).join('');
        
        this.updateParticipantsCount(participants.length);
    }
    
    updateActionsSection(actions) {
        const actionsList = document.getElementById('actions-list');
        if (!actionsList || !actions || actions.length === 0) {
            return;
        }
        
        actionsList.innerHTML = actions.map((action, index) => `
            <div class="action-item">
                <input type="checkbox" class="action-checkbox" ${action.is_completed ? 'checked' : ''} 
                       onchange="toggleActionComplete(${index})">
                <div class="action-content">
                    <div class="action-text">${action.text}</div>
                    <div class="action-meta">
                        <div class="action-assignee">
                            <span>👤</span>
                            <span>${action.assignee}</span>
                            </div>
                        <div class="action-due">
                            <span>📅</span>
                            <span>${this.formatDate(action.due_date)}</span>
                        </div>
                </div>
            </div>
            </div>
        `).join('');
        
        this.updateActionsCount(actions.length);
    }
    
    updateParticipantsCount(count) {
        const participantsCount = document.getElementById('participants-count');
        if (participantsCount) {
            participantsCount.textContent = `${count}명`;
        }
    }
    
    updateActionsCount(count) {
        const actionsCount = document.getElementById('actions-count');
        if (actionsCount) {
            actionsCount.textContent = `${count}개`;
        }
    }
    
    enableEditButtons() {
        const editButtons = document.querySelectorAll('.field-edit-btn');
        editButtons.forEach(button => {
            button.disabled = false;
        });
    }
    
    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('ko-KR', {
            month: 'long',
            day: 'numeric'
        });
    }
    
    renderAnalysisWithTabs(data) {
        // 기존 함수는 호환성을 위해 유지하되, 새로운 함수로 리다이렉트
        this.renderNewAnalysisResult(data);
    }
    
    toggleActionComplete(actionIndex) {
        const actionElement = document.getElementById(`action-${actionIndex}`);
        const checkbox = actionElement?.querySelector('.action-checkbox');
        
        if (!checkbox) return;
        
        const isCompleted = checkbox.checked;
        
        // UI 업데이트
        if (isCompleted) {
            actionElement.classList.add('completed');
        } else {
            actionElement.classList.remove('completed');
        }
        
        // 서버에 상태 업데이트 (DB 저장)
        this.updateActionStatus(actionIndex, isCompleted);
        
        // 현재 분석 데이터의 액션 상태 업데이트
        if (this.currentAnalysisData && this.currentAnalysisData.actions) {
            this.currentAnalysisData.actions[actionIndex].is_completed = isCompleted;
            
            // 알림 표시
            const actionText = this.currentAnalysisData.actions[actionIndex].text;
            const status = isCompleted ? '완료' : '미완료';
            this.showNotification('액션 아이템 업데이트', `"${actionText}" 항목이 ${status}로 변경되었습니다.`);
        }
    }
    
    renderParticipants(participants) {
        return participants.map(participant => `
            <div class="participant-item">
                <div class="participant-name">${participant.name}</div>
                ${participant.role ? `<div class="participant-role">${participant.role}</div>` : ''}
                ${participant.email ? `<div class="participant-email">${participant.email}</div>` : ''}
            </div>
        `).join('');
    }
    
    renderScheduleTabs(schedules) {
        return schedules.map((schedule, index) => `
            <div class="schedule-tab-item ${index === 0 ? 'active' : ''}" data-tab="${index}">
                <div class="tab-title">${schedule.summary}</div>
                <div class="tab-subtitle">${schedule.type} • ${schedule.assignees.join(', ') || '담당자 미정'}</div>
            </div>
        `).join('');
    }
    
    renderScheduleFields(schedule, index) {
        return `
            <div class="analysis-fields-container">
                <div class="analysis-field">
                    <div class="analysis-field-header">
                        <label class="analysis-field-label">📝 Summary (요약)</label>
                        <div class="analysis-field-actions">
                            <button class="btn btn-outline btn-sm field-edit-btn" onclick="editScheduleField(${index}, 'summary')">
                                <span id="summary-btn-${index}">수정</span>
                            </button>
                        </div>
                    </div>
                    <div class="analysis-field-value" contenteditable="false" data-field="summary" id="summary-value-${index}">${schedule.summary}</div>
                </div>
                
                <div class="analysis-field">
                    <div class="analysis-field-header">
                        <label class="analysis-field-label">📄 Description (설명)</label>
                        <div class="analysis-field-actions">
                            <button class="btn btn-outline btn-sm field-edit-btn" onclick="editScheduleField(${index}, 'description')">
                                <span id="description-btn-${index}">수정</span>
                            </button>
                        </div>
                    </div>
                    <div class="analysis-field-value multiline" contenteditable="false" data-field="description" id="description-value-${index}">${schedule.description}</div>
                </div>
                
                <div class="analysis-field">
                    <div class="analysis-field-header">
                        <label class="analysis-field-label">📍 Location (장소)</label>
                        <div class="analysis-field-actions">
                            <button class="btn btn-outline btn-sm field-edit-btn" onclick="editScheduleField(${index}, 'location')">
                                <span id="location-btn-${index}">수정</span>
                            </button>
                        </div>
                    </div>
                    <div class="analysis-field-value" contenteditable="false" data-field="location" id="location-value-${index}">${schedule.location}</div>
                </div>
                
                <div class="analysis-field">
                    <div class="analysis-field-header">
                        <label class="analysis-field-label">⏰ Start Date (시작일시)</label>
                        <div class="analysis-field-actions">
                            <button class="btn btn-outline btn-sm field-edit-btn" onclick="editScheduleField(${index}, 'startdate')">
                                <span id="startdate-btn-${index}">수정</span>
                            </button>
                        </div>
                    </div>
                    <div class="analysis-field-value date-field" contenteditable="false" data-field="startdate" id="startdate-value-${index}">${this.formatDateTime(schedule.startdate)}</div>
                </div>
                
                <div class="analysis-field">
                    <div class="analysis-field-header">
                        <label class="analysis-field-label">⏰ End Date (종료일시)</label>
                        <div class="analysis-field-actions">
                            <button class="btn btn-outline btn-sm field-edit-btn" onclick="editScheduleField(${index}, 'enddate')">
                                <span id="enddate-btn-${index}">수정</span>
                            </button>
                        </div>
                    </div>
                    <div class="analysis-field-value date-field" contenteditable="false" data-field="enddate" id="enddate-value-${index}">${this.formatDateTime(schedule.enddate)}</div>
                </div>
                
                <div class="analysis-field">
                    <div class="analysis-field-header">
                        <label class="analysis-field-label">👤 Assignees (담당자)</label>
                        <div class="analysis-field-actions">
                            <button class="btn btn-outline btn-sm field-edit-btn" onclick="editScheduleField(${index}, 'assignees')">
                                <span id="assignees-btn-${index}">수정</span>
                            </button>
                        </div>
                    </div>
                    <div class="analysis-field-value" contenteditable="false" data-field="assignees" id="assignees-value-${index}">${schedule.assignees.join(', ') || '담당자 미정'}</div>
                </div>
                
                <div class="analysis-field">
                    <div class="analysis-field-header">
                        <label class="analysis-field-label">🏷️ Type (유형)</label>
                        <div class="analysis-field-actions">
                            <button class="btn btn-outline btn-sm field-edit-btn" onclick="editScheduleField(${index}, 'type')">
                                <span id="type-btn-${index}">수정</span>
                            </button>
                        </div>
                    </div>
                    <div class="analysis-field-value" contenteditable="false" data-field="type" id="type-value-${index}">${this.getTypeDisplayName(schedule.type)}</div>
                </div>
            </div>
        `;
    }
    
    getTypeDisplayName(type) {
        const typeMap = {
            'meeting': '회의',
            'task': '업무',
            'deadline': '마감일'
        };
        return typeMap[type] || type;
    }
    
    formatDateTime(dateTimeStr) {
        const date = new Date(dateTimeStr);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        
        return `${year}-${month}-${day} ${hours}:${minutes}`;
    }
    
    formatScheduleDateTime(schedule) {
        if (!schedule) return '';
        
        let dateTimeStr = '';
        if (schedule.start_date) {
            dateTimeStr = schedule.start_date;
            if (schedule.start_time) {
                dateTimeStr += ` ${schedule.start_time}`;
            }
        }
        return dateTimeStr;
    }

    formatScheduleEndDateTime(schedule) {
        if (!schedule) return '';
        
        let dateTimeStr = '';
        if (schedule.end_date) {
            dateTimeStr = schedule.end_date;
            if (schedule.end_time) {
                dateTimeStr += ` ${schedule.end_time}`;
            }
        }
        return dateTimeStr;
    }
    
    editField(fieldName) {
        const fieldValue = document.getElementById(`${fieldName}-value`);
        const buttonSpan = document.getElementById(`${fieldName}-btn`);
        const actionContainer = fieldValue.closest('.analysis-field').querySelector('.analysis-field-actions');
        
        const isEditing = buttonSpan.textContent === '저장';
        
        if (isEditing) {
            // 저장 모드 -> 보기 모드
            fieldValue.contentEditable = 'false';
            fieldValue.classList.remove('editing');
            
            // 수정된 데이터 수집 및 저장
            this.saveFieldData(fieldName, fieldValue.textContent.trim());
            
            // 버튼 상태 변경
            actionContainer.innerHTML = `
                <button class="btn btn-outline btn-sm field-edit-btn" onclick="editField('${fieldName}')">
                    <span id="${fieldName}-btn">수정</span>
                </button>
            `;
        } else {
            // 보기 모드 -> 수정 모드
            fieldValue.contentEditable = 'true';
            fieldValue.classList.add('editing');
            fieldValue.focus();
            
            // 저장/취소 버튼으로 변경
            actionContainer.innerHTML = `
                <button class="btn btn-sm field-edit-btn save" onclick="editField('${fieldName}')">
                    <span id="${fieldName}-btn">저장</span>
                </button>
                <button class="btn btn-sm field-edit-btn cancel" onclick="cancelEdit('${fieldName}')">
                    취소
                </button>
            `;
            
            // 원본 데이터 백업
            fieldValue.dataset.originalValue = fieldValue.textContent.trim();
            
            this.showNotification('수정 모드', `${this.getFieldDisplayName(fieldName)}을(를) 수정할 수 있습니다.`);
        }
    }
    
    cancelEdit(fieldName) {
        const fieldValue = document.getElementById(`${fieldName}-value`);
        const actionContainer = fieldValue.closest('.analysis-field').querySelector('.analysis-field-actions');
        
        // 원본 데이터 복원
        fieldValue.textContent = fieldValue.dataset.originalValue || '';
        fieldValue.contentEditable = 'false';
        fieldValue.classList.remove('editing');
        
        // 버튼 상태 변경
        actionContainer.innerHTML = `
            <button class="btn btn-outline btn-sm field-edit-btn" onclick="editField('${fieldName}')">
                <span id="${fieldName}-btn">수정</span>
            </button>
        `;
        
        this.showNotification('취소됨', `${this.getFieldDisplayName(fieldName)} 수정이 취소되었습니다.`);
    }
    
    async saveFieldData(fieldName, value) {
        if (!this.currentAnalysisData || !this.currentAnalysisData.id) {
            this.showNotification('저장 오류', '분석 결과 ID가 없습니다.', 'error');
            return;
        }

        try {
            // 로컬 데이터 업데이트
            if (fieldName === 'summary') {
                this.currentAnalysisData.summary = value;
            } else if (fieldName === 'description') {
                this.currentAnalysisData.description = value;
            } else if (fieldName === 'location') {
                this.currentAnalysisData.location = value;
            } else if (fieldName === 'startdate') {
                this.currentAnalysisData.startdate = value;
            } else if (fieldName === 'enddate') {
                this.currentAnalysisData.enddate = value;
            }

            // 서버에 저장
            const response = await fetch(`/api/results/${this.currentAnalysisData.id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    field: fieldName,
                    value: value
                })
            });

            if (response.ok) {
                this.showNotification('저장 완료', `${this.getFieldDisplayName(fieldName)}이(가) 저장되었습니다.`);
            } else {
                throw new Error('서버 저장 실패');
            }
        } catch (error) {
            console.error('필드 저장 오류:', error);
            this.showNotification('저장 오류', '데이터 저장 중 오류가 발생했습니다.', 'error');
        }
    }
    
    getFieldDisplayName(fieldName) {
        const fieldNames = {
            'summary': '요약',
            'description': '설명',
            'location': '장소',
            'startdate': '시작일시',
            'enddate': '종료일시'
        };
        return fieldNames[fieldName] || fieldName;
    }
    
    collectAnalysisData() {
        const fieldValues = document.querySelectorAll('.analysis-field-value');
        const updatedData = {};
        
        fieldValues.forEach(field => {
            const fieldName = field.getAttribute('data-field');
            let value = field.textContent.trim();
            
            // 날짜 필드의 경우 ISO 형식으로 변환
            if (fieldName === 'startdate' || fieldName === 'enddate') {
                value = this.parseDateTime(value);
            }
            
            updatedData[fieldName] = value;
        });
        
        this.currentAnalysisData = updatedData;
        return updatedData;
    }
    
    parseDateTime(dateTimeStr) {
        // "2024-01-22 14:00" 형식을 "2024-01-22T14:00:00" 형식으로 변환
        const cleanStr = dateTimeStr.replace(/\s+/g, ' ').trim();
        const parts = cleanStr.split(' ');
        
        if (parts.length >= 2) {
            const datePart = parts[0];
            const timePart = parts[1];
            return `${datePart}T${timePart}:00`;
        }
        
        return dateTimeStr;
    }
    
    async generateICS() {
        if (!this.currentSchedules || this.currentSchedules.length === 0) {
            this.showNotification('오류', '분석 결과가 없습니다. 먼저 통화 내용을 분석해주세요.', 'error');
            return;
        }
        
        try {
            // 새로운 API 구조에 맞춰 schedules 배열로 전송
            const requestData = {
                schedules: this.currentSchedules
            };
            
            // API 호출
            const response = await fetch('/api/generate-ics', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'ICS 생성에 실패했습니다.');
            }
            
            const result = await response.json();
            
            // ICS 미리보기 표시
            const previewSection = document.getElementById('ics-preview-section');
            const previewContent = document.getElementById('ics-preview-content');
            
            if (previewSection && previewContent) {
                previewContent.textContent = result.ics_content;
                previewSection.style.display = 'block';
            }
            
            // ICS 내용 저장 (다운로드용)
            this.currentICSContent = result.ics_content;
            this.currentICSFilename = result.filename;
            
            this.showNotification('ICS 생성 완료', 'ICS 파일이 생성되었습니다.');
            
        } catch (error) {
            console.error('ICS 생성 오류:', error);
            this.showNotification('ICS 생성 오류', `ICS 생성 중 오류가 발생했습니다: ${error.message}`, 'error');
            
            // 오류 시 기본 ICS 생성 (첫 번째 일정 사용)
            const firstSchedule = this.currentSchedules[0];
            const icsContent = this.createICSContent(firstSchedule);
            
            const previewSection = document.getElementById('ics-preview-section');
            const previewContent = document.getElementById('ics-preview-content');
            
            if (previewSection && previewContent) {
                previewContent.textContent = icsContent;
                previewSection.style.display = 'block';
            }
        }
    }
    
    createICSContent(data) {
        const now = new Date();
        const timestamp = now.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
        
        const startDate = new Date(data.startdate);
        const endDate = new Date(data.enddate);
        
        const formatICSDate = (date) => {
            return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
        };
        
        return `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MUFI//MUFI Calendar//KO
BEGIN:VEVENT
UID:${timestamp}@mufi.com
DTSTAMP:${timestamp}
DTSTART:${formatICSDate(startDate)}
DTEND:${formatICSDate(endDate)}
SUMMARY:${data.summary}
DESCRIPTION:${data.description}
LOCATION:${data.location}
END:VEVENT
END:VCALENDAR`;
    }
    
    async downloadICS() {
        if (!this.currentAnalysisData) {
            this.showNotification('오류', '다운로드할 ICS 데이터가 없습니다.', 'error');
            return;
        }
        
        try {
            // API 호출
            const response = await fetch('/api/download-ics', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.currentAnalysisData)
            });
            
            if (!response.ok) {
                throw new Error('ICS 다운로드에 실패했습니다.');
            }
            
            // 파일 다운로드
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            
            // 파일명 추출 (Content-Disposition 헤더에서)
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'schedule.ics';
            if (contentDisposition) {
                const matches = contentDisposition.match(/filename="([^"]+)"/);
                if (matches) {
                    filename = matches[1];
                }
            }
            
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showNotification('다운로드 완료', 'ICS 파일이 다운로드되었습니다.');
            
        } catch (error) {
            console.error('ICS 다운로드 오류:', error);
            this.showNotification('다운로드 오류', `ICS 다운로드 중 오류가 발생했습니다: ${error.message}`, 'error');
            
            // 오류 시 기본 다운로드
            const icsContent = this.createICSContent(this.currentAnalysisData);
            const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `일정_${new Date().toISOString().split('T')[0]}.ics`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    }
    
    resetAnalysis() {
        // 5개 칸을 초기 상태로 되돌리기
        document.getElementById('summary-value').textContent = '분석 후 요약이 여기에 표시됩니다.';
        document.getElementById('description-value').textContent = '분석 후 상세 설명이 여기에 표시됩니다.';
        document.getElementById('location-value').textContent = '분석 후 장소가 여기에 표시됩니다.';
        document.getElementById('startdate-value').textContent = '분석 후 시작일시가 여기에 표시됩니다.';
        document.getElementById('enddate-value').textContent = '분석 후 종료일시가 여기에 표시됩니다.';
        
        // 모든 필드를 readonly 상태로 변경
        const fieldValues = document.querySelectorAll('.analysis-field-value');
        fieldValues.forEach(field => {
            field.classList.add('readonly');
            field.contentEditable = 'false';
            field.classList.remove('editing');
        });
        
        // 모든 수정 버튼 비활성화
        const editButtons = document.querySelectorAll('.field-edit-btn');
        editButtons.forEach(button => {
            button.disabled = true;
        });
        
        // 수정 버튼 텍스트 초기화
        document.getElementById('summary-btn').textContent = '수정';
        document.getElementById('description-btn').textContent = '수정';
        document.getElementById('location-btn').textContent = '수정';
        document.getElementById('startdate-btn').textContent = '수정';
        document.getElementById('enddate-btn').textContent = '수정';
        
        // 액션 버튼들 초기화
        const actionContainers = document.querySelectorAll('.analysis-field-actions');
        actionContainers.forEach((container, index) => {
            const fieldNames = ['summary', 'description', 'location', 'startdate', 'enddate'];
            const fieldName = fieldNames[index];
            container.innerHTML = `
                <button class="btn btn-outline btn-sm field-edit-btn" onclick="editField('${fieldName}')" disabled>
                    <span id="${fieldName}-btn">수정</span>
                </button>
            `;
        });
        
        // ICS 미리보기 숨기기
        const previewSection = document.getElementById('ics-preview-section');
        previewSection.style.display = 'none';
        
        this.currentAnalysisData = null;
        this.showNotification('초기화 완료', '분석 결과가 초기화되었습니다.');
    }
    
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        modal.classList.add('active');
    }
    
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        modal.classList.remove('active');
    }
    

    
    editAnalysis() {
        this.showNotification('편집 모드', '분석 결과를 편집할 수 있습니다.');
    }
    
    sendEmail() {
        const to = document.getElementById('email-to').value;
        const subject = document.getElementById('email-subject').value;
        const content = document.getElementById('email-content').value;
        
        if (!to || !subject || !content) {
            this.showNotification('오류', '필수 항목을 모두 입력해주세요.');
            return;
        }
        
        // 이메일 발송 로직
        this.showNotification('이메일 발송', '이메일이 성공적으로 발송되었습니다.');
        
        // 발송 내역에 추가
        const emailItem = {
            id: Date.now(),
            to,
            subject,
            content,
            timestamp: new Date().toLocaleString(),
            status: 'sent'
        };
        
        this.emailHistory.push(emailItem);
        this.updateEmailList();
        
        // 폼 초기화
        document.getElementById('email-form').reset();
    }
    
    previewEmail() {
        this.showNotification('미리보기', '이메일 미리보기 기능은 준비 중입니다.');
    }
    
    updateEmailList() {
        const emailList = document.getElementById('email-list');
        
        // 요소가 없으면 안전하게 리턴
        if (!emailList) {
            return;
        }
        
        const sampleEmails = [
            {
                subject: '프로젝트 회의 일정',
                to: 'john@example.com',
                timestamp: '2024-01-15 09:30',
                status: 'sent'
            },
            {
                subject: '클라이언트 미팅 안내',
                to: 'client@company.com',
                timestamp: '2024-01-14 16:45',
                status: 'sent'
            },
            {
                subject: '팀 워크샵 참석 요청',
                to: 'team@company.com',
                timestamp: '2024-01-13 11:20',
                status: 'pending'
            }
        ];
        
        emailList.innerHTML = sampleEmails.map(email => `
            <div class="email-item">
                <div class="email-info">
                    <h4>${email.subject}</h4>
                    <p>${email.to} • ${email.timestamp}</p>
                </div>
                <span class="email-status ${email.status}">
                    ${email.status === 'sent' ? '발송완료' : '대기중'}
                </span>
            </div>
        `).join('');
    }
    
    showNotification(title, message) {
        const notification = document.getElementById('notification');
        const notificationTitle = document.getElementById('notification-title');
        const notificationMessage = document.getElementById('notification-message');
        
        // 요소가 없으면 안전하게 리턴
        if (!notification || !notificationTitle || !notificationMessage) {
            console.log('알림:', title, message);
            return;
        }
        
        notificationTitle.textContent = title;
        notificationMessage.textContent = message;
        
        notification.classList.add('show');
        
        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }
    
    loadSampleData() {
        // 샘플 연락처 데이터
        this.contacts = [
            {
                id: 1,
                name: '김대리',
                email: 'kim@company.com',
                company: '개발팀'
            },
            {
                id: 2,
                name: '이과장',
                email: 'lee@company.com',
                company: '기획팀'
            },
            {
                id: 3,
                name: '박팀장',
                email: 'park@company.com',
                company: '관리팀'
            }
        ];
        
        this.updateEmailList();
        this.renderContacts();
        this.loadShareData();
        
        // 분석 기록 자동 로드
        this.loadAnalysisHistory();
    }
    
    // 연락처 관리 기능
    openAddContactModal() {
        this.openModal('add-contact-modal');
    }
    
    saveContact() {
        const name = document.getElementById('contact-name').value.trim();
        const email = document.getElementById('contact-email').value.trim();
        const company = document.getElementById('contact-company').value.trim();
        
        if (!name || !email) {
            this.showNotification('오류', '이름과 이메일은 필수 입력 항목입니다.');
            return;
        }
        
        // 이메일 중복 확인
        if (this.contacts.some(contact => contact.email === email)) {
            this.showNotification('오류', '이미 등록된 이메일 주소입니다.');
            return;
        }
        
        const newContact = {
            id: Date.now(),
            name,
            email,
            company
        };
        
        this.contacts.push(newContact);
        this.renderContacts();
        this.closeModal('add-contact-modal');
        
        // 폼 초기화
        document.getElementById('contact-form').reset();
        
        this.showNotification('연락처 추가', `${name}님이 연락처에 추가되었습니다.`);
    }
    
    renderContacts() {
        const container = document.getElementById('contacts-list');
        
        // 요소가 없으면 안전하게 리턴
        if (!container) {
            return;
        }
        
        if (this.contacts.length === 0) {
            container.innerHTML = '<div class="empty-state">저장된 연락처가 없습니다.</div>';
            return;
        }
        
        container.innerHTML = this.contacts.map(contact => `
            <div class="contact-item">
                <div class="contact-info">
                    <div class="contact-name">${contact.name}</div>
                    <div class="contact-email">${contact.email}</div>
                    ${contact.company ? `<div class="contact-company">${contact.company}</div>` : ''}
                </div>
                <div class="contact-actions-btn">
                    <button class="btn btn-outline btn-sm" onclick="deleteContact(${contact.id})">삭제</button>
                </div>
            </div>
        `).join('');
    }
    
    deleteContact(contactId) {
        if (confirm('이 연락처를 삭제하시겠습니까?')) {
            this.contacts = this.contacts.filter(contact => contact.id !== contactId);
            this.renderContacts();
            this.showNotification('연락처 삭제', '연락처가 삭제되었습니다.');
        }
    }
    
    // 받는 사람 관리 기능
    openContactModal() {
        this.renderContactSelectList();
        this.openModal('contact-select-modal');
    }
    
    renderContactSelectList() {
        const container = document.getElementById('contact-select-list');
        
        // 요소가 없으면 안전하게 리턴
        if (!container) {
            return;
        }
        
        if (this.contacts.length === 0) {
            container.innerHTML = '<div class="empty-state">저장된 연락처가 없습니다. 먼저 연락처를 추가해주세요.</div>';
            return;
        }
        
        container.innerHTML = this.contacts.map(contact => `
            <div class="contact-select-item" onclick="toggleContactSelection(${contact.id})">
                <input type="checkbox" class="contact-select-checkbox" id="contact-${contact.id}">
                <div class="contact-info">
                    <div class="contact-name">${contact.name}</div>
                    <div class="contact-email">${contact.email}</div>
                    ${contact.company ? `<div class="contact-company">${contact.company}</div>` : ''}
                </div>
            </div>
        `).join('');
    }
    
    toggleContactSelection(contactId) {
        const checkbox = document.getElementById(`contact-${contactId}`);
        checkbox.checked = !checkbox.checked;
        
        const item = checkbox.closest('.contact-select-item');
        if (checkbox.checked) {
            item.classList.add('selected');
            if (!this.selectedContacts.includes(contactId)) {
                this.selectedContacts.push(contactId);
            }
        } else {
            item.classList.remove('selected');
            this.selectedContacts = this.selectedContacts.filter(id => id !== contactId);
        }
    }
    
    addSelectedContacts() {
        if (this.selectedContacts.length === 0) {
            this.showNotification('알림', '선택된 연락처가 없습니다.');
            return;
        }
        
        this.selectedContacts.forEach(contactId => {
            const contact = this.contacts.find(c => c.id === contactId);
            if (contact && !this.selectedRecipients.some(r => r.email === contact.email)) {
                this.selectedRecipients.push({
                    name: contact.name,
                    email: contact.email
                });
            }
        });
        
        this.renderRecipients();
        this.selectedContacts = [];
        this.closeModal('contact-select-modal');
        
        this.showNotification('받는 사람 추가', `받는 사람이 추가되었습니다.`);
    }
    
    renderRecipients() {
        const container = document.getElementById('recipients-list');
        
        // 요소가 없으면 안전하게 리턴
        if (!container) {
            return;
        }
        
        container.innerHTML = this.selectedRecipients.map((recipient, index) => `
            <div class="recipient-tag">
                <span>${recipient.name} (${recipient.email})</span>
                <button class="remove-btn" onclick="removeRecipient(${index})">×</button>
            </div>
        `).join('');
    }
    
    removeRecipient(index) {
        this.selectedRecipients.splice(index, 1);
        this.renderRecipients();
    }
    
    // ICS 선택 기능
    openICSModal() {
        this.renderICSList();
        this.openModal('ics-select-modal');
    }
    
    renderICSList() {
        const container = document.getElementById('ics-list');
        
        // 요소가 없으면 안전하게 리턴
        if (!container) {
            return;
        }
        
        if (this.analysisResults.length === 0) {
            container.innerHTML = '<div class="empty-state">분석된 ICS 데이터가 없습니다. 먼저 통화 내용을 분석해주세요.</div>';
            return;
        }
        
        container.innerHTML = this.analysisResults.map((result, index) => `
            <div class="ics-item" onclick="selectICSItem(${index})">
                <input type="radio" class="ics-radio" name="ics-select" id="ics-${index}">
                <div class="ics-item-info">
                    <div class="ics-title">${result.data.summary}</div>
                    <div class="ics-date">${this.formatDateTime(result.data.startdate)} - ${this.formatDateTime(result.data.enddate)}</div>
                </div>
            </div>
        `).join('');
    }
    
    selectICSItem(index) {
        // 모든 라디오 버튼 해제
        document.querySelectorAll('.ics-radio').forEach(radio => radio.checked = false);
        document.querySelectorAll('.ics-item').forEach(item => item.classList.remove('selected'));
        
        // 선택된 항목 표시
        document.getElementById(`ics-${index}`).checked = true;
        document.querySelectorAll('.ics-item')[index].classList.add('selected');
        
        this.selectedICS = this.analysisResults[index];
    }
    
    selectICSFile() {
        if (!this.selectedICS) {
            this.showNotification('알림', 'ICS 파일을 선택해주세요.');
            return;
        }
        
        const icsInfo = document.getElementById('ics-info');
        const selectedIcsDiv = document.getElementById('selected-ics');
        
        icsInfo.textContent = `${this.selectedICS.data.summary} (${this.formatDateTime(this.selectedICS.data.startdate)})`;
        selectedIcsDiv.style.display = 'flex';
        
        this.closeModal('ics-select-modal');
        this.showNotification('ICS 선택', 'ICS 파일이 선택되었습니다.');
    }
    
    removeSelectedICS() {
        this.selectedICS = null;
        document.getElementById('selected-ics').style.display = 'none';
        this.showNotification('ICS 제거', 'ICS 파일 선택이 해제되었습니다.');
    }
    
    // 일괄 발송 기능
    sendBulkEmail() {
        if (this.selectedRecipients.length === 0) {
            this.showNotification('오류', '받는 사람을 선택해주세요.');
            return;
        }
        
        const subject = document.getElementById('email-subject').value.trim();
        const content = document.getElementById('email-content').value.trim();
        
        if (!subject || !content) {
            this.showNotification('오류', '제목과 내용을 입력해주세요.');
            return;
        }
        
        // 실제로는 여기서 이메일 발송 API 호출
        this.showNotification('발송 중', `${this.selectedRecipients.length}명에게 이메일을 발송하고 있습니다...`);
        
        setTimeout(() => {
            this.showNotification('발송 완료', `${this.selectedRecipients.length}명에게 이메일이 성공적으로 발송되었습니다.`);
            
            // 폼 초기화
            document.getElementById('email-form').reset();
            this.selectedRecipients = [];
            this.selectedICS = null;
            this.renderRecipients();
            document.getElementById('selected-ics').style.display = 'none';
        }, 2000);
    }
    
    // 일정 공유 관련 기능
    loadShareData() {
        // 공유 가능한 일정 (분석 결과 + 기존 일정)
        this.shareableSchedules = [
            ...(this.analysisResults || []).map(result => ({
                id: `analysis_${result.id || Date.now()}`,
                type: 'analysis',
                title: result.data.summary,
                date: result.data.startdate,
                endDate: result.data.enddate,
                location: result.data.location,
                description: result.data.description,
                data: result.data
            })),
            ...(this.schedules || []).map(schedule => ({
                id: `schedule_${schedule.id}`,
                type: 'schedule',
                title: schedule.title,
                date: `${schedule.date} ${schedule.time}`,
                description: schedule.description,
                data: schedule
            }))
        ];
        
        // 샘플 공유받은 일정 데이터
        this.receivedSchedules = [
            {
                id: 1,
                title: '마케팅 전략 회의',
                date: '2024-01-20 15:00',
                endDate: '2024-01-20 16:30',
                location: '회의실 A',
                description: '2024년 마케팅 전략 수립 및 예산 계획',
                from: '이마케팅 (marketing@company.com)',
                message: '마케팅 전략 회의에 참석해 주세요. 중요한 안건들이 있습니다.',
                status: 'pending',
                receivedAt: '2024-01-15 09:30'
            },
            {
                id: 2,
                title: '프로젝트 킥오프',
                date: '2024-01-22 10:00',
                endDate: '2024-01-22 12:00',
                location: '대회의실',
                description: '신규 프로젝트 시작 및 팀 소개',
                from: '박PM (pm@company.com)',
                message: '새로운 프로젝트가 시작됩니다. 꼭 참석해 주세요!',
                status: 'added',
                receivedAt: '2024-01-14 14:20'
            },
            {
                id: 3,
                title: '분기별 성과 발표',
                date: '2024-01-25 14:00',
                endDate: '2024-01-25 17:00',
                location: '오디토리움',
                description: '4분기 성과 발표 및 시상식',
                from: '최인사 (hr@company.com)',
                message: '분기별 성과 발표회입니다. 모든 팀원 참석 필수입니다.',
                status: 'declined',
                receivedAt: '2024-01-13 11:45'
            }
        ];
        
        this.renderShareableSchedules();
        this.renderReceivedSchedules();
    }
    
    renderShareableSchedules() {
        const container = document.getElementById('share-schedule-list');
        
        // 요소가 없으면 안전하게 리턴
        if (!container) {
            return;
        }
        
        if (this.shareableSchedules.length === 0) {
            container.innerHTML = '<div class="empty-state">공유할 수 있는 일정이 없습니다. 먼저 통화 분석을 하거나 일정을 추가해 주세요.</div>';
            return;
        }
        
        container.innerHTML = this.shareableSchedules.map(schedule => `
            <div class="share-schedule-item" onclick="toggleShareScheduleSelection('${schedule.id}')">
                <input type="checkbox" class="share-schedule-checkbox" id="share-schedule-${schedule.id}">
                <div class="share-schedule-info">
                    <div class="share-schedule-title">${schedule.title}</div>
                    <div class="share-schedule-date">${this.formatDateTime(schedule.date)}</div>
                    <div class="share-schedule-type">${schedule.type === 'analysis' ? '분석 결과' : '일정'}</div>
                </div>
            </div>
        `).join('');
    }
    
    toggleShareScheduleSelection(scheduleId) {
        const checkbox = document.getElementById(`share-schedule-${scheduleId}`);
        checkbox.checked = !checkbox.checked;
        
        const item = checkbox.closest('.share-schedule-item');
        if (checkbox.checked) {
            item.classList.add('selected');
            if (!this.selectedShareSchedules.includes(scheduleId)) {
                this.selectedShareSchedules.push(scheduleId);
            }
        } else {
            item.classList.remove('selected');
            this.selectedShareSchedules = this.selectedShareSchedules.filter(id => id !== scheduleId);
        }
    }
    
    openShareContactModal() {
        this.renderShareContactList();
        this.openModal('share-contact-modal');
    }
    
    renderShareContactList() {
        const container = document.getElementById('share-contact-list');
        
        // 요소가 없으면 안전하게 리턴
        if (!container) {
            return;
        }
        
        // 실제로는 API에서 MUFI 사용자 목록을 가져올 것
        const mufiUsers = [
            { id: 1, name: '김개발', email: 'dev@company.com', department: '개발팀' },
            { id: 2, name: '이디자인', email: 'design@company.com', department: '디자인팀' },
            { id: 3, name: '박기획', email: 'plan@company.com', department: '기획팀' },
            { id: 4, name: '최마케팅', email: 'marketing@company.com', department: '마케팅팀' },
            { id: 5, name: '정영업', email: 'sales@company.com', department: '영업팀' }
        ];
        
        container.innerHTML = mufiUsers.map(user => `
            <div class="share-contact-item" onclick="toggleShareContactSelection(${user.id})">
                <input type="checkbox" class="contact-select-checkbox" id="share-contact-${user.id}">
                <div class="contact-info">
                    <div class="contact-name">${user.name}</div>
                    <div class="contact-email">${user.email}</div>
                    <div class="contact-company">${user.department}</div>
                </div>
            </div>
        `).join('');
    }
    
    toggleShareContactSelection(userId) {
        const checkbox = document.getElementById(`share-contact-${userId}`);
        checkbox.checked = !checkbox.checked;
        
        const item = checkbox.closest('.share-contact-item');
        if (checkbox.checked) {
            item.classList.add('selected');
            if (!this.selectedShareContacts.includes(userId)) {
                this.selectedShareContacts.push(userId);
            }
        } else {
            item.classList.remove('selected');
            this.selectedShareContacts = this.selectedShareContacts.filter(id => id !== userId);
        }
    }
    
    addSelectedShareContacts() {
        if (this.selectedShareContacts.length === 0) {
            this.showNotification('알림', '선택된 사용자가 없습니다.');
            return;
        }
        
        const mufiUsers = [
            { id: 1, name: '김개발', email: 'dev@company.com' },
            { id: 2, name: '이디자인', email: 'design@company.com' },
            { id: 3, name: '박기획', email: 'plan@company.com' },
            { id: 4, name: '최마케팅', email: 'marketing@company.com' },
            { id: 5, name: '정영업', email: 'sales@company.com' }
        ];
        
        this.selectedShareContacts.forEach(userId => {
            const user = mufiUsers.find(u => u.id === userId);
            if (user && !this.shareRecipients.some(r => r.email === user.email)) {
                this.shareRecipients.push({
                    name: user.name,
                    email: user.email
                });
            }
        });
        
        this.renderShareRecipients();
        this.selectedShareContacts = [];
        this.closeModal('share-contact-modal');
        
        this.showNotification('공유 대상 추가', '공유 대상이 추가되었습니다.');
    }
    
    renderShareRecipients() {
        const container = document.getElementById('share-recipients-list');
        
        // 요소가 없으면 안전하게 리턴
        if (!container) {
            return;
        }
        
        container.innerHTML = this.shareRecipients.map((recipient, index) => `
            <div class="share-recipient-tag">
                <span>${recipient.name} (${recipient.email})</span>
                <button class="remove-btn" onclick="removeShareRecipient(${index})">×</button>
            </div>
        `).join('');
    }
    
    removeShareRecipient(index) {
        this.shareRecipients.splice(index, 1);
        this.renderShareRecipients();
    }
    
    shareSchedule() {
        if (this.selectedShareSchedules.length === 0) {
            this.showNotification('오류', '공유할 일정을 선택해주세요.');
            return;
        }
        
        if (this.shareRecipients.length === 0) {
            this.showNotification('오류', '공유 대상을 선택해주세요.');
            return;
        }
        
        const message = document.getElementById('share-message').value.trim();
        
        this.showNotification('공유 중', `${this.shareRecipients.length}명에게 ${this.selectedShareSchedules.length}개 일정을 공유하고 있습니다...`);
        
        setTimeout(() => {
            this.showNotification('공유 완료', '일정이 성공적으로 공유되었습니다.');
            this.clearShareForm();
        }, 2000);
    }
    
    clearShareForm() {
        this.selectedShareSchedules = [];
        this.shareRecipients = [];
        document.getElementById('share-message').value = '';
        
        // 체크박스 초기화
        document.querySelectorAll('.share-schedule-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        document.querySelectorAll('.share-schedule-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        this.renderShareRecipients();
    }
    
    // 공유받은 일정 관리
    renderReceivedSchedules(filter = 'all') {
        const container = document.getElementById('received-schedules-list');
        
        // 요소가 없으면 안전하게 리턴
        if (!container) {
            return;
        }
        
        let filteredSchedules = this.receivedSchedules;
        if (filter !== 'all') {
            filteredSchedules = this.receivedSchedules.filter(schedule => schedule.status === filter);
        }
        
        if (filteredSchedules.length === 0) {
            container.innerHTML = '<div class="empty-state">해당하는 공유받은 일정이 없습니다.</div>';
            return;
        }
        
        container.innerHTML = filteredSchedules.map(schedule => `
            <div class="received-schedule-item ${schedule.status}" onclick="openReceivedScheduleModal(${schedule.id})">
                <div class="received-schedule-info">
                    <div class="received-schedule-title">${schedule.title}</div>
                    <div class="received-schedule-date">${this.formatDateTime(schedule.date)}</div>
                    <div class="received-schedule-from">공유자: ${schedule.from}</div>
                    ${schedule.message ? `<div class="received-schedule-message">"${schedule.message}"</div>` : ''}
                </div>
                <div class="received-schedule-actions">
                    <span class="received-schedule-status ${schedule.status}">
                        ${this.getStatusText(schedule.status)}
                    </span>
                    ${schedule.status === 'pending' ? `
                        <button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); addReceivedScheduleToCalendar(${schedule.id})">추가</button>
                        <button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); declineReceivedSchedule(${schedule.id})">거절</button>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }
    
    getStatusText(status) {
        const statusMap = {
            'pending': '대기중',
            'added': '추가됨',
            'declined': '거절됨'
        };
        return statusMap[status] || status;
    }
    
    filterReceivedSchedules(filter) {
        // 필터 버튼 상태 업데이트
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-filter="${filter}"]`).classList.add('active');
        
        this.renderReceivedSchedules(filter);
    }
    
    openReceivedScheduleModal(scheduleId) {
        const schedule = this.receivedSchedules.find(s => s.id === scheduleId);
        if (!schedule) return;
        
        this.currentReceivedSchedule = schedule;
        
        const container = document.getElementById('received-schedule-details');
        container.innerHTML = `
            <div class="schedule-detail-section">
                <div class="schedule-detail-title">${schedule.title}</div>
                
                <div class="schedule-detail-field">
                    <div class="schedule-detail-label">📅 일시</div>
                    <div class="schedule-detail-value">${this.formatDateTime(schedule.date)} - ${this.formatDateTime(schedule.endDate)}</div>
                </div>
                
                <div class="schedule-detail-field">
                    <div class="schedule-detail-label">📍 장소</div>
                    <div class="schedule-detail-value">${schedule.location || '장소 없음'}</div>
                </div>
                
                <div class="schedule-detail-field">
                    <div class="schedule-detail-label">📝 설명</div>
                    <div class="schedule-detail-value">${schedule.description || '설명 없음'}</div>
                </div>
                
                ${schedule.message ? `
                    <div class="schedule-detail-message">
                        <div class="schedule-detail-label">💬 공유 메시지</div>
                        <div class="schedule-detail-value">"${schedule.message}"</div>
                        <div class="schedule-detail-from">- ${schedule.from}</div>
                    </div>
                ` : ''}
                
                <div class="schedule-detail-field">
                    <div class="schedule-detail-label">⏰ 공유받은 시간</div>
                    <div class="schedule-detail-value">${schedule.receivedAt}</div>
                </div>
            </div>
        `;
        
        this.openModal('received-schedule-modal');
    }
    
    addReceivedScheduleToCalendar(scheduleId) {
        const schedule = this.receivedSchedules.find(s => s.id === scheduleId);
        if (!schedule) return;
        
        // 일정을 내 캘린더에 추가
        const newSchedule = {
            id: Date.now(),
            title: schedule.title,
            date: schedule.date.split(' ')[0],
            time: schedule.date.split(' ')[1],
            description: schedule.description,
            location: schedule.location,
            sharedFrom: schedule.from
        };
        
        this.schedules.push(newSchedule);
        
        // 상태 업데이트
        schedule.status = 'added';
        
        this.updateScheduleList();
        this.renderReceivedSchedules();
        this.closeModal('received-schedule-modal');
        
        this.showNotification('캘린더 추가', `"${schedule.title}" 일정이 캘린더에 추가되었습니다.`);
    }
    
    declineReceivedSchedule(scheduleId) {
        const schedule = this.receivedSchedules.find(s => s.id === scheduleId);
        if (!schedule) return;
        
        if (confirm('이 일정을 거절하시겠습니까?')) {
            schedule.status = 'declined';
            this.renderReceivedSchedules();
            this.closeModal('received-schedule-modal');
            
            this.showNotification('일정 거절', `"${schedule.title}" 일정을 거절했습니다.`);
        }
    }

    // 일정 선택 모달 관련 기능
    openScheduleSelectModal() {
        this.renderScheduleSelectList();
        this.openModal('schedule-select-modal');
    }

    renderScheduleSelectList() {
        const container = document.getElementById('schedule-select-list');
        if (!container) return;

        // 실제로는 서버에서 사용자의 일정 목록을 가져와야 함
        const mySchedules = [
            {
                id: 1,
                title: '프로젝트 회의',
                datetime: '2024-01-15 14:00',
                location: '회의실 A',
                description: '프로젝트 진행 상황 점검 및 향후 계획 논의'
            },
            {
                id: 2,
                title: '클라이언트 미팅',
                datetime: '2024-01-16 10:00',
                location: '온라인',
                description: '신규 프로젝트 제안서 발표 및 Q&A'
            },
            {
                id: 3,
                title: '팀 워크샵',
                datetime: '2024-01-17 09:00',
                location: '대회의실',
                description: '팀 빌딩 및 업무 프로세스 개선 워크샵'
            },
            {
                id: 4,
                title: '월간 보고서 검토',
                datetime: '2024-01-19 11:00',
                location: '소회의실',
                description: '1월 월간 성과 보고서 검토 및 피드백'
            },
            {
                id: 5,
                title: '고객사 방문',
                datetime: '2024-01-20 14:30',
                location: '고객사 본사',
                description: '분기별 정기 미팅 및 계약 갱신 논의'
            }
        ];

        container.innerHTML = mySchedules.map(schedule => `
            <div class="schedule-select-item" onclick="dashboard.toggleScheduleSelection(${schedule.id})">
                <div class="schedule-select-content">
                    <div class="schedule-select-title">${schedule.title}</div>
                    <div class="schedule-select-subtitle">${schedule.datetime} - ${schedule.location}</div>
                    <div class="schedule-select-description">${schedule.description}</div>
                </div>
                <div class="schedule-select-actions">
                    <input type="checkbox" class="schedule-select-checkbox" 
                           value="${schedule.id}" 
                           data-title="${schedule.title}" 
                           data-datetime="${schedule.datetime}" 
                           data-location="${schedule.location}"
                           ${this.selectedSchedulesForShare.includes(schedule.id) ? 'checked' : ''}>
                </div>
            </div>
        `).join('');
    }

    toggleScheduleSelection(scheduleId) {
        const checkbox = document.querySelector(`input[value="${scheduleId}"]`);
        if (checkbox) {
            checkbox.checked = !checkbox.checked;
            
            if (checkbox.checked) {
                if (!this.selectedSchedulesForShare.includes(scheduleId)) {
                    this.selectedSchedulesForShare.push(scheduleId);
                }
            } else {
                this.selectedSchedulesForShare = this.selectedSchedulesForShare.filter(id => id !== scheduleId);
            }
            
            // 선택 상태 시각적 표시
            const item = checkbox.closest('.schedule-select-item');
            if (checkbox.checked) {
                item.classList.add('selected');
            } else {
                item.classList.remove('selected');
            }
        }
    }

    addSelectedSchedules() {
        const selectedSchedules = [];
        
        // 체크된 일정들 수집
        document.querySelectorAll('.schedule-select-checkbox:checked').forEach(checkbox => {
            selectedSchedules.push({
                id: parseInt(checkbox.value),
                title: checkbox.dataset.title,
                datetime: checkbox.dataset.datetime,
                location: checkbox.dataset.location
            });
        });

        // 선택된 일정들을 화면에 표시
        this.renderSelectedSchedules(selectedSchedules);
        
        // 모달 닫기
        this.closeModal('schedule-select-modal');
        
        if (selectedSchedules.length > 0) {
            this.showNotification('일정 선택 완료', `${selectedSchedules.length}개의 일정이 선택되었습니다.`);
        }
    }

    renderSelectedSchedules(schedules) {
        const container = document.getElementById('selected-schedules-list');
        if (!container) return;

        container.innerHTML = schedules.map(schedule => `
            <div class="selected-schedule-tag">
                <span>${schedule.title}</span>
                <button class="remove-btn" onclick="dashboard.removeSelectedSchedule(${schedule.id})" title="제거">×</button>
            </div>
        `).join('');

        // 내부 데이터도 업데이트
        this.selectedShareSchedules = schedules;
    }

    removeSelectedSchedule(scheduleId) {
        // 선택된 일정에서 제거
        this.selectedShareSchedules = this.selectedShareSchedules.filter(s => s.id !== scheduleId);
        this.selectedSchedulesForShare = this.selectedSchedulesForShare.filter(id => id !== scheduleId);
        
        // 화면 업데이트
        this.renderSelectedSchedules(this.selectedShareSchedules);
    }

    // 검색 기능
    searchSchedules() {
        const searchTerm = document.getElementById('schedule-search').value.toLowerCase();
        const items = document.querySelectorAll('.schedule-select-item');
        
        items.forEach(item => {
            const title = item.querySelector('.schedule-select-title').textContent.toLowerCase();
            const description = item.querySelector('.schedule-select-description').textContent.toLowerCase();
            
            if (title.includes(searchTerm) || description.includes(searchTerm)) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    }
    
    // 참석자별 일정 그룹화
    groupSchedulesByParticipant(participants, schedules) {
        const participantSchedules = {};
        
        // 참석자별로 빈 배열 초기화
        participants.forEach(participant => {
            participantSchedules[participant.name] = [];
        });
        
        // 일정을 담당자별로 분배
        schedules.forEach(schedule => {
            if (schedule.assignees && Array.isArray(schedule.assignees)) {
                schedule.assignees.forEach(assignee => {
                    if (participantSchedules[assignee]) {
                        participantSchedules[assignee].push(schedule);
                    }
                });
            } else {
                // 담당자가 없으면 첫 번째 참석자에게 할당
                if (participants.length > 0) {
                    participantSchedules[participants[0].name].push(schedule);
                }
            }
        });
        
        return participantSchedules;
    }
    
    // 참석자별 일정 렌더링
    renderParticipantSchedules(schedules, participantIndex) {
        if (!schedules || schedules.length === 0) {
            return '<p class="no-schedules">담당하는 일정이 없습니다.</p>';
        }
        
        return schedules.map((schedule, scheduleIndex) => `
            <div class="schedule-card" data-participant="${participantIndex}" data-schedule="${scheduleIndex}">
                <div class="schedule-header">
                    <h6 class="schedule-title">${schedule.summary}</h6>
                </div>
                
                <div class="analysis-fields-container">
                    <div class="analysis-field">
                        <div class="analysis-field-header">
                            <label class="analysis-field-label">📝 Summary (요약)</label>
                            <div class="analysis-field-actions">
                                <button class="btn btn-outline btn-sm field-edit-btn" onclick="editParticipantScheduleField(${participantIndex}, ${scheduleIndex}, 'summary')">
                                    <span id="summary-btn-${participantIndex}-${scheduleIndex}">수정</span>
                                </button>
                            </div>
                        </div>
                        <div class="analysis-field-value" contenteditable="false" data-field="summary" id="summary-value-${participantIndex}-${scheduleIndex}">${schedule.summary}</div>
                    </div>
                    
                    <div class="analysis-field">
                        <div class="analysis-field-header">
                            <label class="analysis-field-label">📄 Description (설명)</label>
                            <div class="analysis-field-actions">
                                <button class="btn btn-outline btn-sm field-edit-btn" onclick="editParticipantScheduleField(${participantIndex}, ${scheduleIndex}, 'description')">
                                    <span id="description-btn-${participantIndex}-${scheduleIndex}">수정</span>
                                </button>
                            </div>
                        </div>
                        <div class="analysis-field-value multiline" contenteditable="false" data-field="description" id="description-value-${participantIndex}-${scheduleIndex}">${schedule.description}</div>
                    </div>
                    
                    <div class="analysis-field">
                        <div class="analysis-field-header">
                            <label class="analysis-field-label">📍 Location (장소)</label>
                            <div class="analysis-field-actions">
                                <button class="btn btn-outline btn-sm field-edit-btn" onclick="editParticipantScheduleField(${participantIndex}, ${scheduleIndex}, 'location')">
                                    <span id="location-btn-${participantIndex}-${scheduleIndex}">수정</span>
                                </button>
                            </div>
                        </div>
                        <div class="analysis-field-value" contenteditable="false" data-field="location" id="location-value-${participantIndex}-${scheduleIndex}">${schedule.location}</div>
                    </div>
                    
                    <div class="analysis-field">
                        <div class="analysis-field-header">
                            <label class="analysis-field-label">⏰ Start Date (시작일시)</label>
                            <div class="analysis-field-actions">
                                <button class="btn btn-outline btn-sm field-edit-btn" onclick="editParticipantScheduleField(${participantIndex}, ${scheduleIndex}, 'startdate')">
                                    <span id="startdate-btn-${participantIndex}-${scheduleIndex}">수정</span>
                                </button>
                            </div>
                        </div>
                        <div class="analysis-field-value date-field" contenteditable="false" data-field="startdate" id="startdate-value-${participantIndex}-${scheduleIndex}">${this.formatDateTime(schedule.startdate)}</div>
                    </div>
                    
                    <div class="analysis-field">
                        <div class="analysis-field-header">
                            <label class="analysis-field-label">⏰ End Date (종료일시)</label>
                            <div class="analysis-field-actions">
                                <button class="btn btn-outline btn-sm field-edit-btn" onclick="editParticipantScheduleField(${participantIndex}, ${scheduleIndex}, 'enddate')">
                                    <span id="enddate-btn-${participantIndex}-${scheduleIndex}">수정</span>
                                </button>
                            </div>
                        </div>
                        <div class="analysis-field-value date-field" contenteditable="false" data-field="enddate" id="enddate-value-${participantIndex}-${scheduleIndex}">${this.formatDateTime(schedule.enddate)}</div>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    // 참석자 탭 전환
    switchParticipantTab(index) {
        // 모든 탭 비활성화
        document.querySelectorAll('.participant-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelectorAll('.participant-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        
        // 선택된 탭 활성화
        document.querySelector(`[data-participant="${index}"]`).classList.add('active');
        document.getElementById(`participant-panel-${index}`).classList.add('active');
        
        this.activeParticipantIndex = index;
    }
    
    // 참석자별 일정 필드 수정
    editParticipantScheduleField(participantIndex, scheduleIndex, fieldName) {
        const fieldValue = document.getElementById(`${fieldName}-value-${participantIndex}-${scheduleIndex}`);
        const buttonSpan = document.getElementById(`${fieldName}-btn-${participantIndex}-${scheduleIndex}`);
        const actionContainer = fieldValue.closest('.analysis-field').querySelector('.analysis-field-actions');
        
        const isEditing = buttonSpan.textContent === '저장';
        
        if (isEditing) {
            // 저장 모드 -> 보기 모드
            fieldValue.contentEditable = 'false';
            fieldValue.classList.remove('editing');
            
            // 수정된 데이터 저장
            let newValue = fieldValue.textContent.trim();
            const participant = this.currentParticipants[participantIndex];
            const scheduleToUpdate = this.participantSchedules[participant.name][scheduleIndex];
            
            if (fieldName === 'startdate' || fieldName === 'enddate') {
                scheduleToUpdate[fieldName] = this.parseDateTime(newValue);
            } else {
                scheduleToUpdate[fieldName] = newValue;
            }
            
            // 버튼 상태 변경
            actionContainer.innerHTML = `
                <button class="btn btn-outline btn-sm field-edit-btn" onclick="editParticipantScheduleField(${participantIndex}, ${scheduleIndex}, '${fieldName}')">
                    <span id="${fieldName}-btn-${participantIndex}-${scheduleIndex}">수정</span>
                </button>
            `;
            
            this.showNotification('저장 완료', `${this.getFieldDisplayName(fieldName)}이(가) 저장되었습니다.`);
        } else {
            // 보기 모드 -> 수정 모드
            fieldValue.contentEditable = 'true';
            fieldValue.classList.add('editing');
            fieldValue.focus();
            
            // 저장/취소 버튼으로 변경
            actionContainer.innerHTML = `
                <button class="btn btn-sm field-edit-btn save" onclick="editParticipantScheduleField(${participantIndex}, ${scheduleIndex}, '${fieldName}')">
                    <span id="${fieldName}-btn-${participantIndex}-${scheduleIndex}">저장</span>
                </button>
                <button class="btn btn-sm field-edit-btn cancel" onclick="cancelParticipantScheduleEdit(${participantIndex}, ${scheduleIndex}, '${fieldName}')">
                    취소
                </button>
            `;
            
            // 원본 데이터 백업
            fieldValue.dataset.originalValue = fieldValue.textContent.trim();
            
            this.showNotification('수정 모드', `${this.getFieldDisplayName(fieldName)}을(를) 수정할 수 있습니다.`);
        }
    }
    
    // 참석자별 일정 필드 수정 취소
    cancelParticipantScheduleEdit(participantIndex, scheduleIndex, fieldName) {
        const fieldValue = document.getElementById(`${fieldName}-value-${participantIndex}-${scheduleIndex}`);
        const actionContainer = fieldValue.closest('.analysis-field').querySelector('.analysis-field-actions');
        
        // 원본 데이터 복원
        fieldValue.textContent = fieldValue.dataset.originalValue || '';
        fieldValue.contentEditable = 'false';
        fieldValue.classList.remove('editing');
        
        // 버튼 상태 변경
        actionContainer.innerHTML = `
            <button class="btn btn-outline btn-sm field-edit-btn" onclick="editParticipantScheduleField(${participantIndex}, ${scheduleIndex}, '${fieldName}')">
                <span id="${fieldName}-btn-${participantIndex}-${scheduleIndex}">수정</span>
            </button>
        `;
        
        this.showNotification('취소됨', `${this.getFieldDisplayName(fieldName)} 수정이 취소되었습니다.`);
    }
    
    // 새로운 탭 시스템 메서드들
    switchScheduleTab(index) {
        // 모든 탭 비활성화
        document.querySelectorAll('.schedule-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelectorAll('.schedule-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        
        // 선택된 탭 활성화
        document.querySelector(`[data-tab="${index}"]`).classList.add('active');
        document.getElementById(`schedule-panel-${index}`).classList.add('active');
        
        this.activeScheduleIndex = index;
    }
    
    editScheduleField(scheduleIndex, fieldName) {
        const fieldValue = document.getElementById(`${fieldName}-value-${scheduleIndex}`);
        const buttonSpan = document.getElementById(`${fieldName}-btn-${scheduleIndex}`);
        const button = buttonSpan.closest('.field-edit-btn');
        
        const isEditing = buttonSpan.textContent === '저장';
        
        if (isEditing) {
            // 저장 모드 -> 보기 모드
            fieldValue.contentEditable = 'false';
            fieldValue.classList.remove('editing');
            
            // 수정된 데이터 저장
            let newValue = fieldValue.textContent.trim();
            if (fieldName === 'assignees') {
                // 담당자는 배열로 변환
                this.currentSchedules[scheduleIndex][fieldName] = newValue ? newValue.split(',').map(s => s.trim()) : [];
            } else {
                this.currentSchedules[scheduleIndex][fieldName] = newValue;
            }
            
            button.innerHTML = `<span id="${fieldName}-btn-${scheduleIndex}">수정</span>`;
            this.showNotification('저장 완료', `${this.getFieldDisplayName(fieldName)}이(가) 저장되었습니다.`);
        } else {
            // 보기 모드 -> 수정 모드
            fieldValue.contentEditable = 'true';
            fieldValue.classList.add('editing');
            fieldValue.focus();
            
            // 저장/취소 버튼으로 변경
            button.innerHTML = `
                <span id="${fieldName}-btn-${scheduleIndex}">저장</span>
                <button class="btn btn-outline btn-sm btn-cancel" onclick="cancelScheduleEdit(${scheduleIndex}, '${fieldName}')">취소</button>
            `;
        }
    }
    
    cancelScheduleEdit(scheduleIndex, fieldName) {
        const fieldValue = document.getElementById(`${fieldName}-value-${scheduleIndex}`);
        const button = document.getElementById(`${fieldName}-btn-${scheduleIndex}`).closest('.field-edit-btn');
        
        // 원래 값으로 복원
        const originalValue = this.currentSchedules[scheduleIndex][fieldName];
        if (fieldName === 'assignees') {
            fieldValue.textContent = Array.isArray(originalValue) ? originalValue.join(', ') : originalValue;
        } else if (fieldName === 'startdate' || fieldName === 'enddate') {
            fieldValue.textContent = this.formatDateTime(originalValue);
        } else if (fieldName === 'type') {
            fieldValue.textContent = this.getTypeDisplayName(originalValue);
        } else {
            fieldValue.textContent = originalValue;
        }
        
        // 편집 모드 해제
        fieldValue.contentEditable = 'false';
        fieldValue.classList.remove('editing');
        
        // 버튼 복원
        button.innerHTML = `<span id="${fieldName}-btn-${scheduleIndex}">수정</span>`;
    }
    
    displayAnalysisResultFromDB(data) {
        // 분석 완료 상태로 변경
        this.setAnalysisState('complete');
        
        // 현재 분석 데이터 저장 (DB 형식)
        this.currentAnalysisData = {
            id: data.id,
            type: data.type,
            source: data.source_name,
            summary: data.summary || '',
            description: data.description || '',
            schedules: data.schedules || [],
            participants: data.participants || [],
            actions: data.actions || [],
            created_at: data.created_at
        };
        
        // UI 업데이트
        this.updateSummarySection(data.summary || '');
        this.updateScheduleSection(data.schedules?.[0] || {});
        this.updateDescriptionSection(data.description || '');
        this.updateParticipantsSection(data.participants || []);
        this.updateActionsSection(data.actions || []);
        
        // 편집 버튼 활성화
        this.enableEditButtons();
    }
    
    async loadAnalysisHistory() {
        try {
            const response = await fetch('/api/results?limit=20&offset=0');
            
            if (!response.ok) {
                throw new Error('분석 기록을 불러올 수 없습니다.');
            }
            
            const result = await response.json();
            
            if (result.success && result.data) {
                this.renderAnalysisHistory(result.data);
            }
            
        } catch (error) {
            console.error('분석 기록 로드 오류:', error);
            this.showNotification('로드 오류', '분석 기록을 불러오는 중 오류가 발생했습니다.', 'error');
        }
    }
    
    renderAnalysisHistory(historyData) {
        // 분석 기록을 표시할 UI 영역이 있다면 렌더링
        const historyContainer = document.getElementById('analysis-history');
        if (!historyContainer) return;
        
        if (historyData.length === 0) {
            historyContainer.innerHTML = '<div class="empty-state">저장된 분석 기록이 없습니다.</div>';
            return;
        }
        
        historyContainer.innerHTML = historyData.map(item => `
            <div class="history-item" onclick="dashboard.loadAnalysisResult('${item.id}')">
                <div class="history-header">
                    <h4>${item.source_name}</h4>
                    <span class="history-date">${this.formatDateTime(item.created_at)}</span>
                </div>
                <div class="history-summary">${item.summary || '요약 없음'}</div>
                <div class="history-meta">
                    <span class="history-type">${item.type === 'file' ? '파일' : '직접입력'}</span>
                    <span class="history-participants">${item.participants?.length || 0}명 참석</span>
                    <span class="history-actions">${item.actions?.length || 0}개 액션</span>
                </div>
            </div>
        `).join('');
    }
    
    async loadAnalysisResult(analysisId) {
        try {
            const response = await fetch(`/api/results/${analysisId}`);
            
            if (!response.ok) {
                throw new Error('분석 결과를 불러올 수 없습니다.');
            }
            
            const result = await response.json();
            
            if (result.success && result.data) {
                this.displayAnalysisResultFromDB(result.data);
                this.showNotification('로드 완료', '저장된 분석 결과를 불러왔습니다.');
            }
            
        } catch (error) {
            console.error('분석 결과 로드 오류:', error);
            this.showNotification('로드 오류', '분석 결과를 불러오는 중 오류가 발생했습니다.', 'error');
        }
    }
    
    async deleteAnalysisResult(analysisId) {
        if (!confirm('이 분석 결과를 삭제하시겠습니까?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/results/${analysisId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('분석 결과를 삭제할 수 없습니다.');
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('삭제 완료', '분석 결과가 삭제되었습니다.');
                this.loadAnalysisHistory(); // 목록 새로고침
            }
            
        } catch (error) {
            console.error('분석 결과 삭제 오류:', error);
            this.showNotification('삭제 오류', '분석 결과 삭제 중 오류가 발생했습니다.', 'error');
        }
    }
    
    async updateActionStatus(actionIndex, isCompleted) {
        if (!this.currentAnalysisData || !this.currentAnalysisData.id) {
            return;
        }
        
        try {
            const response = await fetch(`/api/results/${this.currentAnalysisData.id}/actions/${actionIndex}?is_completed=${isCompleted}`, {
                method: 'PATCH'
            });
            
            if (response.ok) {
                // 로컬 상태도 업데이트
                if (this.currentAnalysisData.actions[actionIndex]) {
                    this.currentAnalysisData.actions[actionIndex].is_completed = isCompleted;
                }
            }
            
        } catch (error) {
            console.error('액션 상태 업데이트 오류:', error);
            // 에러가 발생해도 UI는 그대로 유지 (낙관적 업데이트)
        }
    }

}

// 대시보드 초기화
const dashboard = new Dashboard();

// 전역 함수들 (dashboard 초기화 이후)
function openModal(modalId) {
    if (window.dashboard) dashboard.openModal(modalId);
}

function closeModal(modalId) {
    if (window.dashboard) dashboard.closeModal(modalId);
}



function editField(fieldName) {
    if (window.dashboard) dashboard.editField(fieldName);
}

function cancelEdit(fieldName) {
    if (window.dashboard) dashboard.cancelEdit(fieldName);
}

function generateICS() {
    if (window.dashboard) dashboard.generateICS();
}

function downloadICS() {
    if (window.dashboard) dashboard.downloadICS();
}

function resetAnalysis() {
    if (window.dashboard) dashboard.resetAnalysis();
}

function sendEmail() {
    if (window.dashboard) dashboard.sendEmail();
}

function previewEmail() {
    if (window.dashboard) dashboard.previewEmail();
}

function startAnalysis() {
    if (window.dashboard) dashboard.analyzeText();
}

function clearFile() {
    if (window.dashboard) dashboard.clearFile();
}

function clearAllInput() {
    if (window.dashboard) dashboard.clearAllInput();
}

// 이메일 관련 전역 함수들
function openAddContactModal() {
    if (window.dashboard) dashboard.openAddContactModal();
}

function saveContact() {
    if (window.dashboard) dashboard.saveContact();
}

function deleteContact(contactId) {
    if (window.dashboard) dashboard.deleteContact(contactId);
}

function openContactModal() {
    if (window.dashboard) dashboard.openContactModal();
}

function toggleContactSelection(contactId) {
    if (window.dashboard) dashboard.toggleContactSelection(contactId);
}

function addSelectedContacts() {
    if (window.dashboard) dashboard.addSelectedContacts();
}

function removeRecipient(index) {
    if (window.dashboard) dashboard.removeRecipient(index);
}

function openICSModal() {
    if (window.dashboard) dashboard.openICSModal();
}

function selectICSItem(index) {
    if (window.dashboard) dashboard.selectICSItem(index);
}

function selectICSFile() {
    if (window.dashboard) dashboard.selectICSFile();
}

function removeSelectedICS() {
    if (window.dashboard) dashboard.removeSelectedICS();
}

function sendBulkEmail() {
    if (window.dashboard) dashboard.sendBulkEmail();
}

// 일정 공유 관련 전역 함수들
function toggleShareScheduleSelection(scheduleId) {
    if (window.dashboard) dashboard.toggleShareScheduleSelection(scheduleId);
}

function openShareContactModal() {
    if (window.dashboard) dashboard.openShareContactModal();
}

function toggleShareContactSelection(userId) {
    if (window.dashboard) dashboard.toggleShareContactSelection(userId);
}

function addSelectedShareContacts() {
    if (window.dashboard) dashboard.addSelectedShareContacts();
}

function removeShareRecipient(index) {
    if (window.dashboard) dashboard.removeShareRecipient(index);
}

function shareSchedule() {
    if (window.dashboard) dashboard.shareSchedule();
}

function clearShareForm() {
    if (window.dashboard) dashboard.clearShareForm();
}

function filterReceivedSchedules(filter) {
    if (window.dashboard) dashboard.filterReceivedSchedules(filter);
}

function openReceivedScheduleModal(scheduleId) {
    if (window.dashboard) dashboard.openReceivedScheduleModal(scheduleId);
}

function addReceivedScheduleToCalendar(scheduleId) {
    if (window.dashboard) dashboard.addReceivedScheduleToCalendar(scheduleId);
}

function declineReceivedSchedule(scheduleId) {
    if (window.dashboard) dashboard.declineReceivedSchedule(scheduleId);
}

// 일정 선택 모달 관련 전역 함수들
function openScheduleSelectModal() {
    if (window.dashboard) dashboard.openScheduleSelectModal();
}

function toggleScheduleSelection(scheduleId) {
    if (window.dashboard) dashboard.toggleScheduleSelection(scheduleId);
}

function addSelectedSchedules() {
    if (window.dashboard) dashboard.addSelectedSchedules();
}

function removeSelectedSchedule(scheduleId) {
    if (window.dashboard) dashboard.removeSelectedSchedule(scheduleId);
}

function searchSchedules() {
    if (window.dashboard) dashboard.searchSchedules();
}

// 새로운 탭 시스템 관련 전역 함수들
function switchScheduleTab(index) {
    if (window.dashboard) dashboard.switchScheduleTab(index);
}

function editScheduleField(scheduleIndex, fieldName) {
    if (window.dashboard) dashboard.editScheduleField(scheduleIndex, fieldName);
}

function cancelScheduleEdit(scheduleIndex, fieldName) {
    if (window.dashboard) dashboard.cancelScheduleEdit(scheduleIndex, fieldName);
}

// 참석자별 탭 시스템 관련 전역 함수들
function switchParticipantTab(index) {
    if (window.dashboard) dashboard.switchParticipantTab(index);
}

function editParticipantScheduleField(participantIndex, scheduleIndex, fieldName) {
    if (window.dashboard) dashboard.editParticipantScheduleField(participantIndex, scheduleIndex, fieldName);
}

function cancelParticipantScheduleEdit(participantIndex, scheduleIndex, fieldName) {
    if (window.dashboard) dashboard.cancelParticipantScheduleEdit(participantIndex, scheduleIndex, fieldName);
}

// 액션 아이템 토글 함수
function toggleActionComplete(actionIndex) {
    if (window.dashboard) dashboard.toggleActionComplete(actionIndex);
}

// window 객체에 dashboard 할당 (전역 접근용)
window.dashboard = dashboard; 