

class MembersSection {
    constructor() {
        this.users = [];
        this.contacts = [];
        this.currentTab = 'mufi-users';
        this.init();
    }

    // 초기화
    init() {
        console.log('👥 인원 관리 섹션 초기화');
        this.setupEventListeners();
        this.loadMufiUsers();
    }

    // 이벤트 리스너 설정
    setupEventListeners() {
        // 탭 버튼 이벤트
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // 외부 인원 추가 버튼
        const addContactBtn = document.getElementById('addContactBtn');
        if (addContactBtn) {
            addContactBtn.addEventListener('click', () => {
                this.showAddContactModal();
            });
        }
    }

    // 탭 전환
    switchTab(tabName) {
        // 탭 버튼 활성화 상태 변경
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            button.classList.remove('active');
            if (button.dataset.tab === tabName) {
                button.classList.add('active');
            }
        });

        // 탭 콘텐츠 전환
        const tabContents = document.querySelectorAll('.tab-content');
        tabContents.forEach(content => {
            content.classList.remove('active');
            if (content.id === `${tabName}-tab`) {
                content.classList.add('active');
            }
        });

        this.currentTab = tabName;

        // 탭에 따른 데이터 로드
        if (tabName === 'mufi-users') {
            this.loadMufiUsers();
        } else if (tabName === 'external-contacts') {
            this.loadExternalContacts();
        }
    }

    // MUFI 사용자 목록 로드
    async loadMufiUsers() {
        try {
            const token = localStorage.getItem('mufi_token');
            if (!token) {
                this.showNotification('로그인이 필요합니다.', 'error');
                return;
            }

            // 로딩 오버레이 표시
            if (window.dashboard && window.dashboard.showLoadingOverlay) {
                window.dashboard.showLoadingOverlay('사용자 목록을 불러오는 중...');
            }

            const response = await fetch('/api/members/mufi-users', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            const result = await response.json();
            
            if (response.ok) {
                this.users = result.data.users || [];
                console.log('📊 받아온 사용자 데이터:', this.users);
                this.displayMufiUsers();
                this.showNotification(result.message, 'success');
            } else {
                this.showNotification(result.detail || '사용자 목록을 불러오는데 실패했습니다.', 'error');
                this.showEmptyState('members');
            }
        } catch (error) {
            console.error('❌ SULLIVAN 사용자 로드 오류:', error);
            this.showNotification('사용자 목록을 불러오는데 실패했습니다.', 'error');
            this.showEmptyState('members');
        } finally {
            // 로딩 오버레이 숨기기
            if (window.dashboard && window.dashboard.hideLoadingOverlay) {
                window.dashboard.hideLoadingOverlay();
            }
        }
    }

    // 외부 인원 목록 로드
    async loadExternalContacts() {
        try {
            const token = localStorage.getItem('mufi_token');
            if (!token) {
                this.showNotification('로그인이 필요합니다.', 'error');
                return;
            }

            // 로딩 오버레이 표시
            if (window.dashboard && window.dashboard.showLoadingOverlay) {
                window.dashboard.showLoadingOverlay('외부 인원 목록을 불러오는 중...');
            }

            const response = await fetch('/api/members/external-contacts', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            const result = await response.json();
            
            if (response.ok) {
                this.contacts = result.data.contacts || [];
                this.displayExternalContacts();
                this.showNotification(result.message, 'success');
            } else {
                this.showNotification(result.detail || '외부 인원 목록을 불러오는데 실패했습니다.', 'error');
                this.showEmptyState('contacts');
            }
        } catch (error) {
            console.error('❌ 외부 인원 로드 오류:', error);
            this.showNotification('외부 인원 목록을 불러오는데 실패했습니다.', 'error');
            this.showEmptyState('contacts');
        } finally {
            // 로딩 오버레이 숨기기
            if (window.dashboard && window.dashboard.hideLoadingOverlay) {
                window.dashboard.hideLoadingOverlay();
            }
        }
    }

    // MUFI 사용자 목록 표시
    displayMufiUsers() {
        const container = document.getElementById('usersGrid');
        const loading = document.getElementById('membersLoading');
        const empty = document.getElementById('emptyPlaceholder');

        if (!container) return;

        // 로딩 숨기기
        if (loading) loading.style.display = 'none';

        if (this.users.length === 0) {
            // 빈 상태 표시
            if (empty) empty.style.display = 'block';
            if (container) container.style.display = 'none';
            return;
        }

        // 빈 상태 숨기기
        if (empty) empty.style.display = 'none';
        if (container) container.style.display = 'grid';

        const usersHTML = this.users.map(user => {
            console.log('👤 사용자 데이터:', user);
            const createdAt = new Date(user.created_at);
            const formattedDate = createdAt.toLocaleDateString('ko-KR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });

            return `
                <div class="user-card" data-user-id="${user.id}">
                    <div class="user-header">
                        <div class="user-avatar">
                            ${user.picture ? 
                                `<img src="${user.picture}" alt="${user.name || user.email}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">` : 
                                ''
                            }
                            <i class="fas fa-user" style="${user.picture ? 'display: none;' : 'display: flex;'}"></i>
                        </div>
                                                 <div class="user-info">
                             <h3 class="user-name">${user.name || user.email.split('@')[0] || '닉네임 없음'}</h3>
                             <p class="user-email">${user.email}</p>
                         </div>
                        <div class="user-status">
                            <span class="status-badge active">SULLIVAN 사용자</span>
                        </div>
                    </div>
                    
                    <div class="user-details">
                        <div class="detail-item">
                            <span class="label">가입일:</span>
                            <span class="value">${formattedDate}</span>
                        </div>
                    </div>
                    
                                         <div class="user-actions">
                         <button class="btn btn-sm btn-outline-primary" onclick="window.membersSection.viewUserDetails('${user.id}')" title="상세보기">
                             <i class="fas fa-eye"></i>
                         </button>
                     </div>
                </div>
            `;
        }).join('');

        container.innerHTML = usersHTML;
    }

    // 외부 인원 목록 표시
    displayExternalContacts() {
        const container = document.getElementById('contactsGrid');
        const loading = document.getElementById('contactsLoading');
        const empty = document.getElementById('contactsEmptyPlaceholder');

        if (!container) return;

        // 로딩 숨기기
        if (loading) loading.style.display = 'none';

        if (this.contacts.length === 0) {
            // 빈 상태 표시
            if (empty) empty.style.display = 'block';
            if (container) container.style.display = 'none';
            return;
        }

        // 빈 상태 숨기기
        if (empty) empty.style.display = 'none';
        if (container) container.style.display = 'grid';

        const contactsHTML = this.contacts.map(contact => {
            const createdAt = new Date(contact.created_at);
            const formattedDate = createdAt.toLocaleDateString('ko-KR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });

            return `
                <div class="contact-card" data-contact-id="${contact.id}">
                    <div class="contact-header">
                        <div class="contact-avatar">
                            ${contact.picture ? 
                                `<img src="${contact.picture}" alt="${contact.name || contact.email}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">` : 
                                ''
                            }
                            <i class="fas fa-user-tie" style="${contact.picture ? 'display: none;' : 'display: flex;'}"></i>
                        </div>
                                                 <div class="contact-info">
                             <h3 class="contact-name">${contact.name || contact.email.split('@')[0] || '닉네임 없음'}</h3>
                             <p class="contact-email">${contact.email}</p>
                         </div>
                        <div class="contact-status">
                            <span class="status-badge active">외부 인원</span>
                        </div>
                    </div>
                    
                    <div class="contact-details">
                        ${contact.relationship ? `
                            <div class="detail-item">
                                <span class="label">관계:</span>
                                <span class="value">${contact.relationship}</span>
                            </div>
                        ` : ''}
                        <div class="detail-item">
                            <span class="label">등록일:</span>
                            <span class="value">${formattedDate}</span>
                        </div>
                    </div>
                    
                                         <div class="contact-actions">
                         <button class="btn btn-sm btn-outline-primary" onclick="window.membersSection.viewContactDetails('${contact.id}')" title="상세보기">
                             <i class="fas fa-eye"></i>
                         </button>
                     </div>
                </div>
            `;
        }).join('');

        container.innerHTML = contactsHTML;
    }

    // 사용자 상세보기
    viewUserDetails(userId) {
        const user = this.users.find(u => u.id == userId);
        if (user) {
            this.showNotification(`${user.email} 사용자 상세보기 기능은 준비 중입니다.`, 'info');
        }
    }

    // 사용자 편집
    editUser(userId) {
        const user = this.users.find(u => u.id == userId);
        if (user) {
            this.showNotification(`${user.email} 사용자 편집 기능은 준비 중입니다.`, 'info');
        }
    }

    // 사용자 삭제
    async deleteUser(userId) {
        const user = this.users.find(u => u.id == userId);
        if (!user) return;

        if (!confirm(`정말로 ${user.email} 사용자를 삭제하시겠습니까?`)) {
            return;
        }

        try {
            const token = localStorage.getItem('mufi_token');
            if (!token) {
                this.showNotification('로그인이 필요합니다.', 'error');
                return;
            }

            const response = await fetch(`/api/members/user/${userId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            const result = await response.json();
            
            if (response.ok) {
                this.showNotification('사용자가 성공적으로 삭제되었습니다.', 'success');
                this.loadMufiUsers(); // 목록 새로고침
            } else {
                this.showNotification(result.detail || '사용자 삭제에 실패했습니다.', 'error');
            }
        } catch (error) {
            console.error('❌ 사용자 삭제 오류:', error);
            this.showNotification('사용자 삭제 중 오류가 발생했습니다.', 'error');
        }
    }

    // 외부 인원 상세보기
    viewContactDetails(contactId) {
        const contact = this.contacts.find(c => c.id == contactId);
        if (contact) {
            this.showNotification(`${contact.name} 외부 인원 상세보기 기능은 준비 중입니다.`, 'info');
        }
    }

    // 외부 인원 편집
    editContact(contactId) {
        const contact = this.contacts.find(c => c.id == contactId);
        if (contact) {
            this.showNotification(`${contact.name} 외부 인원 편집 기능은 준비 중입니다.`, 'info');
        }
    }

    // 외부 인원 삭제
    async deleteContact(contactId) {
        const contact = this.contacts.find(c => c.id == contactId);
        if (!contact) return;

        if (!confirm(`정말로 ${contact.name} 외부 인원을 삭제하시겠습니까?`)) {
            return;
        }

        try {
            const token = localStorage.getItem('mufi_token');
            if (!token) {
                this.showNotification('로그인이 필요합니다.', 'error');
                return;
            }

            const response = await fetch(`/api/members/contact/${contactId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            const result = await response.json();
            
            if (response.ok) {
                this.showNotification('외부 인원이 성공적으로 삭제되었습니다.', 'success');
                this.loadExternalContacts(); // 목록 새로고침
            } else {
                this.showNotification(result.detail || '외부 인원 삭제에 실패했습니다.', 'error');
            }
        } catch (error) {
            console.error('❌ 외부 인원 삭제 오류:', error);
            this.showNotification('외부 인원 삭제 중 오류가 발생했습니다.', 'error');
        }
    }

    // 외부 인원 추가 모달 표시
    showAddContactModal() {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.setAttribute('data-modal-type', 'add-contact');

        modal.innerHTML = `
            <div class="modal-content" style="max-width: 500px;">
                <div class="modal-header">
                    <h2 class="modal-title">외부 인원 추가</h2>
                    <p class="modal-subtitle">새로운 외부 인원 정보를 입력하세요</p>
                </div>

                <div class="modal-body">
                    <form id="addContactForm">
                        <div class="form-group">
                            <label for="contactName">이름 <span style="color: #ef4444;">*</span></label>
                            <input type="text" id="contactName" name="name" required 
                                   placeholder="이름을 입력하세요" 
                                   style="width: 100%; padding: 0.75rem; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 0.95rem;">
                        </div>

                        <div class="form-group" style="margin-top: 1rem;">
                            <label for="contactEmail">이메일 <span style="color: #ef4444;">*</span></label>
                            <input type="email" id="contactEmail" name="email" required 
                                   placeholder="이메일을 입력하세요" 
                                   style="width: 100%; padding: 0.75rem; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 0.95rem;">
                        </div>

                        <div class="form-group" style="margin-top: 1rem;">
                            <label for="contactRelationship">관계</label>
                            <input type="text" id="contactRelationship" name="relationship" 
                                   placeholder="예: 친구, 부장, 동료 등 (선택사항)" 
                                   style="width: 100%; padding: 0.75rem; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 0.95rem;">
                        </div>
                    </form>
                </div>

                <div class="modal-actions">
                    <button class="btn btn-secondary" data-action="close-add-contact-modal">
                        취소
                    </button>
                    <button class="btn btn-primary" data-action="submit-add-contact">
                        <i class="fas fa-plus"></i> 추가하기
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // 모달 닫기 이벤트 리스너
        modal.querySelector('[data-action="close-add-contact-modal"]').addEventListener('click', () => modal.remove());
        modal.querySelector('[data-action="submit-add-contact"]').addEventListener('click', () => this.submitAddContact(modal));
        
        // 모달 외부 클릭 시 닫기
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
        
        // ESC 키로 닫기
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && document.body.contains(modal)) modal.remove();
        }, { once: true });

        // 첫 번째 입력 필드에 포커스
        setTimeout(() => {
            const firstInput = modal.querySelector('#contactName');
            if (firstInput) firstInput.focus();
        }, 100);
    }

    // 외부 인원 추가 제출
    async submitAddContact(modal) {
        const form = modal.querySelector('#addContactForm');
        if (!form) return;

        const formData = new FormData(form);
        const contactData = {
            name: formData.get('name')?.trim() || '',
            email: formData.get('email')?.trim() || '',
            relationship: formData.get('relationship')?.trim() || null
        };

        // 필수 필드 검증
        if (!contactData.name) {
            this.showNotification('이름을 입력해주세요.', 'error');
            return;
        }

        if (!contactData.email) {
            this.showNotification('이메일을 입력해주세요.', 'error');
            return;
        }

        // 이메일 형식 검증
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(contactData.email)) {
            this.showNotification('올바른 이메일 형식을 입력해주세요.', 'error');
            return;
        }

        try {
            const token = localStorage.getItem('mufi_token');
            if (!token) {
                this.showNotification('로그인이 필요합니다.', 'error');
                return;
            }

            // 빈 값 제거
            Object.keys(contactData).forEach(key => {
                if (contactData[key] === '' || contactData[key] === null) {
                    delete contactData[key];
                }
            });

            const response = await fetch('/api/members/external-contacts', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(contactData)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.showNotification(result.message || '외부 인원이 성공적으로 추가되었습니다.', 'success');
                modal.remove();
                // 외부 인원 목록 새로고침
                this.loadExternalContacts();
            } else {
                throw new Error(result.detail || '외부 인원 추가에 실패했습니다.');
            }

        } catch (error) {
            console.error('❌ 외부 인원 추가 오류:', error);
            this.showNotification(error.message || '외부 인원 추가 중 오류가 발생했습니다.', 'error');
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

    // 로딩 상태 표시
    showLoading(type) {
        const loading = document.getElementById(`${type}Loading`);
        const container = document.getElementById(`${type === 'members' ? 'users' : 'contacts'}Grid`);
        const empty = document.getElementById(`${type === 'members' ? 'empty' : 'contactsEmpty'}Placeholder`);

        if (loading) loading.style.display = 'flex';
        if (container) container.style.display = 'none';
        if (empty) empty.style.display = 'none';
    }

    // 빈 상태 표시
    showEmptyState(type) {
        const loading = document.getElementById(`${type}Loading`);
        const container = document.getElementById(`${type === 'members' ? 'users' : 'contacts'}Grid`);
        const empty = document.getElementById(`${type === 'members' ? 'empty' : 'contactsEmpty'}Placeholder`);

        if (loading) loading.style.display = 'none';
        if (container) container.style.display = 'none';
        if (empty) empty.style.display = 'block';
    }

    // 로딩 상태 해제
    hideLoading(type) {
        const loading = document.getElementById(`${type}Loading`);
        if (loading) loading.style.display = 'none';
    }
}

// 전역 객체로 등록
window.membersSection = new MembersSection();
