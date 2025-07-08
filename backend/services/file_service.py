import os
import aiofiles
from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException
from pathlib import Path
import uuid
from datetime import datetime

from config import settings


class FileService:
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def save_uploaded_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        업로드된 파일을 저장하고 정보를 반환합니다.
        
        Args:
            file: 업로드된 파일
            
        Returns:
            파일 정보 딕셔너리
        """
        try:
            # 파일 검증
            self._validate_file(file)
            
            # 고유 파일명 생성
            file_extension = Path(file.filename).suffix.lower()
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = self.upload_dir / unique_filename
            
            # 파일 저장
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # 파일 정보 반환
            return {
                "filename": file.filename,
                "saved_filename": unique_filename,
                "file_path": str(file_path),
                "file_size": len(content),
                "content_type": file.content_type,
                "upload_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"파일 저장 중 오류 발생: {str(e)}")
    
    def _validate_file(self, file: UploadFile) -> None:
        """파일 검증을 수행합니다."""
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        # 파일 확장자 검증
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"지원하지 않는 파일 형식입니다. 허용된 형식: {', '.join(settings.ALLOWED_FILE_TYPES)}"
            )
        
        # 파일 크기 검증 (실제 크기는 읽어야 알 수 있지만, 여기서는 헤더 정보 사용)
        if hasattr(file, 'size') and file.size and file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"파일 크기가 너무 큽니다. 최대 크기: {settings.MAX_FILE_SIZE // (1024*1024)}MB"
            )
    
    async def extract_text_from_file(self, file_path: str) -> str:
        """
        파일에서 텍스트를 추출합니다.
        
        Args:
            file_path: 파일 경로
            
        Returns:
            추출된 텍스트
        """
        try:
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == '.txt':
                return await self._extract_from_txt(file_path)
            elif file_extension == '.docx':
                return await self._extract_from_docx(file_path)
            elif file_extension == '.pdf':
                return await self._extract_from_pdf(file_path)
            else:
                raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"텍스트 추출 중 오류 발생: {str(e)}")
    
    async def _extract_from_txt(self, file_path: str) -> str:
        """TXT 파일에서 텍스트를 추출합니다."""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return content
        except UnicodeDecodeError:
            # UTF-8로 읽기 실패 시 다른 인코딩 시도
            try:
                async with aiofiles.open(file_path, 'r', encoding='cp949') as f:
                    content = await f.read()
                    return content
            except:
                async with aiofiles.open(file_path, 'r', encoding='latin-1') as f:
                    content = await f.read()
                    return content
    
    async def _extract_from_docx(self, file_path: str) -> str:
        """DOCX 파일에서 텍스트를 추출합니다."""
        try:
            # python-docx 라이브러리 사용 (설치 필요)
            from docx import Document
            
            doc = Document(file_path)
            text_content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            return '\n'.join(text_content)
            
        except ImportError:
            # docx 라이브러리가 없는 경우 기본 텍스트 반환
            return "DOCX 파일 처리를 위해 python-docx 라이브러리가 필요합니다."
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DOCX 파일 처리 중 오류: {str(e)}")
    
    async def _extract_from_pdf(self, file_path: str) -> str:
        """PDF 파일에서 텍스트를 추출합니다."""
        try:
            # PyPDF2 라이브러리 사용 (설치 필요)
            import PyPDF2
            
            text_content = []
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(text)
            
            return '\n'.join(text_content)
            
        except ImportError:
            # PyPDF2 라이브러리가 없는 경우 기본 텍스트 반환
            return "PDF 파일 처리를 위해 PyPDF2 라이브러리가 필요합니다."
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF 파일 처리 중 오류: {str(e)}")
    
    async def cleanup_file(self, file_path: str) -> None:
        """임시 파일을 정리합니다."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"파일 정리 중 오류 발생: {e}")
    
    async def cleanup_old_files(self, days: int = 1) -> None:
        """오래된 파일들을 정리합니다."""
        try:
            from datetime import timedelta
            
            cutoff_time = datetime.now() - timedelta(days=days)
            
            for file_path in self.upload_dir.glob('*'):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                        
        except Exception as e:
            print(f"오래된 파일 정리 중 오류 발생: {e}")


# 싱글톤 인스턴스
file_service = FileService() 