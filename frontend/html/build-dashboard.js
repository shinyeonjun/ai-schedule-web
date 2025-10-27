const fs = require('fs');
const path = require('path');

function buildDashboard() {
    console.log('🎯 대시보드 빌드 시작...');
    
    try {
        // 1. 메인 템플릿 로드
        let mainTemplate = fs.readFileSync('dashboard/main.html', 'utf8');
        console.log('✅ 메인 템플릿 로드 완료');
        
        // 2. 컴포넌트 로드
        const sidebar = fs.readFileSync('dashboard/sidebar.html', 'utf8');
        const header = fs.readFileSync('dashboard/header.html', 'utf8');
        console.log('✅ 컴포넌트 로드 완료');
        
        // 3. 섹션 로드
        const analysis = fs.readFileSync('dashboard/sections/analysis.html', 'utf8');
        const schedules = fs.readFileSync('dashboard/sections/schedules.html', 'utf8');
        const members = fs.readFileSync('dashboard/sections/members.html', 'utf8');
        const group = fs.readFileSync('dashboard/sections/group.html', 'utf8');
        console.log('✅ 섹션 로드 완료');
        
        // 4. 모달 로드
        const modals = fs.readFileSync('dashboard/modals.html', 'utf8');
        console.log('✅ 모달 로드 완료');
        
        // 5. 템플릿 치환
        mainTemplate = mainTemplate.replace('{{SIDEBAR}}', sidebar);
        mainTemplate = mainTemplate.replace('{{HEADER}}', header);
        mainTemplate = mainTemplate.replace('{{CONTENT}}', analysis + schedules + members + group);
        mainTemplate = mainTemplate.replace('{{MODALS}}', modals);
        console.log('✅ 템플릿 치환 완료');
        
        // 6. 최종 파일 생성
        fs.writeFileSync('dashboard.html', mainTemplate);
        console.log('✅ 최종 대시보드 파일 생성 완료: dashboard.html');
        
        console.log('🎉 대시보드 빌드 완료!');
        
    } catch (error) {
        console.error('❌ 빌드 실패:', error.message);
        process.exit(1);
    }
}

// 빌드 실행
buildDashboard();
