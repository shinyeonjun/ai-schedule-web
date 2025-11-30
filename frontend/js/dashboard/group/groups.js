// 그룹 관리 섹션
console.log('📦 groups.js 파일 로드됨');

window.groupSection = {
    myGroups: [],
    initialized: false,
    eventListenersSetup: false,
    isLoading: false,
    lastLoadTime: 0,

    // 초기화
    init() {
        // 이미 초기화된 경우 스킵
        if (this.initialized) {
            console.log('⚠️ 그룹 섹션은 이미 초기화되었습니다. 스킵합니다.');
            return;
        }

        console.log('🔧 그룹 섹션 초기화');
        this.setupEventListeners();
        this.initialized = true;
    },

    // 데이터 로드 (별도 함수로 분리)
    loadData() {
        console.log('📥 그룹 데이터 로드');
        // 중복 호출 방지 (1초 이내 재호출 방지)
        const now = Date.now();
        if (this.isLoading || (now - this.lastLoadTime < 1000)) {
            console.log('⚠️ 그룹 데이터 로드 스킵 (이미 로드 중이거나 최근에 로드함)');
            return;
        }
        this.loadMyGroups();
    },

    // 이벤트 리스너 설정
    setupEventListeners() {
        // 이미 설정된 경우 스킵
        if (this.eventListenersSetup) {
            console.log('⚠️ 이벤트 리스너는 이미 설정되었습니다. 스킵합니다.');
            return;
        }

        console.log('🔧 그룹 섹션 이벤트 리스너 설정');
        
        // 그룹 섹션 내부의 버튼들에만 이벤트 리스너 추가
        const groupSection = document.getElementById('group-section');
        if (!groupSection) {
            console.warn('⚠️ 그룹 섹션을 찾을 수 없습니다.');
            return;
        }

        // 이벤트 위임을 사용하여 그룹 섹션 내부의 클릭 이벤트 처리
        groupSection.addEventListener('click', (e) => {
            const createBtn = e.target.closest('[data-action="create-group"]');
            if (createBtn) {
                e.preventDefault();
                e.stopPropagation();
                console.log('✅ 그룹 생성 버튼 클릭됨');
                if (typeof this.showCreateGroupModal === 'function') {
                    this.showCreateGroupModal();
                } else {
                    console.error('❌ showCreateGroupModal 함수가 정의되지 않았습니다.');
                }
                return;
            }

            const refreshBtn = e.target.closest('[data-action="refresh-groups"]');
            if (refreshBtn) {
                e.preventDefault();
                e.stopPropagation();
                console.log('🔄 새로고침 버튼 클릭됨');
                if (typeof this.loadMyGroups === 'function') {
                    this.loadMyGroups();
                } else {
                    console.error('❌ loadMyGroups 함수가 정의되지 않았습니다.');
                }
                return;
            }
        });

        this.eventListenersSetup = true;
        console.log('✅ 이벤트 리스너 설정 완료');
    },

    // 내 그룹 목록 로드
    async loadMyGroups() {
        // 중복 호출 방지
        if (this.isLoading) {
            console.log('⚠️ 그룹 목록 로드 중이므로 스킵');
            return;
        }

        try {
            this.isLoading = true;
            this.lastLoadTime = Date.now();
            
            const token = localStorage.getItem('mufi_token');
            if (!token) {
                this.showNotification('로그인이 필요합니다.', 'error');
                return;
            }

            console.log('📥 내 그룹 목록 로드 중...');

            const response = await fetch('/api/groups', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.myGroups = data.data.groups || [];
                this.renderMyGroups();
                console.log(`✅ ${this.myGroups.length}개 그룹 로드 완료`);
            } else {
                throw new Error(data.detail || '그룹 목록을 불러오는데 실패했습니다.');
            }

        } catch (error) {
            console.error('❌ 그룹 목록 로드 오류:', error);
            this.showNotification(error.message || '그룹 목록을 불러오는데 실패했습니다.', 'error');
            
            // 에러 시 빈 배열로 설정
            this.myGroups = [];
            this.renderMyGroups();
        } finally {
            this.isLoading = false;
        }
    },

    // 내 그룹 렌더링
    renderMyGroups() {
        const container = document.getElementById('groupsContainer');

        if (this.myGroups.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-users fa-3x"></i>
                    <h3>아직 그룹이 없습니다</h3>
                    <p>새 그룹을 만들거나 초대를 받아보세요</p>
                    <button class="btn btn-primary" data-action="create-group">
                        <i class="fas fa-plus"></i> 첫 그룹 만들기
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = this.myGroups.map(group => this.createGroupCard(group)).join('');
    },

    // 그룹 카드 생성
    createGroupCard(group) {
        const roleClass = group.role || 'member';
        const roleText = {
            'owner': '소유자',
            'admin': '관리자',
            'member': '멤버'
        }[roleClass] || '멤버';

        const membersHtml = group.members.slice(0, 5).map(member => {
            if (member.picture) {
                return `<img src="${member.picture}" alt="${member.name}" class="member-avatar" title="${member.name}">`;
            }
            const initial = member.name.charAt(0);
            return `<div class="member-avatar-placeholder" title="${member.name}">${initial}</div>`;
        }).join('');

        const moreCount = group.member_count - 5;
        const moreHtml = moreCount > 0 ? `<div class="member-more">+${moreCount}</div>` : '';

        const createdDate = new Date(group.created_at).toLocaleDateString('ko-KR');

        return `
            <div class="group-card" data-group-id="${group.id}">
                <div class="group-card-header">
                    <div>
                        <h3 class="group-card-title">${group.group_name}</h3>
                        <span class="group-card-role ${roleClass}">${roleText}</span>
                    </div>
                </div>

                <div class="group-card-info">
                    <div class="group-card-info-item">
                        <i class="fas fa-users"></i>
                        <span>멤버 <strong>${group.member_count}명</strong></span>
                    </div>
                    <div class="group-card-info-item">
                        <i class="fas fa-calendar"></i>
                        <span>일정 <strong>${group.schedule_count}개</strong></span>
                    </div>
                </div>

                <div class="group-card-members">
                    <div class="group-card-members-title">멤버</div>
                    <div class="group-card-members-list">
                        ${membersHtml}
                        ${moreHtml}
                    </div>
                </div>

                <div class="group-card-actions">
                    <button class="btn btn-sm btn-outline-primary" onclick="window.groupSection.showMembersModal(${group.id})">
                        <i class="fas fa-users"></i> 멤버
                    </button>
                    ${roleClass !== 'member' ? `
                        <button class="btn btn-sm btn-outline-primary" onclick="window.groupSection.showInviteModal(${group.id})">
                            <i class="fas fa-user-plus"></i> 초대
                        </button>
                    ` : ''}
                    <button class="btn btn-sm btn-outline-primary" onclick="window.groupSection.showSchedulesModal(${group.id})">
                        <i class="fas fa-calendar-alt"></i> 일정
                    </button>
                    ${roleClass === 'owner' ? `
                        <button class="btn btn-sm btn-outline-danger" onclick="window.groupSection.showDeleteGroupModal(${group.id})" title="그룹 삭제">
                            <i class="fas fa-trash"></i> 삭제
                        </button>
                    ` : `
                        <button class="btn btn-sm btn-outline-danger" onclick="window.groupSection.showLeaveGroupModal(${group.id})" title="그룹 탈퇴">
                            <i class="fas fa-sign-out-alt"></i> 탈퇴
                        </button>
                    `}
                </div>
            </div>
        `;
    },


    // 그룹 생성 모달
    showCreateGroupModal() {
        console.log('📝 그룹 생성 모달 표시');
        
        // 기존 모달이 있으면 제거
        const existingModal = document.querySelector('.modal-overlay');
        if (existingModal) {
            existingModal.remove();
        }

        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.setAttribute('data-modal-type', 'create-group');
        
        // 모달 외부 클릭 시 닫기
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2 class="modal-title">새 그룹 만들기</h2>
                    <p class="modal-subtitle">팀원들과 일정을 공유할 그룹을 만드세요</p>
                </div>

                <div class="modal-body">
                    <div class="form-group">
                        <label>그룹 이름 <span style="color: #ef4444;">*</span></label>
                        <input type="text" id="groupName" placeholder="예: 마케팅팀, 프로젝트 A" maxlength="50">
                        <span class="helper-text">최대 50자</span>
                    </div>

                    <div class="form-group">
                        <label>그룹 설명</label>
                        <textarea id="groupDescription" placeholder="그룹에 대한 간단한 설명을 입력하세요 (선택)" rows="3"></textarea>
                    </div>
                </div>

                <div class="modal-actions">
                    <button class="btn btn-secondary" data-action="close-modal">
                        취소
                    </button>
                    <button class="btn btn-primary" data-action="submit-create-group">
                        <i class="fas fa-plus"></i> 생성
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // 모달 내부 버튼 이벤트 리스너
        const closeBtn = modal.querySelector('[data-action="close-modal"]');
        const submitBtn = modal.querySelector('[data-action="submit-create-group"]');

        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                modal.remove();
            });
        }

        if (submitBtn) {
            submitBtn.addEventListener('click', () => {
                this.createGroup();
            });
        }

        // 입력 필드에 포커스
        setTimeout(() => {
            const nameInput = modal.querySelector('#groupName');
            if (nameInput) {
                nameInput.focus();
            }
        }, 100);

        // ESC 키로 모달 닫기
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                modal.remove();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);

        // 모달이 제거될 때 이벤트 리스너도 제거
        const observer = new MutationObserver(() => {
            if (!document.body.contains(modal)) {
                document.removeEventListener('keydown', handleEscape);
                observer.disconnect();
            }
        });
        observer.observe(document.body, { childList: true });
    },

    // 그룹 생성
    async createGroup() {
        try {
            const groupNameInput = document.getElementById('groupName');
            const groupDescriptionInput = document.getElementById('groupDescription');
            
            if (!groupNameInput) {
                console.error('❌ 그룹 이름 입력 필드를 찾을 수 없습니다.');
                this.showNotification('오류가 발생했습니다. 페이지를 새로고침해주세요.', 'error');
                return;
            }

            const groupName = groupNameInput.value.trim();
            const groupDescription = groupDescriptionInput ? groupDescriptionInput.value.trim() : '';

            if (!groupName) {
                this.showNotification('그룹 이름을 입력해주세요.', 'error');
                groupNameInput.focus();
                return;
            }

            const token = localStorage.getItem('mufi_token');
            if (!token) {
                this.showNotification('로그인이 필요합니다.', 'error');
                // 모달 닫기
                const modal = document.querySelector('.modal-overlay[data-modal-type="create-group"]');
                if (modal) modal.remove();
                return;
            }

            console.log('📤 그룹 생성 요청:', { groupName, groupDescription });

            // 로딩 상태 표시
            const submitBtn = document.querySelector('[data-action="submit-create-group"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 생성 중...';
            }

            const response = await fetch('/api/groups', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    group_name: groupName, 
                    description: groupDescription || null 
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.showNotification('그룹이 생성되었습니다!', 'success');
                // 모달 닫기
                const modal = document.querySelector('.modal-overlay[data-modal-type="create-group"]');
                if (modal) modal.remove();
                // 그룹 목록 새로고침
                await this.loadMyGroups();
            } else {
                throw new Error(data.detail || '그룹 생성에 실패했습니다.');
            }

        } catch (error) {
            console.error('❌ 그룹 생성 오류:', error);
            this.showNotification(error.message || '그룹 생성에 실패했습니다.', 'error');
            
            // 버튼 상태 복원
            const submitBtn = document.querySelector('[data-action="submit-create-group"]');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-plus"></i> 생성';
            }
        }
    },

    // 초대 모달
    showInviteModal(groupId) {
        const group = this.myGroups.find(g => g.id === groupId);
        if (!group) return;

        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2 class="modal-title">그룹 초대</h2>
                    <p class="modal-subtitle">${group.group_name}에 멤버를 초대하세요</p>
                </div>

                <div class="modal-body">
                    <div class="form-group">
                        <label>초대 방식</label>
                        <div style="display: flex; gap: 0.5rem; margin-bottom: 1rem;">
                            <button class="btn btn-outline-primary" style="flex: 1;" onclick="window.groupSection.generateInviteLink(${groupId})">
                                🔗 초대 링크 생성
                            </button>
                        </div>
                    </div>

                    <div id="inviteLinkResult" style="display: none;">
                        <div class="invite-link-result">
                            <div class="invite-link-url">
                                <input type="text" id="inviteUrl" readonly>
                                <button class="btn btn-primary btn-sm" onclick="window.groupSection.copyInviteLink()">
                                    <i class="fas fa-copy"></i> 복사
                                </button>
                            </div>
                            <div class="invite-link-info">
                                <i class="fas fa-info-circle"></i>
                                <span id="expiresInfoText">이 링크는 7일 후 만료됩니다</span>
                            </div>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>만료 기간</label>
                        <select id="expiresIn">
                            <option value="1">1일</option>
                            <option value="3">3일</option>
                            <option value="7" selected>7일</option>
                            <option value="30">30일</option>
                        </select>
                    </div>
                </div>

                <div class="modal-actions">
                    <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">
                        닫기
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    },

    // 초대 링크 생성
    async generateInviteLink(groupId) {
        try {
            const token = localStorage.getItem('mufi_token');
            if (!token) {
                this.showNotification('로그인이 필요합니다.', 'error');
                return;
            }

            // 만료 기간 가져오기
            const expiresInSelect = document.getElementById('expiresIn');
            if (!expiresInSelect) {
                throw new Error('만료 기간 선택 요소를 찾을 수 없습니다.');
            }
            const expiresInDays = parseInt(expiresInSelect.value) || 7;

            console.log('🔗 초대 링크 생성 중...');
            console.log('📅 선택한 만료 기간:', expiresInDays, '일');
            console.log('📅 선택 요소 값:', expiresInSelect.value);

            const response = await fetch(`/api/groups/${groupId}/invite`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    expires_in_days: expiresInDays
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                const inviteUrl = data.data.invite_url;
                document.getElementById('inviteUrl').value = inviteUrl;
                document.getElementById('inviteLinkResult').style.display = 'block';
                
                // 만료 기간 안내 메시지 업데이트
                const infoTextElement = document.getElementById('expiresInfoText');
                if (infoTextElement) {
                    infoTextElement.textContent = `이 링크는 ${expiresInDays}일 후 만료됩니다`;
                }
                
                this.showNotification('초대 링크가 생성되었습니다!', 'success');
            } else {
                throw new Error(data.detail || '초대 링크 생성에 실패했습니다.');
            }

        } catch (error) {
            console.error('❌ 초대 링크 생성 오류:', error);
            this.showNotification(error.message || '초대 링크 생성에 실패했습니다.', 'error');
        }
    },

    // 초대 링크 복사
    copyInviteLink() {
        const input = document.getElementById('inviteUrl');
        input.select();
        document.execCommand('copy');
        this.showNotification('초대 링크가 복사되었습니다!', 'success');
    },


    // 멤버 모달
    showMembersModal(groupId) {
        const group = this.myGroups.find(g => g.id === groupId);
        if (!group) return;

        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 600px;">
                <div class="modal-header">
                    <h2 class="modal-title">멤버 관리</h2>
                    <p class="modal-subtitle">${group.group_name} (${group.member_count}명)</p>
                </div>

                <div class="modal-body">
                    <div class="members-list">
                        ${group.members.map(member => `
                            <div class="member-item">
                                <div class="member-info">
                                    ${member.picture ? 
                                        `<img src="${member.picture}" alt="${member.name}" class="member-avatar">` :
                                        `<div class="member-avatar-placeholder">${member.name.charAt(0)}</div>`
                                    }
                                    <div>
                                        <div class="member-name">${member.name}</div>
                                        <div class="member-email">${member.email}</div>
                                    </div>
                                </div>
                                <div class="member-actions">
                                    <span class="member-role-badge member">${member.role || '멤버'}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div class="modal-actions">
                    <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">
                        닫기
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    },

    // 일정 모달
    async showSchedulesModal(groupId) {
        const group = this.myGroups.find(g => g.id === groupId);
        if (!group) return;

        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.setAttribute('data-modal-type', 'group-schedules');
        modal.setAttribute('data-group-id', groupId);

        // 로딩 상태 표시
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 700px;">
                <div class="modal-header">
                    <h2 class="modal-title">그룹 일정</h2>
                    <p class="modal-subtitle">${group.group_name}의 공유 일정</p>
                </div>

                <div class="modal-body">
                    <div class="group-schedules" id="groupSchedulesList">
                        <div style="text-align: center; padding: 2rem;">
                            <div class="loading-spinner" style="width: 40px; height: 40px; border: 3px solid #e2e8f0; border-top-color: #1e293b; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto;"></div>
                            <p style="margin-top: 1rem; color: #64748b;">일정을 불러오는 중...</p>
                        </div>
                    </div>
                </div>

                <div class="modal-actions">
                    <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">
                        닫기
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // 그룹 일정 로드
        await this.loadGroupSchedules(groupId, modal);

        // 모달 외부 클릭 시 닫기
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    },

    // 그룹 일정 로드
    async loadGroupSchedules(groupId, modal) {
        try {
            const token = localStorage.getItem('mufi_token');
            if (!token) {
                const listContainer = modal.querySelector('#groupSchedulesList');
                listContainer.innerHTML = `
                    <div class="empty-state" style="padding: 2rem;">
                        <i class="fas fa-exclamation-circle fa-2x"></i>
                        <p style="margin-top: 1rem;">로그인이 필요합니다.</p>
                    </div>
                `;
                return;
            }

            console.log(`📥 그룹 일정 로드 시작: groupId=${groupId}`);
            const response = await fetch(`/api/groups/${groupId}/schedules`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            console.log(`📥 응답 상태: ${response.status}`);

            const listContainer = modal.querySelector('#groupSchedulesList');

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    const schedules = data.data?.schedules || [];
                    console.log(`✅ ${schedules.length}개 일정 로드 완료`);
                    this.renderGroupSchedules(schedules, listContainer);
                } else {
                    console.error('❌ API 응답 실패:', data);
                    this.renderGroupSchedules([], listContainer);
                }
            } else if (response.status === 404) {
                // 404 오류인 경우 빈 상태로 표시
                console.log('⚠️ 그룹 일정 없음 (404) - 빈 상태 표시');
                this.renderGroupSchedules([], listContainer);
            } else {
                // 다른 오류인 경우 에러 메시지 표시
                const data = await response.json().catch(() => ({ detail: '일정을 불러오는데 실패했습니다.' }));
                console.error(`❌ 그룹 일정 로드 오류 (${response.status}):`, data);
                listContainer.innerHTML = `
                    <div class="empty-state" style="padding: 2rem; text-align: center;">
                        <i class="fas fa-exclamation-circle fa-2x" style="color: #94a3b8; margin-bottom: 1rem;"></i>
                        <p style="margin-top: 1rem; color: #64748b;">${data.detail || '일정을 불러오는데 실패했습니다.'}</p>
                    </div>
                `;
            }

        } catch (error) {
            console.error('❌ 그룹 일정 로드 오류:', error);
            const listContainer = modal.querySelector('#groupSchedulesList');
            listContainer.innerHTML = `
                <div class="empty-state" style="padding: 2rem;">
                    <i class="fas fa-exclamation-circle fa-2x"></i>
                    <p style="margin-top: 1rem;">일정을 불러오는데 실패했습니다.</p>
                </div>
            `;
        }
    },

    // 그룹 일정 렌더링
    renderGroupSchedules(schedules, container) {
        if (schedules.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="padding: 4rem 2rem; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px;">
                    <i class="fas fa-calendar-plus" style="font-size: 4rem; color: #cbd5e1; margin-bottom: 1.5rem; opacity: 0.5;"></i>
                    <h3 style="font-size: 1.35rem; font-weight: 700; color: #1e293b; margin: 0 0 0.75rem 0;">공유된 일정이 없습니다</h3>
                    <p style="font-size: 1rem; color: #64748b; margin: 0; line-height: 1.6; max-width: 400px;">분석 결과에서 일정을 그룹에 공유할 수 있습니다</p>
                </div>
            `;
            return;
        }

        container.innerHTML = schedules.map(schedule => {
            const startDate = new Date(schedule.start_datetime);
            const endDate = new Date(schedule.end_datetime);
            const formattedDateTime = `${startDate.toLocaleDateString('ko-KR')} ${startDate.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })} - ${endDate.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}`;

            return `
                <div class="schedule-item" data-schedule-id="${schedule.id}" data-group-schedule-id="${schedule.group_schedule_id}">
                    <div class="schedule-item-content">
                        <div class="schedule-item-title">${schedule.title || '제목 없음'}</div>
                        <div class="schedule-item-time">
                            <i class="fas fa-calendar"></i>
                            ${formattedDateTime}
                        </div>
                        ${schedule.location ? `
                            <div class="schedule-item-location" style="margin-top: 0.5rem; color: #64748b; font-size: 0.9rem;">
                                <i class="fas fa-map-marker-alt"></i> ${schedule.location}
                            </div>
                        ` : ''}
                        ${schedule.shared_by ? `
                            <div class="schedule-item-shared-by" style="margin-top: 0.5rem; font-size: 0.85rem; color: #94a3b8;">
                                <i class="fas fa-user"></i> ${schedule.shared_by.name}님이 공유함
                            </div>
                        ` : ''}
                    </div>
                    <div class="schedule-item-actions">
                        <button class="btn btn-sm btn-outline-success" onclick="window.groupSection.addToCalendarFromGroup('${schedule.id}')" title="캘린더에 추가">
                            <i class="fas fa-calendar-plus"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-info" onclick="window.groupSection.sendEmailFromGroup('${schedule.id}')" title="메일 보내기">
                            <i class="fas fa-envelope"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="window.groupSection.removeScheduleFromGroup('${schedule.group_schedule_id}')" title="그룹에서 삭제">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        // CSS 애니메이션 추가
        if (!document.getElementById('group-schedules-style')) {
            const style = document.createElement('style');
            style.id = 'group-schedules-style';
            style.textContent = `
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
                .schedule-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 1rem;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    margin-bottom: 0.75rem;
                    transition: all 0.2s;
                }
                .schedule-item:hover {
                    border-color: #2563eb;
                    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
                }
                .schedule-item-content {
                    flex: 1;
                }
                .schedule-item-actions {
                    display: flex;
                    gap: 0.5rem;
                }
            `;
            document.head.appendChild(style);
        }
    },

    // 그룹에서 일정 제거
    async removeScheduleFromGroup(groupScheduleId) {
        if (!confirm('그룹에서 이 일정을 제거하시겠습니까?')) {
            return;
        }

        try {
            const token = localStorage.getItem('mufi_token');
            if (!token) {
                this.showNotification('로그인이 필요합니다.', 'error');
                return;
            }

            const response = await fetch(`/api/groups/schedules/${groupScheduleId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.showNotification('그룹에서 일정이 제거되었습니다.', 'success');
                
                // 모달에서 일정 제거
                const scheduleItem = document.querySelector(`[data-group-schedule-id="${groupScheduleId}"]`);
                if (scheduleItem) {
                    scheduleItem.remove();
                    
                    // 일정이 없으면 빈 상태 표시
                    const modal = document.querySelector('[data-modal-type="group-schedules"]');
                    if (modal) {
                        const listContainer = modal.querySelector('#groupSchedulesList');
                        const remainingItems = listContainer.querySelectorAll('.schedule-item');
                        if (remainingItems.length === 0) {
                            this.renderGroupSchedules([], listContainer);
                        }
                    }
                }
            } else {
                throw new Error(data.detail || '일정 제거에 실패했습니다.');
            }

        } catch (error) {
            console.error('❌ 그룹 일정 제거 오류:', error);
            this.showNotification(error.message || '일정 제거에 실패했습니다.', 'error');
        }
    },

    // 그룹 일정에서 캘린더 추가
    async addToCalendarFromGroup(scheduleId) {
        // schedules.js의 addToCalendar 함수 사용
        if (window.schedulesSection && typeof window.schedulesSection.addToCalendar === 'function') {
            await window.schedulesSection.addToCalendar(scheduleId);
        } else {
            this.showNotification('캘린더 추가 기능을 사용할 수 없습니다.', 'error');
        }
    },

    // 그룹 일정에서 이메일 보내기
    async sendEmailFromGroup(scheduleId) {
        // schedules.js의 sendEmail 함수 사용
        if (window.schedulesSection && typeof window.schedulesSection.sendEmail === 'function') {
            await window.schedulesSection.sendEmail(scheduleId);
        } else {
            this.showNotification('이메일 전송 기능을 사용할 수 없습니다.', 'error');
        }
    },


    // 알림 표시
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#2563eb'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 9999;
            animation: slideIn 0.3s;
        `;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    },

    // 그룹 탈퇴 모달 표시
    showLeaveGroupModal(groupId) {
        const group = this.myGroups.find(g => g.id === groupId);
        if (!group) return;

        if (!confirm(`정말로 "${group.group_name}" 그룹에서 탈퇴하시겠습니까?\n\n탈퇴 후에는 다시 초대를 받아야 그룹에 참여할 수 있습니다.`)) {
            return;
        }

        this.leaveGroup(groupId);
    },

    // 그룹 탈퇴
    async leaveGroup(groupId) {
        try {
            const token = localStorage.getItem('mufi_token');
            if (!token) {
                this.showNotification('로그인이 필요합니다.', 'error');
                return;
            }

            const response = await fetch(`/api/groups/${groupId}/leave`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.showNotification(data.message || '그룹에서 탈퇴했습니다.', 'success');
                // 그룹 목록 새로고침
                await this.loadMyGroups();
            } else {
                throw new Error(data.detail || '그룹 탈퇴에 실패했습니다.');
            }

        } catch (error) {
            console.error('❌ 그룹 탈퇴 오류:', error);
            this.showNotification(error.message || '그룹 탈퇴 중 오류가 발생했습니다.', 'error');
        }
    },

    // 그룹 삭제 모달 표시
    showDeleteGroupModal(groupId) {
        const group = this.myGroups.find(g => g.id === groupId);
        if (!group) return;

        if (!confirm(`정말로 "${group.group_name}" 그룹을 삭제하시겠습니까?\n\n삭제된 그룹은 복구할 수 없으며, 모든 멤버와 일정이 함께 삭제됩니다.`)) {
            return;
        }

        this.deleteGroup(groupId);
    },

    // 그룹 삭제
    async deleteGroup(groupId) {
        try {
            const token = localStorage.getItem('mufi_token');
            if (!token) {
                this.showNotification('로그인이 필요합니다.', 'error');
                return;
            }

            const response = await fetch(`/api/groups/${groupId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.showNotification(data.message || '그룹이 삭제되었습니다.', 'success');
                // 그룹 목록 새로고침
                await this.loadMyGroups();
            } else {
                throw new Error(data.detail || '그룹 삭제에 실패했습니다.');
            }

        } catch (error) {
            console.error('❌ 그룹 삭제 오류:', error);
            this.showNotification(error.message || '그룹 삭제 중 오류가 발생했습니다.', 'error');
        }
    }
};

// 그룹 섹션 초기화 함수 (이벤트 리스너만 설정, 데이터는 로드하지 않음)
function initGroupSection() {
    console.log('🔧 initGroupSection 호출됨');
    const groupSection = document.getElementById('group-section');
    
    if (groupSection && window.groupSection) {
        console.log('✅ 그룹 섹션 초기화 시작 (이벤트 리스너만 설정)');
        try {
            // init()은 이벤트 리스너만 설정하고, 데이터는 로드하지 않음
            window.groupSection.init();
            console.log('✅ 그룹 섹션 초기화 완료');
        } catch (error) {
            console.error('❌ 그룹 섹션 초기화 오류:', error);
        }
    } else {
        console.warn('⚠️ 그룹 섹션 또는 window.groupSection이 없습니다.');
        if (!groupSection) {
            console.warn('⚠️ #group-section 요소를 찾을 수 없습니다.');
        }
        if (!window.groupSection) {
            console.warn('⚠️ window.groupSection이 정의되지 않았습니다.');
        }
    }
}

// DOM 로드 상태에 따라 초기화 (이벤트 리스너만 설정, 데이터는 로드하지 않음)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('📄 DOMContentLoaded - 그룹 섹션 초기화 시도');
        initGroupSection();
    });
} else {
    // DOM이 이미 로드된 경우 즉시 실행
    console.log('📄 DOM 이미 로드됨 - 그룹 섹션 초기화 시도');
    initGroupSection();
}

// 인증 완료 이벤트 리스너 (이벤트 리스너만 설정)
document.addEventListener('mufi-auth-completed', () => {
    console.log('🎉 인증 완료 이벤트 수신 - 그룹 섹션 초기화');
    setTimeout(() => {
        initGroupSection();
        // 현재 활성화된 섹션이 그룹이면 데이터 로드
        const groupSection = document.getElementById('group-section');
        if (groupSection && groupSection.classList.contains('active') && window.groupSection) {
            window.groupSection.loadData();
        }
    }, 100);
});

