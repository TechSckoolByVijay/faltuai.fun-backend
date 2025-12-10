import io
import logging
from typing import Optional
from PyPDF2 import PdfReader
from fastapi import UploadFile, HTTPException, status
from app.config import settings

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Service for processing documents and extracting text
    """
    
    @staticmethod
    def validate_file(file: UploadFile) -> bool:
        """
        Validate uploaded file type and size
        
        Args:
            file: Uploaded file
            
        Returns:
            True if valid
            
        Raises:
            HTTPException: If file is invalid
        """
        # Check file size
        if hasattr(file, 'size') and file.size and file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        # Check file type
        if file.content_type not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type. Allowed types: {settings.ALLOWED_FILE_TYPES}"
            )
        
        return True
    
    @staticmethod
    async def extract_text_from_pdf(file: UploadFile) -> str:
        """
        Extract text from PDF file using PyPDF2
        
        Args:
            file: PDF file
            
        Returns:
            Extracted text content
        """
        try:
            content = await file.read()
            pdf_file = io.BytesIO(content)
            pdf_reader = PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            if not text.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Could not extract text from PDF. The file might be image-based or corrupted."
                )
                
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process PDF file"
            )
    
    @staticmethod
    async def extract_text_from_txt(file: UploadFile) -> str:
        """
        Extract text from text file
        
        Args:
            file: Text file
            
        Returns:
            File content as string
        """
        try:
            content = await file.read()
            text = content.decode('utf-8')
            
            if not text.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Text file is empty"
                )
                
            return text.strip()
            
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not decode text file. Please ensure it's UTF-8 encoded."
            )
        except Exception as e:
            logger.error(f"Error reading text file: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process text file"
            )
    
    @classmethod
    async def process_file(cls, file: UploadFile) -> str:
        """
        Process uploaded file and extract text
        
        Args:
            file: Uploaded file (PDF or TXT)
            
        Returns:
            Extracted text content
        """
        # Validate file
        cls.validate_file(file)
        
        # Reset file pointer
        await file.seek(0)
        
        # Extract text based on file type
        if file.content_type == "application/pdf":
            return await cls.extract_text_from_pdf(file)
        elif file.content_type == "text/plain":
            return await cls.extract_text_from_txt(file)
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported file type"
            )

# TODO: Implement Azure Document Intelligence integration
class AzureDocumentProcessor:
    """
    Service for processing documents using Azure Document Intelligence
    Currently placeholder for future implementation
    """
    
    @staticmethod
    async def extract_text_advanced(file: UploadFile) -> str:
        """
        Extract text using Azure Document Intelligence
        
        Args:
            file: Uploaded file
            
        Returns:
            Extracted text with better accuracy
        """
        # TODO: Implement Azure Document Intelligence
        # For now, fall back to basic processing
        processor = DocumentProcessor()
        return await processor.process_file(file)

# Export services
__all__ = ["DocumentProcessor", "AzureDocumentProcessor"]