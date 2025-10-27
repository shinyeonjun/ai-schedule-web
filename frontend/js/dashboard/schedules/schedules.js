class SchedulesSection {
    constructor() {
        this.sessions = [];
        this.currentSession = null;
        this.init();
    }

    // 초기화
    init() {
        console.log('📅 분석 결과 섹션 초기화');
        this.setupEventListeners();

        // 토큰이 있으면 바로 로드, 없으면 인증 완료 이벤트 대기
        const token = localStorage.getItem('mufi_token');
        if (token) {
            this.loadAnalysisSessions();
        } else {
            console.log('⏳ 토큰 없음, 인증 완료 대기 중...');
        }
    }

    // 이벤트 리스너 설정
    setupEventListeners() {
        // 새로고침 버튼
        const refreshBtn = document.querySelector('.refresh-sessions-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadAnalysisSessions();
            });
        }
    }

    // 분석 세션 목록 로드
    async loadAnalysisSessions() {
        try {
            const token = localStorage.getItem('mufi_token');
            if (!token) {
                this.showNotification('로그인이 필요합니다.', 'error');
                return;
            }

            const response = await fetch('/api/schedules/analysis-sessions', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            const result = await response.json();

            if (response.ok) {
                this.sessions = result.data.sessions || [];
                this.displayAnalysisSessions();
                this.showNotification(result.message, 'success');
            } else {
                this.showNotification(result.detail || '세션 목록을 불러오는데 실패했습니다.', 'error');
            }
        } catch (error) {
            console.error('❌ 분석 세션 로드 오류:', error);
            this.showNotification('세션 목록을 불러오는데 실패했습니다.', 'error');
        }
    }

    // 분석 세션 목록 표시
    displayAnalysisSessions() {
        const container = document.getElementById('sessionsContainer');
        if (!container) return;

        if (this.sessions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <i class="fas fa-calendar-times"></i>
                    </div>
                    <h3>저장된 분석 세션이 없습니다</h3>
                    <p>통화 분석에서 일정을 저장하면 여기에 표시됩니다.</p>
                    <button class="btn btn-primary" onclick="window.location.href='/dashboard#analysis'">
                        <i class="fas fa-plus"></i> 통화 분석하기
                    </button>
                </div>
            `;
            return;
        }

        const sessionsHTML = this.sessions.map((session, index) => {
            const createdDate = new Date(session.created_at);
            const formattedDate = createdDate.toLocaleDateString('ko-KR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });

            return `
                <div class="session-card" data-session-id="${session.analysis_session_id}">
                                    <div class="session-header">
                    <div class="session-info">
                        <h3 class="session-title" data-session-id="${session.analysis_session_id}" onclick="window.schedulesSection.editSessionTitle('${session.analysis_session_id}', '${session.analysis_source_name}')">${session.analysis_source_name}</h3>
                        <p class="session-date">${formattedDate}</p>
                    </div>
                        <div class="session-stats">
                            <div class="stat-item">
                                <span class="stat-label">총 일정</span>
                                <span class="stat-value">${session.total_schedules}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">그룹</span>
                                <span class="stat-value group">${session.group_count}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">개인</span>
                                <span class="stat-value personal">${session.personal_count}</span>
                            </div>
                        </div>
                    </div>
                    
                                         <div class="session-actions">
                         <button class="btn btn-outline-primary" onclick="window.schedulesSection.viewSessionDetails('${session.analysis_session_id}')">
                             <i class="fas fa-eye"></i> 일정 보기
                         </button>
                         <button class="btn btn-outline-danger" onclick="window.schedulesSection.deleteSession('${session.analysis_session_id}')">
                             <i class="fas fa-trash"></i> 일정 삭제
                         </button>
                     </div>
                </div>
            `;
        }).join('');

        container.innerHTML = sessionsHTML;
    }

    // 세션 상세보기
    async viewSessionDetails(sessionId) {
        try {
            const token = localStorage.getItem('mufi_token');
            const response = await fetch(`/api/schedules/session/${sessionId}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            const result = await response.json();

            if (response.ok) {
                this.currentSession = result.data;
                this.showSessionDetailsModal(result.data);
            } else {
                this.showNotification(result.detail || '세션 상세 정보를 불러오는데 실패했습니다.', 'error');
            }
        } catch (error) {
            console.error('❌ 세션 상세보기 오류:', error);
            this.showNotification('세션 상세 정보를 불러오는데 실패했습니다.', 'error');
        }
    }

    // 세션 상세 모달 표시
    showSessionDetailsModal(sessionData) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content session-details-modal">
                <div class="modal-header">
                    <h2>${sessionData.session.analysis_source_name}</h2>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="session-summary">
                        <div class="summary-item">
                            <span class="label">생성일:</span>
                            <span class="value">${new Date(sessionData.session.created_at).toLocaleString('ko-KR')}</span>
                        </div>
                        <div class="summary-item">
                            <span class="label">총 일정:</span>
                            <span class="value">${sessionData.session.total_schedules}개</span>
                        </div>
                        <div class="summary-item">
                            <span class="label">그룹 일정:</span>
                            <span class="value">${sessionData.session.group_count}개</span>
                        </div>
                        <div class="summary-item">
                            <span class="label">개인 일정:</span>
                            <span class="value">${sessionData.session.personal_count}개</span>
                        </div>
                    </div>
                    
                    <div class="schedules-list">
                        ${this.renderSchedulesList(sessionData.schedules)}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">
                        <i class="fas fa-times"></i> 닫기
                    </button>
                    <button class="btn btn-danger" onclick="window.schedulesSection.deleteSession('${sessionData.session.analysis_session_id}')">
                        <i class="fas fa-trash"></i> 일정 삭제
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    }

    // 일정 목록 렌더링
    renderSchedulesList(schedules) {
        let html = '';

        // 그룹 일정
        if (schedules.group && schedules.group.length > 0) {
            html += `
                <div class="schedule-group">
                    <h3 class="group-title">
                        <i class="fas fa-users"></i> 그룹 일정 (${schedules.group.length}개)
                    </h3>
                    ${schedules.group.map(schedule => this.renderScheduleCard(schedule)).join('')}
                </div>
            `;
        }

        // 개인 일정
        if (schedules.personal && schedules.personal.length > 0) {
            html += `
                <div class="schedule-group">
                    <h3 class="group-title">
                        <i class="fas fa-user"></i> 개인 일정 (${schedules.personal.length}개)
                    </h3>
                    ${schedules.personal.map(schedule => this.renderScheduleCard(schedule)).join('')}
                </div>
            `;
        }

        return html;
    }

    // 일정 카드 렌더링
    renderScheduleCard(schedule) {
        const startDate = new Date(schedule.start_datetime);
        const endDate = new Date(schedule.end_datetime);

        const formattedStart = startDate.toLocaleString('ko-KR', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        const formattedEnd = endDate.toLocaleString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit'
        });

        return `
            <div class="schedule-card" data-schedule-id="${schedule.id}">
                <div class="schedule-header">
                    <h4 class="schedule-title">${schedule.title}</h4>
                    <span class="schedule-type ${schedule.schedule_type}">
                        ${schedule.schedule_type === 'group' ? '그룹' : '개인'}
                    </span>
                </div>
                <div class="schedule-content">
                    <p class="schedule-description">${schedule.description}</p>
                    <div class="schedule-details">
                        <div class="detail-item">
                            <i class="fas fa-map-marker-alt"></i>
                            <span>${schedule.location || '장소 미정'}</span>
                        </div>
                        <div class="detail-item">
                            <i class="fas fa-clock"></i>
                            <span>${formattedStart} - ${formattedEnd}</span>
                        </div>
                                                 <div class="detail-item">
                             <i class="fas fa-users"></i>
                             <span>${this.formatParticipants(schedule.participants)}</span>
                         </div>
                    </div>
                </div>
                <div class="schedule-actions">
                    <button class="btn btn-sm btn-outline-primary" onclick="window.schedulesSection.editSchedule('${schedule.id}')" title="편집">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-success" onclick="window.schedulesSection.addToCalendar('${schedule.id}')" title="캘린더에 추가">
                        <i class="fas fa-calendar-plus"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-info" onclick="window.schedulesSection.sendEmail('${schedule.id}')" title="메일 보내기">
                        <i class="fas fa-envelope"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="window.schedulesSection.shareSchedule('${schedule.id}')" title="공유">
                        <i class="fas fa-share-alt"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="window.schedulesSection.deleteSchedule('${schedule.id}')" title="삭제">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }

    // 캘린더 추가 (개별 일정)
    // Google 토큰 상태 확인
    async checkGoogleTokenStatus() {
        const token = localStorage.getItem('mufi_token');
        if (!token) return false;

        try {
            const response = await fetch('/api/schedules/google-token-status', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();

            if (data.success && data.data.has_token && data.data.is_valid) {
                return true;
            } else {
                return false;
            }
        } catch (error) {
            console.error('토큰 상태 확인 오류:', error);
            return false;
        }
    }

    async addToCalendar(scheduleId) {
        try {
            console.log('캘린더 추가 시작:', scheduleId);

            const token = localStorage.getItem('mufi_token');
            if (!token) {
                this.showNotification('로그인이 필요합니다.', 'error');
                return;
            }

            console.log('🔍 Google Calendar API 직접 호출 시작');

            // Google Calendar에 직접 추가 (토큰 상태 확인 건너뛰기)
            const calendarResponse = await fetch(`/api/schedules/schedule/${scheduleId}/add-to-calendar`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            console.log('📡 Google Calendar API 응답 상태:', calendarResponse.status);

            const calendarResult = await calendarResponse.json();
            console.log('📄 Google Calendar API 응답:', calendarResult);

            if (calendarResponse.ok) {
                this.showNotification('일정이 성공적으로 Google Calendar에 추가되었습니다!', 'success');
            } else {
                console.error('❌ Google Calendar API 오류:', calendarResult);
                this.showNotification(calendarResult.detail || 'Google Calendar에 일정 추가에 실패했습니다.', 'error');
            }

        } catch (error) {
            console.error('❌ 캘린더 추가 오류:', error);
            this.showNotification('캘린더 추가에 실패했습니다.', 'error');
        }
    }

    // 메일 보내기 (세션 전체)
    sendEmail(sessionId) {
        // 개별 일정 메일 보내기로 리다이렉트
        this.sendScheduleEmail(sessionId);
    }

    // 세션 공유 (세션 전체)
    shareSession(sessionId) {
        this.showNotification('공유 기능은 준비 중입니다.', 'info');
        // TODO: 공유 로직 구현
    }

    // 개별 일정 캘린더 추가
    addScheduleToCalendar(scheduleId) {
        this.showNotification(`일정 ID ${scheduleId}를 캘린더에 추가합니다.`, 'info');
        // TODO: 개별 일정 캘린더 추가 로직 구현
    }

    // 개별 일정 메일 보내기
    async sendScheduleEmail(scheduleId) {
        try {
            // Gmail 인증 상태 확인
            const token = localStorage.getItem('mufi_token');
            if (!token) {
                this.showNotification('로그인이 필요합니다.', 'error');
                return;
            }

            // Gmail 인증 상태 확인
            const authResponse = await fetch('/api/schedules/gmail-auth-status', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            const authResult = await authResponse.json();

            if (!authResult.data.success) {
                this.showNotification(`Gmail 인증이 필요합니다: ${authResult.data.error || '알 수 없는 오류'}`, 'error');
                return;
            }

            // Gmail 전송 모달 표시
            this.showGmailSendModal(scheduleId);

        } catch (error) {
            console.error('❌ Gmail 전송 준비 오류:', error);
            this.showNotification('Gmail 전송 준비 중 오류가 발생했습니다.', 'error');
        }
    }

    // Gmail 전송 모달 표시 (다중 수신자 + 검색/드롭다운 + 칩)
    async showGmailSendModal(scheduleId) {
        // 수신자 옵션 로드 (내부 사용자 + 외부 인원)
        try {
            await this.loadRecipientOptions();
        } catch (e) {
            console.warn('수신자 목록 로드 실패:', e);
        }

        const modal = document.createElement('div');
        modal.className = 'modal-overlay';

        // 기본 제목: 일정 제목 연동 시도
        let defaultSubject = '일정 안내';
        try {
            if (this.currentSession && this.currentSession.schedules) {
                const all = [...(this.currentSession.schedules.group || []), ...(this.currentSession.schedules.personal || [])];
                const s = all.find(x => x.id === scheduleId);
                if (s && s.title) defaultSubject = `일정 안내: ${s.title}`;
            }
        } catch {}

        modal.innerHTML = `
            <div class="modal-content gmail-modal">
                <div class="modal-header">
                    <h3>Gmail로 일정 전송</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <form id="gmailSendForm">
                        <div class="form-group">
                            <label>수신자</label>
                            <div class="chips-input" id="recipientChips">
                                <div class="chips" id="recipientChipsList"></div>
                                <input type="text" id="recipientInput" class="chips-text" placeholder="이름이나 이메일을 입력하세요">
                            </div>
                            <div class="suggestions" id="recipientSuggestions"></div>
                            <div class="helper-text">내부 사용자/외부 인원을 검색해서 선택하거나 이메일을 직접 입력하세요. Enter 또는 콤마(,)로 추가</div>
                        </div>
                        <div class="form-group">
                            <label for="emailSubject">제목</label>
                            <input type="text" id="emailSubject" class="form-control" value="${defaultSubject}">
                        </div>
                        <div class="form-group">
                            <label for="emailMessage">내용 (선택)</label>
                            <textarea id="emailMessage" class="form-control" rows="4" placeholder="추가 메시지를 입력하세요..."></textarea>
                        </div>
                        <div class="form-actions">
                            <button type="button" class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">취소</button>
                            <button type="submit" class="btn btn-primary"><i class="fas fa-paper-plane"></i> 전송</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // 상태 초기화
        modal.__selectedRecipients = [];

        // 이벤트 바인딩
        const input = modal.querySelector('#recipientInput');
        const chipsList = modal.querySelector('#recipientChipsList');
        const suggestions = modal.querySelector('#recipientSuggestions');
        const form = modal.querySelector('#gmailSendForm');

        const renderSuggestions = (items) => {
            if (!items || items.length === 0) {
                suggestions.innerHTML = '';
                suggestions.style.display = 'none';
                return;
            }
            const html = items.map(item => `
                <div class="suggestion-item" data-email="${item.email}" data-name="${item.name}" data-type="${item.type}">
                    <div class="suggestion-main">
                        <span class="suggestion-name">${item.name || item.email}</span>
                        <span class="suggestion-email">${item.email}</span>
                    </div>
                    <span class="suggestion-badge ${item.type}">${item.type === 'user' ? '내부' : '외부'}</span>
                </div>
            `).join('');
            suggestions.innerHTML = html;
            suggestions.style.display = 'block';
        };

        const updateSuggestions = () => {
            const q = (input.value || '').trim().toLowerCase();
            if (!q) { suggestions.innerHTML = ''; suggestions.style.display = 'none'; return; }
            const filtered = (this.recipientOptions || []).filter(opt => {
                return (opt.email && opt.email.toLowerCase().includes(q)) || (opt.name && opt.name.toLowerCase().includes(q));
            }).slice(0, 8);
            renderSuggestions(filtered);
        };

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        const addChip = (name, email) => {
            if (!emailRegex.test(email)) {
                this.showNotification('유효한 이메일이 아닙니다.', 'error');
                return;
            }
            // 중복 방지
            if (modal.__selectedRecipients.some(r => r.email.toLowerCase() === email.toLowerCase())) {
                return;
            }
            modal.__selectedRecipients.push({ name: name || email, email });
            const chip = document.createElement('div');
            chip.className = 'chip';
            chip.innerHTML = `
                <span class="chip-text">${name ? `${name} <${email}>` : email}</span>
                <button class="chip-remove" title="제거">&times;</button>
            `;
            chip.querySelector('.chip-remove').addEventListener('click', () => {
                modal.__selectedRecipients = modal.__selectedRecipients.filter(r => r.email.toLowerCase() !== email.toLowerCase());
                chip.remove();
            });
            chipsList.appendChild(chip);
        };

        const tryAddFromInput = () => {
            const raw = (input.value || '').trim();
            if (!raw) return;
            // "이름 <email@domain>" 또는 email
            const angleMatch = raw.match(/^(.*)<([^>]+)>$/);
            if (angleMatch) {
                addChip(angleMatch[1].trim(), angleMatch[2].trim());
            } else {
                addChip('', raw);
            }
            input.value = '';
            suggestions.innerHTML = '';
            suggestions.style.display = 'none';
        };

        input.addEventListener('input', updateSuggestions);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ',' ) {
                e.preventDefault();
                tryAddFromInput();
            } else if (e.key === 'Backspace' && !input.value) {
                // 마지막 칩 제거
                const last = chipsList.lastElementChild;
                if (last) {
                    const text = last.querySelector('.chip-text')?.textContent || '';
                    last.remove();
                    if (modal.__selectedRecipients.length > 0) modal.__selectedRecipients.pop();
                }
            }
        });

        suggestions.addEventListener('click', (e) => {
            const item = e.target.closest('.suggestion-item');
            if (!item) return;
            const email = item.getAttribute('data-email');
            const name = item.getAttribute('data-name');
            addChip(name, email);
            input.value = '';
            suggestions.innerHTML = '';
            suggestions.style.display = 'none';
        });

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.sendGmailEmail(scheduleId, modal);
        });
    }

    // Gmail 이메일 전송 (다중 수신자 + ICS 첨부)
    async sendGmailEmail(scheduleId, modal) {
        try {
            const token = localStorage.getItem('mufi_token');
            const subject = modal.querySelector('#emailSubject').value;
            const message = modal.querySelector('#emailMessage').value;

            // 수신자 수집 (칩 + 입력 필드 남은 값)
            const recipients = (modal.__selectedRecipients || []).map(r => r.email);
            const pending = (modal.querySelector('#recipientInput')?.value || '').trim();
            if (pending) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (emailRegex.test(pending)) {
                    recipients.push(pending);
                }
            }

            if (!recipients.length) {
                this.showNotification('수신자를 한 명 이상 추가해주세요.', 'error');
                return;
            }

            // 로딩 상태 표시
            const submitBtn = modal.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 전송 중...';
            submitBtn.disabled = true;

            const response = await fetch(`/api/schedules/${scheduleId}/send-gmail`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    recipients: recipients,
                    subject: subject,
                    message: message
                })
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification('이메일이 성공적으로 전송되었습니다!', 'success');
                modal.remove();
            } else {
                this.showNotification(result.detail || '이메일 전송에 실패했습니다.', 'error');
            }

        } catch (error) {
            console.error('❌ Gmail 전송 오류:', error);
            this.showNotification('이메일 전송 중 오류가 발생했습니다.', 'error');
        } finally {
            // 버튼 상태 복원
            const submitBtn = modal.querySelector('button[type="submit"]');
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> 전송';
            submitBtn.disabled = false;
        }
    }

    // 수신자 옵션 로드 (내부 사용자 + 외부 인원)
    async loadRecipientOptions() {
        this.recipientOptions = [];
        try {
            const token = localStorage.getItem('mufi_token');
            if (!token) return;
            const [usersRes, contactsRes] = await Promise.all([
                fetch('/api/members/mufi-users', { headers: { 'Authorization': `Bearer ${token}` } }),
                fetch('/api/members/external-contacts', { headers: { 'Authorization': `Bearer ${token}` } })
            ]);
            const usersJson = await usersRes.json();
            const contactsJson = await contactsRes.json();
            const users = (usersJson?.data?.users || []).map(u => ({ type: 'user', name: u.name || u.email, email: u.email }));
            const contacts = (contactsJson?.data?.contacts || []).map(c => ({ type: 'external', name: c.name || c.email, email: c.email }));
            this.recipientOptions = [...users, ...contacts].filter(x => x.email);
        } catch (e) {
            console.warn('수신자 옵션 로드 실패:', e);
        }
    }

    // 개별 일정 공유
    shareSchedule(scheduleId) {
        this.showNotification(`일정 ID ${scheduleId}를 공유합니다.`, 'info');
        // TODO: 개별 일정 공유 로직 구현
    }

    // 일정 편집
    editSchedule(scheduleId) {
        const scheduleCard = document.querySelector(`[data-schedule-id="${scheduleId}"]`);
        if (!scheduleCard) {
            this.showNotification('일정을 찾을 수 없습니다.', 'error');
            return;
        }

        // 편집 모드 활성화
        scheduleCard.classList.add('editing');

        // 편집 가능한 필드들을 입력 필드로 변환
        this.convertScheduleFieldsToInputs(scheduleCard, scheduleId);

        // 편집 액션 버튼 표시
        this.showScheduleEditActions(scheduleCard, scheduleId);
    }

    // 일정 필드를 입력 필드로 변환
    convertScheduleFieldsToInputs(card, scheduleId) {
        const titleField = card.querySelector('.schedule-title');
        const descriptionField = card.querySelector('.schedule-description');
        const locationField = card.querySelector('.detail-item:first-child span');
        const timeField = card.querySelector('.detail-item:nth-child(2) span');
        const participantsField = card.querySelector('.detail-item:last-child span');

        // 제목 편집
        if (titleField) {
            const originalTitle = titleField.textContent;
            titleField.innerHTML = `
                <input type="text" class="edit-input" value="${originalTitle}" 
                       data-original="${originalTitle}" data-field="title">
            `;
        }

        // 설명 편집
        if (descriptionField) {
            const originalDescription = descriptionField.textContent;
            descriptionField.innerHTML = `
                <textarea class="edit-textarea" data-original="${originalDescription}" data-field="description">${originalDescription}</textarea>
            `;
        }

        // 장소 편집
        if (locationField) {
            const originalLocation = locationField.textContent;
            locationField.innerHTML = `
                <input type="text" class="edit-input" value="${originalLocation}" 
                       data-original="${originalLocation}" data-field="location">
            `;
        }

        // 시간 편집
        if (timeField) {
            const originalTime = timeField.textContent.trim();

            // 현재 일정 카드에서 실제 데이터베이스 시간 가져오기
            const scheduleCard = timeField.closest('.schedule-card');
            const scheduleId = scheduleCard.dataset.scheduleId;

            // 현재 세션에서 해당 일정의 실제 시간 데이터 찾기
            let actualStartTime = '';
            let actualEndTime = '';

            if (this.currentSession && this.currentSession.schedules) {
                const allSchedules = [...(this.currentSession.schedules.group || []), ...(this.currentSession.schedules.personal || [])];
                const currentSchedule = allSchedules.find(s => s.id === scheduleId);

                if (currentSchedule && currentSchedule.start_datetime && currentSchedule.end_datetime) {
                    try {
                        // UTC 시간을 로컬 시간으로 변환
                        const startDate = new Date(currentSchedule.start_datetime);
                        const endDate = new Date(currentSchedule.end_datetime);

                        // 로컬 시간대의 datetime-local 형식으로 변환
                        const year = startDate.getFullYear();
                        const month = String(startDate.getMonth() + 1).padStart(2, '0');
                        const day = String(startDate.getDate()).padStart(2, '0');
                        const startHour = String(startDate.getHours()).padStart(2, '0');
                        const startMinute = String(startDate.getMinutes()).padStart(2, '0');
                        const endHour = String(endDate.getHours()).padStart(2, '0');
                        const endMinute = String(endDate.getMinutes()).padStart(2, '0');

                        actualStartTime = `${year}-${month}-${day}T${startHour}:${startMinute}`;
                        actualEndTime = `${year}-${month}-${day}T${endHour}:${endMinute}`;

                        console.log('실제 DB 시간:', {
                            original: originalTime,
                            start: currentSchedule.start_datetime,
                            end: currentSchedule.end_datetime,
                            convertedStart: actualStartTime,
                            convertedEnd: actualEndTime,
                            startDate: startDate,
                            endDate: endDate
                        });
                    } catch (e) {
                        console.warn('시간 변환 실패:', e);
                        // 기본값 설정
                        const now = new Date();
                        const year = now.getFullYear();
                        const month = String(now.getMonth() + 1).padStart(2, '0');
                        const day = String(now.getDate()).padStart(2, '0');
                        actualStartTime = `${year}-${month}-${day}T14:30`;
                        actualEndTime = `${year}-${month}-${day}T15:00`;
                    }
                } else {
                    // DB 데이터가 없으면 기본값 설정
                    const now = new Date();
                    const year = now.getFullYear();
                    const month = String(now.getMonth() + 1).padStart(2, '0');
                    const day = String(now.getDate()).padStart(2, '0');
                    actualStartTime = `${year}-${month}-${day}T14:30`;
                    actualEndTime = `${year}-${month}-${day}T15:00`;
                }
            } else {
                // 세션 데이터가 없으면 기본값 설정
                const now = new Date();
                const year = now.getFullYear();
                const month = String(now.getMonth() + 1).padStart(2, '0');
                const day = String(now.getDate()).padStart(2, '0');
                actualStartTime = `${year}-${month}-${day}T14:30`;
                actualEndTime = `${year}-${month}-${day}T15:00`;
            }

            timeField.innerHTML = `
                 <div class="time-edit-container" data-original="${originalTime}">
                     <input type="datetime-local" class="edit-input" value="${actualStartTime}" 
                            data-original="${originalTime}" data-field="start_datetime">
                     <span>-</span>
                     <input type="datetime-local" class="edit-input" value="${actualEndTime}" 
                            data-original="${originalTime}" data-field="end_datetime">
                 </div>
             `;
        }

        // 참여자 편집
        if (participantsField) {
            const originalParticipants = participantsField.textContent;
            participantsField.innerHTML = `
                <input type="text" class="edit-input" value="${originalParticipants}" 
                       data-original="${originalParticipants}" data-field="participants">
            `;
        }
    }

    // 시간 범위 파싱
    parseTimeRange(timeString) {
        try {
            // "12월 15일 14:30 - 16:30" 형식을 파싱
            const timeMatch = timeString.match(/(\d{1,2})월\s*(\d{1,2})일\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})/);
            if (timeMatch) {
                const month = parseInt(timeMatch[1]);
                const day = parseInt(timeMatch[2]);
                const startHour = parseInt(timeMatch[3]);
                const startMinute = parseInt(timeMatch[4]);
                const endHour = parseInt(timeMatch[5]);
                const endMinute = parseInt(timeMatch[6]);

                // 현재 연도를 기준으로 datetime-local 형식 생성
                const currentYear = new Date().getFullYear();
                const startDateTime = `${currentYear}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}T${String(startHour).padStart(2, '0')}:${String(startMinute).padStart(2, '0')}`;
                const endDateTime = `${currentYear}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}T${String(endHour).padStart(2, '0')}:${String(endMinute).padStart(2, '0')}`;

                return [startDateTime, endDateTime];
            }

            // 다른 형식 시도: "14:30 - 16:30"
            const simpleTimeMatch = timeString.match(/(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})/);
            if (simpleTimeMatch) {
                const startHour = parseInt(simpleTimeMatch[1]);
                const startMinute = parseInt(simpleTimeMatch[2]);
                const endHour = parseInt(simpleTimeMatch[3]);
                const endMinute = parseInt(simpleTimeMatch[4]);

                // 현재 날짜를 기준으로 datetime-local 형식 생성
                const today = new Date();
                const startDateTime = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}T${String(startHour).padStart(2, '0')}:${String(startMinute).padStart(2, '0')}`;
                const endDateTime = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}T${String(endHour).padStart(2, '0')}:${String(endMinute).padStart(2, '0')}`;

                return [startDateTime, endDateTime];
            }
        } catch (e) {
            console.warn('시간 파싱 실패:', e);
        }

        // 파싱 실패 시 현재 시간을 기준으로 반환
        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth() + 1;
        const currentDay = now.getDate();

        const defaultStartTime = `${currentYear}-${String(currentMonth).padStart(2, '0')}-${String(currentDay).padStart(2, '0')}T14:30`;
        const defaultEndTime = `${currentYear}-${String(currentMonth).padStart(2, '0')}-${String(currentDay).padStart(2, '0')}T16:30`;

        return [defaultStartTime, defaultEndTime];
    }

    // 참여자 데이터 포맷
    formatParticipants(participants) {
        if (!participants) {
            return '참여자 없음';
        }

        // 배열인 경우
        if (Array.isArray(participants)) {
            return participants.length > 0 ? participants.join(', ') : '참여자 없음';
        }

        // 문자열인 경우
        if (typeof participants === 'string') {
            return participants.trim() || '참여자 없음';
        }

        // JSON 문자열인 경우
        try {
            const parsed = JSON.parse(participants);
            if (Array.isArray(parsed)) {
                return parsed.length > 0 ? parsed.join(', ') : '참여자 없음';
            }
        } catch (e) {
            // 파싱 실패 시 문자열로 처리
        }

        return '참여자 없음';
    }

    // 일정 편집 액션 버튼 표시
    showScheduleEditActions(card, scheduleId) {
        const actionsContainer = card.querySelector('.schedule-actions');
        if (!actionsContainer) return;

        // 기존 버튼들 숨기기
        const existingButtons = actionsContainer.querySelectorAll('.btn');
        existingButtons.forEach(btn => btn.style.display = 'none');

        // 편집 액션 버튼 추가
        actionsContainer.innerHTML = `
            <button class="btn btn-sm btn-success" onclick="window.schedulesSection.completeScheduleEdit('${scheduleId}')" title="완료">
                <i class="fas fa-check"></i>
            </button>
            <button class="btn btn-sm btn-danger" onclick="window.schedulesSection.cancelScheduleEdit('${scheduleId}')" title="취소">
                <i class="fas fa-times"></i>
            </button>
        `;
    }

    // 일정 편집 완료
    async completeScheduleEdit(scheduleId) {
        const scheduleCard = document.querySelector(`[data-schedule-id="${scheduleId}"]`);
        if (!scheduleCard) return;

        try {
            // 편집된 데이터 수집
            const editedData = this.collectScheduleEditData(scheduleCard);

            // 변경사항이 없으면 편집 모드만 종료
            if (Object.keys(editedData).length === 0) {
                this.showNotification('변경사항이 없습니다.', 'info');
                this.exitScheduleEditMode(scheduleCard);
                return;
            }

            // 서버에 업데이트 요청
            const token = localStorage.getItem('mufi_token');
            const response = await fetch(`/api/schedules/schedule/${scheduleId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(editedData)
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification('일정이 성공적으로 수정되었습니다.', 'success');

                // 현재 세션의 일정 목록 새로고침
                const sessionId = this.currentSession?.session?.analysis_session_id;
                if (sessionId) {
                    // 모달 닫기
                    const modal = document.querySelector('.modal-overlay');
                    if (modal) {
                        modal.remove();
                    }
                    // 세션 상세보기 다시 열기
                    this.viewSessionDetails(sessionId);
                } else {
                    this.exitScheduleEditMode(scheduleCard);
                }
            } else {
                this.showNotification(result.detail || '일정 수정에 실패했습니다.', 'error');
            }
        } catch (error) {
            console.error('❌ 일정 편집 완료 오류:', error);
            this.showNotification('일정 수정에 실패했습니다.', 'error');
        }
    }

    // 편집된 일정 데이터 수집
    collectScheduleEditData(card) {
        const data = {};
        const scheduleId = card.dataset.scheduleId;

        // 현재 세션에서 해당 일정의 원본 데이터 찾기
        let originalSchedule = null;
        if (this.currentSession && this.currentSession.schedules) {
            const allSchedules = [...(this.currentSession.schedules.group || []), ...(this.currentSession.schedules.personal || [])];
            originalSchedule = allSchedules.find(s => s.id === scheduleId);
        }

        // 각 입력 필드에서 데이터 수집
        const inputs = card.querySelectorAll('.edit-input, .edit-textarea');
        inputs.forEach(input => {
            const field = input.dataset.field;
            const value = input.value.trim();
            const originalValue = input.dataset.original;

            // 값이 변경된 경우에만 포함
            if (value !== originalValue) {
                if (field === 'start_datetime' || field === 'end_datetime') {
                    // 시간 필드의 경우 원본 데이터와 비교
                    try {
                        if (originalSchedule) {
                            const originalTime = field === 'start_datetime' ?
                                originalSchedule.start_datetime : originalSchedule.end_datetime;

                            // 유효한 날짜인지 확인
                            const newDate = new Date(value);
                            if (!isNaN(newDate.getTime())) {
                                // ISO 형식으로 변환 (UTC)
                                const isoTime = newDate.toISOString();

                                // 원본과 비교 (시간대 차이 고려)
                                const originalDate = new Date(originalTime);
                                const timeDiff = Math.abs(newDate.getTime() - originalDate.getTime());

                                // 1분 이상 차이가 있을 때만 업데이트
                                if (timeDiff > 60000) {
                                    data[field] = isoTime;
                                    console.log(`${field} 업데이트:`, {
                                        original: originalTime,
                                        new: isoTime,
                                        diff: timeDiff
                                    });
                                }
                            } else {
                                console.warn(`유효하지 않은 시간 값: ${value}`);
                            }
                        } else {
                            // 유효한 날짜인지 확인
                            const newDate = new Date(value);
                            if (!isNaN(newDate.getTime())) {
                                data[field] = newDate.toISOString();
                            } else {
                                console.warn(`유효하지 않은 시간 값: ${value}`);
                            }
                        }
                    } catch (e) {
                        console.warn(`시간 변환 오류 (${field}):`, e);
                    }
                } else {
                    data[field] = value;
                }
            }
        });

        return data;
    }

    // 일정 편집 취소
    cancelScheduleEdit(scheduleId) {
        const scheduleCard = document.querySelector(`[data-schedule-id="${scheduleId}"]`);
        if (!scheduleCard) return;

        this.exitScheduleEditMode(scheduleCard);
        this.showNotification('편집이 취소되었습니다.', 'info');
    }

    // 일정 편집 모드 종료
    exitScheduleEditMode(card) {
        // 편집 모드 클래스 제거
        card.classList.remove('editing');

        // 원래 텍스트로 복원
        const inputs = card.querySelectorAll('.edit-input, .edit-textarea');
        inputs.forEach(input => {
            const originalValue = input.dataset.original;
            const field = input.dataset.field;

            if (field === 'title') {
                const titleElement = input.parentElement;
                if (titleElement) {
                    titleElement.textContent = originalValue;
                }
            } else if (field === 'description') {
                const descElement = input.parentElement;
                if (descElement) {
                    descElement.textContent = originalValue;
                }
            } else if (field === 'location') {
                const locElement = input.parentElement;
                if (locElement) {
                    locElement.textContent = originalValue;
                }
            } else if (field === 'start_datetime' || field === 'end_datetime') {
                // 시간 필드는 복잡하므로 전체 시간 컨테이너를 복원
                const timeContainer = input.closest('.time-edit-container');
                if (timeContainer && timeContainer.parentElement) {
                    const originalTime = timeContainer.dataset.original || originalValue;

                    // 원본 시간이 비어있거나 유효하지 않으면 기본값 사용
                    if (!originalTime || originalTime.trim() === '') {
                        const now = new Date();
                        const year = now.getFullYear();
                        const month = String(now.getMonth() + 1).padStart(2, '0');
                        const day = String(now.getDate()).padStart(2, '0');
                        timeContainer.parentElement.textContent = `${month}월 ${day}일 14:30 - 15:00`;
                    } else {
                        timeContainer.parentElement.textContent = originalTime;
                    }
                    console.log('시간 복원:', originalTime);
                }
            } else if (field === 'participants') {
                const partElement = input.parentElement;
                if (partElement) {
                    partElement.textContent = originalValue;
                }
            }
        });

        // 원래 액션 버튼들 복원
        this.restoreScheduleActions(card);
    }

    // 일정 액션 버튼 복원
    restoreScheduleActions(card) {
        const actionsContainer = card.querySelector('.schedule-actions');
        if (!actionsContainer) return;

        // 현재 일정 ID 가져오기
        const scheduleId = card.dataset.scheduleId;

        // 원래 버튼들 복원
        actionsContainer.innerHTML = `
            <button class="btn btn-sm btn-outline-primary" onclick="window.schedulesSection.editSchedule('${scheduleId}')" title="편집">
                <i class="fas fa-edit"></i>
            </button>
            <button class="btn btn-sm btn-outline-success" onclick="window.schedulesSection.addToCalendar('${scheduleId}')" title="캘린더에 추가">
                <i class="fas fa-calendar-plus"></i>
            </button>
            <button class="btn btn-sm btn-outline-info" onclick="window.schedulesSection.sendEmail('${scheduleId}')" title="메일 보내기">
                <i class="fas fa-envelope"></i>
            </button>
            <button class="btn btn-sm btn-outline-secondary" onclick="window.schedulesSection.shareSchedule('${scheduleId}')" title="공유">
                <i class="fas fa-share-alt"></i>
            </button>
            <button class="btn btn-sm btn-outline-danger" onclick="window.schedulesSection.deleteSchedule('${scheduleId}')" title="삭제">
                <i class="fas fa-trash"></i>
            </button>
        `;
    }

    // 개별 일정 삭제
    async deleteSchedule(scheduleId) {
        if (!confirm('정말로 이 일정을 삭제하시겠습니까?')) {
            return;
        }

        try {
            console.log('일정 삭제 시작:', scheduleId);
            const token = localStorage.getItem('mufi_token');
            const response = await fetch(`/api/schedules/schedule/${scheduleId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification('일정이 성공적으로 삭제되었습니다.', 'success');
                console.log('서버에서 일정 삭제 성공');

                // 현재 세션에서 삭제된 일정 제거
                if (this.currentSession && this.currentSession.schedules) {
                    console.log('삭제 전 세션 데이터:', this.currentSession);

                    // 그룹 일정에서 제거
                    if (this.currentSession.schedules.group) {
                        this.currentSession.schedules.group = this.currentSession.schedules.group.filter(
                            schedule => schedule.id !== scheduleId
                        );
                    }

                    // 개인 일정에서 제거
                    if (this.currentSession.schedules.personal) {
                        this.currentSession.schedules.personal = this.currentSession.schedules.personal.filter(
                            schedule => schedule.id !== scheduleId
                        );
                    }

                    // 세션 통계 업데이트
                    if (this.currentSession.session) {
                        this.currentSession.session.total_schedules =
                            (this.currentSession.schedules.group?.length || 0) +
                            (this.currentSession.schedules.personal?.length || 0);
                        this.currentSession.session.group_count = this.currentSession.schedules.group?.length || 0;
                        this.currentSession.session.personal_count = this.currentSession.schedules.personal?.length || 0;
                    }

                    console.log('삭제 후 세션 데이터:', this.currentSession);

                    // 모달 내용 즉시 갱신
                    setTimeout(() => {
                        this.refreshModalContent();
                    }, 100); // 약간의 지연을 두어 DOM 업데이트가 완료된 후 갱신

                    // 메인 세션 목록도 갱신
                    this.updateMainSessionList();
                } else {
                    console.log('currentSession 또는 schedules가 없습니다.');
                }
            } else {
                this.showNotification(result.detail || '일정 삭제에 실패했습니다.', 'error');
            }
        } catch (error) {
            console.error('❌ 일정 삭제 오류:', error);
            this.showNotification('일정 삭제에 실패했습니다.', 'error');
        }
    }

    // 세션 삭제
    async deleteSession(sessionId) {
        if (!confirm('정말로 이 분석 세션을 삭제하시겠습니까?\n모든 일정이 영구적으로 삭제됩니다.')) {
            return;
        }

        try {
            const token = localStorage.getItem('mufi_token');
            const response = await fetch(`/api/schedules/session/${sessionId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification(result.message, 'success');
                this.loadAnalysisSessions(); // 목록 새로고침

                // 모달이 열려있다면 닫기
                const modal = document.querySelector('.modal-overlay');
                if (modal) {
                    modal.remove();
                }
            } else {
                this.showNotification(result.detail || '세션 삭제에 실패했습니다.', 'error');
            }
        } catch (error) {
            console.error('❌ 세션 삭제 오류:', error);
            this.showNotification('세션 삭제에 실패했습니다.', 'error');
        }
    }

    // 세션 제목 편집
    editSessionTitle(sessionId, currentTitle) {
        const titleElement = document.querySelector(`[data-session-id="${sessionId}"].session-title`);
        if (!titleElement) return;

        // 원본 텍스트 저장 (안전한 방법)
        const originalText = titleElement.textContent || titleElement.innerText || currentTitle || '';

        // 입력 필드로 변경 (안전한 HTML 생성)
        const inputHtml = document.createElement('input');
        inputHtml.type = 'text';
        inputHtml.className = 'session-title-input';
        inputHtml.value = originalText;
        inputHtml.setAttribute('data-original', originalText);
        inputHtml.setAttribute('data-session-id', sessionId);

        // 기존 내용을 입력 필드로 교체
        titleElement.innerHTML = '';
        titleElement.appendChild(inputHtml);

        const input = titleElement.querySelector('.session-title-input');
        if (!input) return;

        input.focus();
        input.select();

        // 이벤트 리스너 추가
        const handleSubmit = () => {
            const newTitle = input.value.trim();
            if (newTitle && newTitle !== originalText) {
                this.updateSessionTitle(sessionId, newTitle);
            } else {
                // 변경사항이 없으면 원래 텍스트로 복원
                titleElement.textContent = originalText;
            }
        };

        const handleCancel = () => {
            titleElement.textContent = originalText;
        };

        // Enter 키로 제출
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleSubmit();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                handleCancel();
            }
        });

        // 포커스 아웃 시 제출
        input.addEventListener('blur', handleSubmit);
    }

    // HTML 엔티티 디코딩
    decodeHtmlEntities(text) {
        if (!text) return '';
        const textarea = document.createElement('textarea');
        textarea.innerHTML = text;
        return textarea.value;
    }

    // HTML 특수문자 이스케이프
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 세션 제목 업데이트
    async updateSessionTitle(sessionId, newTitle) {
        try {
            const token = localStorage.getItem('mufi_token');
            const response = await fetch(`/api/schedules/session/${sessionId}/title`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ analysis_source_name: newTitle })
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification('세션 제목이 성공적으로 수정되었습니다.', 'success');

                // 입력 필드를 원래 텍스트로 복원 (안전한 방법)
                const titleElement = document.querySelector(`[data-session-id="${sessionId}"].session-title`);
                if (titleElement) {
                    // 입력 필드 제거하고 텍스트로 복원
                    titleElement.innerHTML = '';
                    titleElement.textContent = newTitle;
                }

                // 현재 세션 목록에서 해당 세션의 제목 업데이트
                const sessionIndex = this.sessions.findIndex(s => s.analysis_session_id === sessionId);
                if (sessionIndex !== -1) {
                    this.sessions[sessionIndex].analysis_source_name = newTitle;
                }
            } else {
                this.showNotification(result.detail || '세션 제목 수정에 실패했습니다.', 'error');

                // 실패 시 원래 텍스트로 복원
                const titleElement = document.querySelector(`[data-session-id="${sessionId}"].session-title`);
                if (titleElement) {
                    const input = titleElement.querySelector('.session-title-input');
                    if (input) {
                        titleElement.innerHTML = '';
                        titleElement.textContent = input.dataset.original;
                    }
                }
            }
        } catch (error) {
            console.error('❌ 세션 제목 수정 오류:', error);
            this.showNotification('세션 제목 수정에 실패했습니다.', 'error');

            // 오류 시 원래 텍스트로 복원
            const titleElement = document.querySelector(`[data-session-id="${sessionId}"].session-title`);
            if (titleElement) {
                const input = titleElement.querySelector('.session-title-input');
                if (input) {
                    titleElement.innerHTML = '';
                    titleElement.textContent = input.dataset.original;
                }
            }
        }
    }

    // 모달 내용 갱신
    refreshModalContent() {
        const modal = document.querySelector('.modal-overlay');
        if (!modal || !this.currentSession) {
            console.log('모달 또는 세션 데이터가 없습니다.');
            return;
        }

        console.log('모달 내용 갱신 시작:', this.currentSession);

        // 세션 요약 정보 갱신
        const summaryItems = modal.querySelectorAll('.summary-item .value');
        if (summaryItems.length >= 4) {
            summaryItems[1].textContent = `${this.currentSession.session.total_schedules}개`;
            summaryItems[2].textContent = `${this.currentSession.session.group_count}개`;
            summaryItems[3].textContent = `${this.currentSession.session.personal_count}개`;
            console.log('요약 정보 갱신 완료');
        }

        // 일정 목록 갱신
        const schedulesList = modal.querySelector('.schedules-list');
        if (schedulesList) {
            if (this.currentSession.session.total_schedules === 0) {
                // 일정이 모두 삭제된 경우
                schedulesList.innerHTML = `
                    <div class="empty-schedules">
                        <div class="empty-icon">
                            <i class="fas fa-calendar-times"></i>
                        </div>
                        <h3>일정이 없습니다</h3>
                        <p>모든 일정이 삭제되었습니다.</p>
                    </div>
                `;
                console.log('빈 일정 상태로 갱신 완료');
            } else {
                // 일정이 있는 경우
                schedulesList.innerHTML = this.renderSchedulesList(this.currentSession.schedules);
                console.log('일정 목록 갱신 완료');
            }
        } else {
            console.log('schedules-list 요소를 찾을 수 없습니다.');
        }
    }

    // 메인 세션 목록 갱신
    updateMainSessionList() {
        if (!this.currentSession) {
            console.log('currentSession이 없어서 메인 목록 갱신을 건너뜁니다.');
            return;
        }

        console.log('메인 세션 목록 갱신 시작');

        // 현재 세션 ID
        const sessionId = this.currentSession.session.analysis_session_id;

        // this.sessions 배열에서 해당 세션 찾기
        const sessionIndex = this.sessions.findIndex(s => s.analysis_session_id === sessionId);

        if (sessionIndex !== -1) {
            // 세션 통계 업데이트
            this.sessions[sessionIndex].total_schedules = this.currentSession.session.total_schedules;
            this.sessions[sessionIndex].group_count = this.currentSession.session.group_count;
            this.sessions[sessionIndex].personal_count = this.currentSession.session.personal_count;

            console.log('세션 데이터 업데이트 완료:', this.sessions[sessionIndex]);

            // UI 갱신
            this.displayAnalysisSessions();
            console.log('메인 세션 목록 UI 갱신 완료');
        } else {
            console.log('메인 세션 목록에서 해당 세션을 찾을 수 없습니다.');
        }
    }

    // 알림 표시
    showNotification(message, type = 'info') {
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
            notification.remove();
        }, 3000);
    }

    // Gmail 인증 상태 확인
    async checkGmailAuth() {
        return await GmailUtils.checkGmailAuth();
    }

    // Gmail 인증 요청
    async requestGmailAuth() {
        return await GmailUtils.requestGmailAuth();
    }
}

// 전역 객체로 등록
console.log('🔄 SchedulesSection 전역 객체 등록 시작');

try {
    window.schedulesSection = new SchedulesSection();
    console.log('✅ SchedulesSection 전역 객체 등록 성공:', window.schedulesSection);
} catch (error) {
    console.error('❌ SchedulesSection 전역 객체 등록 실패:', error);

    // 폴백: 기본 객체 생성
    window.schedulesSection = {
        addToCalendar: function (scheduleId) {
            console.log('🔄 캘린더 추가 시작 (폴백):', scheduleId);
            alert('캘린더 추가 테스트: ' + scheduleId);
        },
        showNotification: function (message, type) {
            console.log('알림:', message, type);
            alert(message);
        }
    };
    console.log('⚠️ SchedulesSection 폴백 객체 생성됨');
}

// 인증 완료 이벤트 리스너 등록
document.addEventListener('mufi-auth-completed', (event) => {
    console.log('🎉 인증 완료 이벤트 수신, 분석 결과 섹션 초기화');
    if (window.schedulesSection && window.schedulesSection.loadAnalysisSessions) {
        window.schedulesSection.loadAnalysisSessions();
    } else {
        console.log('⚠️ schedulesSection이 없거나 loadAnalysisSessions 메서드가 없습니다.');
    }
});

// 페이지 로드 완료 시 확인
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM 로드 완료, schedulesSection 상태 확인:', window.schedulesSection);
});

// Gmail 관련 유틸리티 함수들
const GmailUtils = {
    // Gmail 인증 상태 확인 및 처리
    async checkGmailAuth() {
        try {
            const token = localStorage.getItem('mufi_token');
            if (!token) return false;

            const response = await fetch('/api/schedules/gmail-auth-status', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            const result = await response.json();
            
            console.log('🔍 Gmail 인증 상태 응답:', result);

            if (result.success && result.data.success) {
                console.log('✅ Gmail 인증 완료 - DB 토큰 사용 가능');
                return true;
            } else {
                console.log('⚠️ Gmail 인증 필요:', result.data.error);
                return false;
            }
        } catch (error) {
            console.error('❌ Gmail 인증 상태 확인 실패:', error);
            return false;
        }
    },

    // Gmail 인증 요청
    async requestGmailAuth() {
        try {
            // 직접 Google OAuth URL 생성
            const clientId = '900953828805-82ccegsl26mlo0qvhu92pqhnqvaktrn4.apps.googleusercontent.com';
            const redirectUri = 'http://localhost:8000/oauth/google/callback';
            const scope = 'openid email profile https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/gmail.send';

            const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
                `client_id=${clientId}&` +
                `redirect_uri=${encodeURIComponent(redirectUri)}&` +
                `response_type=code&` +
                `scope=${encodeURIComponent(scope)}&` +
                `access_type=offline&` +
                `prompt=consent`;

            // 새 창에서 Google 인증 페이지 열기
            const authWindow = window.open(
                authUrl,
                'google-auth',
                'width=500,height=600,scrollbars=yes,resizable=yes'
            );

            // 인증 완료 감지
            const checkClosed = setInterval(() => {
                if (authWindow.closed) {
                    clearInterval(checkClosed);
                    // 인증 완료 후 페이지 새로고침 또는 상태 업데이트
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                }
            }, 1000);

            return true;
        } catch (error) {
            console.error('❌ Gmail 인증 요청 실패:', error);
            return false;
        }
    },

    // 이메일 전송 (Gmail 인증 확인 포함)
    async sendScheduleEmail(scheduleId, recipientEmail, subject = '일정 안내') {
        try {
            // Gmail 인증 상태 확인
            const isAuthenticated = await this.checkGmailAuth();

            if (!isAuthenticated) {
                // 인증이 필요한 경우 사용자에게 알림
                const confirmAuth = confirm('Gmail 전송을 위해 Google 계정 인증이 필요합니다. 인증 페이지로 이동하시겠습니까?');

                if (confirmAuth) {
                    await this.requestGmailAuth();
                    return;
                } else {
                    console.log('Gmail 인증이 취소되었습니다.');
                    return;
                }
            }

            // 인증이 완료된 경우 이메일 전송
            const token = localStorage.getItem('mufi_token');

            const response = await fetch(`/api/schedules/${scheduleId}/send-gmail`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    recipient_email: recipientEmail,
                    subject: subject,
                    message: '일정 정보를 공유합니다.'
                })
            });

            const result = await response.json();

            if (result.success) {
                console.log('이메일이 성공적으로 전송되었습니다.');
                return true;
            } else {
                console.error('이메일 전송에 실패했습니다:', result.detail);
                return false;
            }

        } catch (error) {
            console.error('❌ 이메일 전송 실패:', error);
            return false;
        }
    }
};