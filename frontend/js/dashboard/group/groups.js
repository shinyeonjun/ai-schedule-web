// 그룹 관리 섹션
window.groupSection = {
    myGroups: [],

    // 초기화
    init() {
        console.log('🔧 그룹 섹션 초기화');
        this.loadMyGroups();
    },

    // 내 그룹 목록 로드
    async loadMyGroups() {
        try {
            const token = localStorage.getItem('mufi_token');
            if (!token) {
                this.showNotification('로그인이 필요합니다.', 'error');
                return;
            }

            console.log('📥 내 그룹 목록 로드 중...');

            // TODO: API 연동
            // const response = await fetch('/api/groups', {
            //     headers: { 'Authorization': `Bearer ${token}` }
            // });
            // const data = await response.json();
            // this.myGroups = data.data.groups || [];

            // 임시 데모 데이터
            this.myGroups = [
                {
                    id: 1,
                    group_name: '마케팅팀',
                    admin_id: 1,
                    role: 'owner',
                    member_count: 5,
                    schedule_count: 12,
                    created_at: '2025-01-15T10:00:00',
                    members: [
                        { id: 1, name: '김철수', email: 'kim@test.com', picture: null },
                        { id: 2, name: '이영희', email: 'lee@test.com', picture: null },
                        { id: 3, name: '박민수', email: 'park@test.com', picture: null }
                    ]
                },
                {
                    id: 2,
                    group_name: '개발팀',
                    admin_id: 2,
                    role: 'admin',
                    member_count: 8,
                    schedule_count: 24,
                    created_at: '2025-01-10T14:30:00',
                    members: [
                        { id: 4, name: '최지원', email: 'choi@test.com', picture: null },
                        { id: 5, name: '정수현', email: 'jung@test.com', picture: null }
                    ]
                },
                {
                    id: 3,
                    group_name: '프로젝트 A',
                    admin_id: 3,
                    role: 'member',
                    member_count: 3,
                    schedule_count: 8,
                    created_at: '2025-01-20T09:15:00',
                    members: [
                        { id: 6, name: '강민아', email: 'kang@test.com', picture: null }
                    ]
                }
            ];

            this.renderMyGroups();
        } catch (error) {
            console.error('❌ 그룹 목록 로드 오류:', error);
            this.showNotification('그룹 목록을 불러오는데 실패했습니다.', 'error');
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
                    <button class="btn btn-primary" onclick="window.groupSection.showCreateGroupModal()">
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
                </div>
            </div>
        `;
    },


    // 그룹 생성 모달
    showCreateGroupModal() {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
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
                    <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">
                        취소
                    </button>
                    <button class="btn btn-primary" onclick="window.groupSection.createGroup()">
                        <i class="fas fa-plus"></i> 생성
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    },

    // 그룹 생성
    async createGroup() {
        try {
            const groupName = document.getElementById('groupName').value.trim();
            const groupDescription = document.getElementById('groupDescription').value.trim();

            if (!groupName) {
                this.showNotification('그룹 이름을 입력해주세요.', 'error');
                return;
            }

            const token = localStorage.getItem('mufi_token');
            if (!token) {
                this.showNotification('로그인이 필요합니다.', 'error');
                return;
            }

            console.log('📤 그룹 생성 요청:', { groupName, groupDescription });

            // TODO: API 연동
            // const response = await fetch('/api/groups', {
            //     method: 'POST',
            //     headers: {
            //         'Authorization': `Bearer ${token}`,
            //         'Content-Type': 'application/json'
            //     },
            //     body: JSON.stringify({ group_name: groupName, description: groupDescription })
            // });

            // if (!response.ok) throw new Error('그룹 생성 실패');

            this.showNotification('그룹이 생성되었습니다!', 'success');
            document.querySelector('.modal-overlay').remove();
            this.loadMyGroups();

        } catch (error) {
            console.error('❌ 그룹 생성 오류:', error);
            this.showNotification('그룹 생성에 실패했습니다.', 'error');
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
                            <div class="invite-link-actions">
                                <button class="btn btn-secondary btn-sm" onclick="window.groupSection.shareKakao()">
                                    💬 카카오톡
                                </button>
                                <button class="btn btn-secondary btn-sm" onclick="window.groupSection.shareEmail()">
                                    ✉️ 이메일
                                </button>
                            </div>
                            <div class="invite-link-info">
                                <i class="fas fa-info-circle"></i>
                                이 링크는 7일 후 만료됩니다
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
            const expiresIn = document.getElementById('expiresIn').value;

            console.log('🔗 초대 링크 생성 중...');

            // TODO: API 연동
            // const response = await fetch(`/api/groups/${groupId}/invite`, {
            //     method: 'POST',
            //     headers: {
            //         'Authorization': `Bearer ${token}`,
            //         'Content-Type': 'application/json'
            //     },
            //     body: JSON.stringify({ expires_in_days: parseInt(expiresIn) })
            // });

            // const data = await response.json();
            // const inviteUrl = data.data.invite_url;

            // 임시 데모 데이터
            const inviteToken = 'demo-' + Math.random().toString(36).substr(2, 9);
            const inviteUrl = `${window.location.origin}/invite/${inviteToken}`;

            document.getElementById('inviteUrl').value = inviteUrl;
            document.getElementById('inviteLinkResult').style.display = 'block';

            this.showNotification('초대 링크가 생성되었습니다!', 'success');

        } catch (error) {
            console.error('❌ 초대 링크 생성 오류:', error);
            this.showNotification('초대 링크 생성에 실패했습니다.', 'error');
        }
    },

    // 초대 링크 복사
    copyInviteLink() {
        const input = document.getElementById('inviteUrl');
        input.select();
        document.execCommand('copy');
        this.showNotification('초대 링크가 복사되었습니다!', 'success');
    },

    // 카카오톡 공유
    shareKakao() {
        this.showNotification('카카오톡 공유 기능은 준비 중입니다.', 'info');
    },

    // 이메일 공유
    shareEmail() {
        const inviteUrl = document.getElementById('inviteUrl').value;
        const subject = 'SULLIVAN 그룹 초대';
        const body = `안녕하세요!\n\n그룹에 초대합니다. 아래 링크를 클릭하여 가입해주세요.\n\n${inviteUrl}`;
        window.location.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
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
    showSchedulesModal(groupId) {
        const group = this.myGroups.find(g => g.id === groupId);
        if (!group) return;

        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 700px;">
                <div class="modal-header">
                    <h2 class="modal-title">그룹 일정</h2>
                    <p class="modal-subtitle">${group.group_name}의 공유 일정</p>
                </div>

                <div class="modal-body">
                    <div class="group-schedules">
                        <div class="schedule-item">
                            <div class="schedule-item-title">주간 회의</div>
                            <div class="schedule-item-time">
                                <i class="fas fa-calendar"></i>
                                2025-01-29 10:00 - 11:00
                            </div>
                        </div>
                        <div class="schedule-item">
                            <div class="schedule-item-title">프로젝트 킥오프</div>
                            <div class="schedule-item-time">
                                <i class="fas fa-calendar"></i>
                                2025-02-01 14:00 - 16:00
                            </div>
                        </div>
                        <div class="empty-state" style="padding: 2rem;">
                            <i class="fas fa-calendar-plus fa-2x"></i>
                            <p style="margin-top: 1rem;">분석 결과에서 일정을 그룹에 공유할 수 있습니다</p>
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
    }
};

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('group-section')) {
        window.groupSection.init();
    }
});

