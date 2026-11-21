from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class OtpGenerationRequest(BaseModel):
    admin_user: str
    room_id: str
    validity_minutes: int = 30

class OtpGenerationResponse(BaseModel):
    otp_code: str
    expires_at: str
    room_id: str

class MachineEnrollmentRequest(BaseModel):
    otp_code: str
    room_id: str
    mac_address: str
    serial_number: Optional[str] = None
    cpu_info: Optional[str] = None
    ram_mb: Optional[int] = None
    is_teacher_pc: bool = False

class MachineEnrollmentResponse(BaseModel):
    status: str
    hostname: str
    room_id: str
    room_profile: str
    ansible_pull_url: str
    ldap_uri: str
    message: str

class TicketCreationRequest(BaseModel):
    title: str
    category: str
    description: str
    hostname: str
    username: str
    screenshot_data: Optional[str] = None

class TicketCreationResponse(BaseModel):
    success: bool
    ticket_id: str
    message: str
