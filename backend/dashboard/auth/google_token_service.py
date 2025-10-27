import os
import httpx
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from supabase import create_client, Client

# Supabase 클라이언트 설정
supabase_url = os.getenv("SUPABASE_URL", "https://znvwtoozdcnaqpuzbnhu.supabase.co")
supabase_key = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpudnd0b296ZGNuYXFwdXpibmh1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ2Mjk0MjQsImV4cCI6MjA3MDIwNTQyNH0.UdqqsxqdUoPtPNyQSRfEjKL6cg90dUDNuzsancxIYR0")
supabase: Client = create_client(supabase_url, supabase_key)

# Google OAuth 설정
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

class GoogleTokenService:
    """Google 토큰 관리 및 자동 갱신 서비스"""
    
    @staticmethod
    async def save_google_tokens(user_id: int, tokens: Dict[str, Any]) -> bool:
        """Google 토큰을 데이터베이스에 저장"""
        try:
            # 만료 시간 계산
            expires_in = tokens.get('expires_in', 3600)  # 기본 1시간
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # 기존 토큰이 있으면 업데이트, 없으면 새로 생성
            existing_token = supabase.table('google_tokens').select('*').eq('user_id', user_id).execute()
            
            token_data = {
                'user_id': user_id,
                'access_token': tokens['access_token'],
                'refresh_token': tokens.get('refresh_token'),
                'token_type': tokens.get('token_type', 'Bearer'),
                'expires_at': expires_at.isoformat(),
                'scope': tokens.get('scope', ''),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if existing_token.data:
                # 기존 토큰 업데이트
                result = supabase.table('google_tokens').update(token_data).eq('user_id', user_id).execute()
            else:
                # 새 토큰 생성
                token_data['created_at'] = datetime.utcnow().isoformat()
                result = supabase.table('google_tokens').insert(token_data).execute()
            
            print(f"✅ Google 토큰 저장 완료: 사용자 {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Google 토큰 저장 실패: {str(e)}")
            return False
    
    @staticmethod
    async def get_valid_access_token(user_id: int) -> Optional[str]:
        """유효한 액세스 토큰 반환 (필요시 자동 갱신)"""
        try:
            # 사용자의 Google 토큰 조회
            result = supabase.table('google_tokens').select('*').eq('user_id', user_id).execute()
            
            if not result.data:
                print(f"⚠️ 사용자 {user_id}의 Google 토큰이 없습니다.")
                return None
            
            token_data = result.data[0]
            access_token = token_data['access_token']
            refresh_token = token_data['refresh_token']
            expires_at = datetime.fromisoformat(token_data['expires_at'].replace('Z', '+00:00'))
            
            # 토큰이 만료되었는지 확인 (5분 여유)
            # 모든 시간을 timezone-naive로 통일하여 비교
            current_time = datetime.utcnow()
            if expires_at.tzinfo is not None:
                # expires_at이 timezone-aware인 경우 UTC로 변환 후 timezone 정보 제거
                expires_at = expires_at.astimezone(timezone.utc).replace(tzinfo=None)
            
            if current_time + timedelta(minutes=5) > expires_at:
                print(f"⚠️ 토큰 만료 예정 또는 만료됨: 사용자 {user_id}")
                print(f"   현재 시간: {current_time}")
                print(f"   만료 시간: {expires_at}")
                print(f"   남은 시간: {expires_at - current_time}")
                
                # 토큰이 만료되었거나 곧 만료될 예정
                if refresh_token:
                    print(f"🔄 토큰 갱신 시작: 사용자 {user_id}")
                    new_tokens = await GoogleTokenService._refresh_access_token(refresh_token)
                    
                    if new_tokens:
                        # 새 토큰 저장
                        await GoogleTokenService.save_google_tokens(user_id, new_tokens)
                        print(f"✅ 토큰 갱신 완료: 사용자 {user_id}")
                        return new_tokens['access_token']
                    else:
                        print(f"❌ 토큰 갱신 실패: 사용자 {user_id}")
                        return None
                else:
                    print(f"❌ 리프레시 토큰이 없어서 갱신 불가: 사용자 {user_id}")
                    return None
            else:
                print(f"✅ 유효한 액세스 토큰 반환: 사용자 {user_id}")
                return access_token
            
            if refresh_token:
                print(f"🔄 토큰 갱신 시작: 사용자 {user_id}")
                new_tokens = await GoogleTokenService._refresh_access_token(refresh_token)
                
                if new_tokens:
                    # 새 토큰 저장
                    await GoogleTokenService.save_google_tokens(user_id, new_tokens)
                    print(f"✅ 토큰 갱신 완료: 사용자 {user_id}")
                    return new_tokens['access_token']
                else:
                    print(f"❌ 토큰 갱신 실패: 사용자 {user_id}")
                    return None
            else:
                print(f"❌ 리프레시 토큰이 없어서 갱신 불가: 사용자 {user_id}")
                return None
                
        except Exception as e:
            print(f"❌ 액세스 토큰 조회 실패: {str(e)}")
            return None
    
    @staticmethod
    async def _refresh_access_token(refresh_token: str) -> Optional[Dict[str, Any]]:
        """리프레시 토큰으로 액세스 토큰 갱신"""
        try:
            token_url = "https://oauth2.googleapis.com/token"
            
            data = {
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            
            print(f"🔄 토큰 갱신 요청 시작")
            print(f"📡 요청 URL: {token_url}")
            print(f"🔑 클라이언트 ID: {GOOGLE_CLIENT_ID[:10]}...")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                
                print(f"📡 토큰 갱신 응답: {response.status_code}")
                print(f"📄 응답 내용: {response.text}")
                
                if response.status_code == 200:
                    tokens = response.json()
                    print("✅ 액세스 토큰 갱신 성공")
                    return tokens
                else:
                    print(f"❌ 액세스 토큰 갱신 실패: {response.status_code} - {response.text}")
                    # 구체적인 오류 메시지 파싱
                    try:
                        error_data = response.json()
                        error_message = error_data.get('error_description', '알 수 없는 오류')
                        print(f"❌ 토큰 갱신 오류 메시지: {error_message}")
                    except:
                        print(f"❌ 토큰 갱신 오류 응답 파싱 실패")
                    return None
                    
        except Exception as e:
            print(f"❌ 토큰 갱신 중 오류: {str(e)}")
            return None
    
    @staticmethod
    async def revoke_google_tokens(user_id: int) -> bool:
        """사용자의 Google 토큰 삭제"""
        try:
            result = supabase.table('google_tokens').delete().eq('user_id', user_id).execute()
            print(f"✅ Google 토큰 삭제 완료: 사용자 {user_id}")
            return True
        except Exception as e:
            print(f"❌ Google 토큰 삭제 실패: {str(e)}")
            return False
    
    @staticmethod
    async def check_token_status(user_id: int) -> Dict[str, Any]:
        """토큰 상태 확인"""
        try:
            result = supabase.table('google_tokens').select('*').eq('user_id', user_id).execute()
            
            if not result.data:
                return {
                    'has_token': False,
                    'is_valid': False,
                    'message': 'Google 토큰이 없습니다.'
                }
            
            token_data = result.data[0]
            expires_at = datetime.fromisoformat(token_data['expires_at'].replace('Z', '+00:00'))
            is_valid = datetime.utcnow() < expires_at
            
            return {
                'has_token': True,
                'is_valid': is_valid,
                'expires_at': token_data['expires_at'],
                'has_refresh_token': bool(token_data['refresh_token']),
                'scope': token_data.get('scope', ''),
                'message': '토큰이 유효합니다.' if is_valid else '토큰이 만료되었습니다.'
            }
            
        except Exception as e:
            return {
                'has_token': False,
                'is_valid': False,
                'message': f'토큰 상태 확인 실패: {str(e)}'
            }
    
    @staticmethod
    async def send_gmail(user_id: int, to_email: str, subject: str, body: str) -> bool:
        """Gmail API를 사용하여 이메일 발송"""
        try:
            # 유효한 액세스 토큰 가져오기 (자동 갱신 포함)
            access_token = await GoogleTokenService.get_valid_access_token(user_id)
            
            if not access_token:
                print(f"❌ 사용자 {user_id}의 유효한 Google 액세스 토큰이 없습니다.")
                return False
            
            # Gmail API를 사용하여 이메일 발송
            gmail_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # 이메일 메시지 구성
            import base64
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            message = MIMEMultipart()
            message['to'] = to_email
            message['subject'] = subject
            
            text_part = MIMEText(body, 'plain', 'utf-8')
            message.attach(text_part)
            
            # Base64 인코딩
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            email_data = {
                'raw': raw_message
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(gmail_url, json=email_data, headers=headers)
                
                if response.status_code == 200:
                    print(f"✅ Gmail 발송 성공: {to_email}")
                    return True
                else:
                    print(f"❌ Gmail 발송 실패: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Gmail 발송 중 오류: {str(e)}")
            return False
    
    def get_valid_credentials(self, user_id):
        """유효한 Google API credentials 객체 반환 (자동 갱신 포함)"""
        try:
            from google.oauth2.credentials import Credentials
            import google.auth.transport.requests
            
            # 사용자의 Google 토큰 조회
            result = supabase.table('google_tokens').select('*').eq('user_id', user_id).execute()
            
            if not result.data:
                print(f"⚠️ 사용자 {user_id}의 Google 토큰이 없습니다.")
                return None
            
            token_data = result.data[0]
            expires_at_str = token_data.get('expires_at')
            
            # 만료 시간 파싱
            expires_at = None
            if expires_at_str:
                try:
                    expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                    if expires_at.tzinfo is not None:
                        expires_at = expires_at.astimezone(timezone.utc).replace(tzinfo=None)
                except Exception as e:
                    print(f"⚠️ 만료 시간 파싱 실패: {e}")
            
            # Credentials 객체 생성
            credentials = Credentials(
                token=token_data['access_token'],
                refresh_token=token_data['refresh_token'],
                token_uri='https://oauth2.googleapis.com/token',
                client_id=GOOGLE_CLIENT_ID,
                client_secret=GOOGLE_CLIENT_SECRET,
                scopes=token_data.get('scope', '').split(' ') if token_data.get('scope') else [],
                expiry=expires_at
            )
            
            # 토큰 만료 확인 및 자동 갱신 (5분 여유)
            current_time = datetime.utcnow()
            if expires_at and current_time + timedelta(minutes=5) > expires_at:
                print(f"🔄 토큰 만료 예정으로 자동 갱신 시작: 사용자 {user_id}")
                
                if credentials.refresh_token:
                    try:
                        # 동기적으로 토큰 갱신 (httpx 사용)
                        import httpx
                        
                        token_url = "https://oauth2.googleapis.com/token"
                        data = {
                            'client_id': GOOGLE_CLIENT_ID,
                            'client_secret': GOOGLE_CLIENT_SECRET,
                            'refresh_token': credentials.refresh_token,
                            'grant_type': 'refresh_token'
                        }
                        
                        with httpx.Client() as client:
                            response = client.post(token_url, data=data)
                            
                            if response.status_code == 200:
                                new_tokens = response.json()
                                
                                # 새 토큰으로 credentials 업데이트
                                credentials.token = new_tokens['access_token']
                                expires_in = new_tokens.get('expires_in', 3600)
                                credentials.expiry = datetime.utcnow() + timedelta(seconds=expires_in)
                                
                                # 데이터베이스에 저장
                                update_data = {
                                    'access_token': credentials.token,
                                    'expires_at': credentials.expiry.isoformat(),
                                    'updated_at': datetime.utcnow().isoformat()
                                }
                                
                                supabase.table('google_tokens').update(update_data).eq('user_id', user_id).execute()
                                print(f"✅ 토큰 자동 갱신 완료: 사용자 {user_id}")
                            else:
                                print(f"❌ 토큰 갱신 HTTP 오류: {response.status_code}")
                                return None
                        
                    except Exception as refresh_error:
                        print(f"❌ 토큰 갱신 실패: {refresh_error}")
                        return None
                else:
                    print(f"❌ 리프레시 토큰이 없어서 갱신 불가: 사용자 {user_id}")
                    return None
            
            return credentials
            
        except Exception as e:
            print(f"❌ Credentials 생성 실패: {str(e)}")
            return None
    
    @staticmethod
    async def check_and_refresh_token(user_id):
        """토큰 상태 확인 및 필요시 갱신 (JWT 세션과 동기화)"""
        try:
            # 사용자의 Google 토큰 조회
            result = supabase.table('google_tokens').select('*').eq('user_id', user_id).execute()
            
            if not result.data:
                print(f"⚠️ 사용자 {user_id}의 Google 토큰이 없습니다.")
                return False
            
            token_data = result.data[0]
            expires_at_str = token_data.get('expires_at')
            refresh_token = token_data.get('refresh_token')
            
            if not expires_at_str or not refresh_token:
                print(f"⚠️ 토큰 정보가 불완전합니다: 사용자 {user_id}")
                return False
            
            # 만료 시간 확인
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            if expires_at.tzinfo is not None:
                expires_at = expires_at.astimezone(timezone.utc).replace(tzinfo=None)
            
            current_time = datetime.utcnow()
            
            # 토큰이 1시간 이내에 만료되면 갱신
            if current_time + timedelta(hours=1) > expires_at:
                print(f"🔄 토큰 갱신 필요: 사용자 {user_id}")
                
                new_tokens = await GoogleTokenService._refresh_access_token(refresh_token)
                if new_tokens:
                    await GoogleTokenService.save_google_tokens(user_id, new_tokens)
                    print(f"✅ 토큰 자동 갱신 완료: 사용자 {user_id}")
                    return True
                else:
                    print(f"❌ 토큰 갱신 실패: 사용자 {user_id}")
                    return False
            else:
                print(f"✅ 토큰이 유효합니다: 사용자 {user_id}")
                return True
                
        except Exception as e:
            print(f"❌ 토큰 확인 및 갱신 실패: {str(e)}")
            return False
    
    @staticmethod
    async def sync_token_with_jwt_session(user_id):
        """JWT 세션과 Google 토큰 동기화 (하루 단위)"""
        try:
            print(f"🔄 JWT 세션과 Google 토큰 동기화 시작: 사용자 {user_id}")
            
            # 사용자의 Google 토큰 조회
            result = supabase.table('google_tokens').select('*').eq('user_id', user_id).execute()
            
            if not result.data:
                print(f"⚠️ 사용자 {user_id}의 Google 토큰이 없습니다.")
                return False
            
            token_data = result.data[0]
            refresh_token = token_data.get('refresh_token')
            
            if not refresh_token:
                print(f"⚠️ 리프레시 토큰이 없습니다: 사용자 {user_id}")
                return False
            
            # 토큰 갱신 (JWT 세션 시작 시 항상 갱신)
            new_tokens = await GoogleTokenService._refresh_access_token(refresh_token)
            
            if new_tokens:
                # 새 토큰 저장
                await GoogleTokenService.save_google_tokens(user_id, new_tokens)
                print(f"✅ JWT 세션과 Google 토큰 동기화 완료: 사용자 {user_id}")
                return True
            else:
                print(f"❌ 토큰 갱신 실패: 사용자 {user_id}")
                return False
                
        except Exception as e:
            print(f"❌ JWT 세션과 토큰 동기화 실패: {str(e)}")
            return False
    
    @staticmethod
    async def daily_token_maintenance():
        """일일 토큰 유지보수 (만료 예정 토큰 갱신)"""
        try:
            print("🔄 일일 Google 토큰 유지보수 시작")
            
            # 24시간 이내 만료 예정인 토큰들 조회
            tomorrow = datetime.utcnow() + timedelta(days=1)
            
            result = supabase.table('google_tokens').select('*').lt('expires_at', tomorrow.isoformat()).execute()
            
            if not result.data:
                print("✅ 갱신이 필요한 토큰이 없습니다.")
                return
            
            renewed_count = 0
            failed_count = 0
            
            for token_data in result.data:
                user_id = token_data['user_id']
                refresh_token = token_data.get('refresh_token')
                
                if refresh_token:
                    try:
                        new_tokens = await GoogleTokenService._refresh_access_token(refresh_token)
                        if new_tokens:
                            await GoogleTokenService.save_google_tokens(user_id, new_tokens)
                            renewed_count += 1
                            print(f"✅ 토큰 갱신 완료: 사용자 {user_id}")
                        else:
                            failed_count += 1
                            print(f"❌ 토큰 갱신 실패: 사용자 {user_id}")
                    except Exception as e:
                        failed_count += 1
                        print(f"❌ 토큰 갱신 오류: 사용자 {user_id}, 오류: {e}")
                else:
                    failed_count += 1
                    print(f"⚠️ 리프레시 토큰 없음: 사용자 {user_id}")
            
            print(f"🔄 일일 토큰 유지보수 완료: 갱신 {renewed_count}개, 실패 {failed_count}개")
            
        except Exception as e:
            print(f"❌ 일일 토큰 유지보수 실패: {str(e)}")