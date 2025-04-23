from .pet import (
    Pet,
    PetListResponse,
    PetOwners,
    PetOwnersResponse,
    PetPhoto,
    PetReports,
    PetReportsResponse,
)
from .report import (
    Report,
    ReportBase,
    ReportCreate,
    ReportListResponse,
    ReportPhoto,
    ReportPhotoBase,
    ReportPhotoCreate,
    ReportPhotosResponse,
    ReportPhotoUpdate,
    ReportStatus,
    ReportUpdate,
)
from .user import User, UserListResponse, UserPet, UserPetsResponse, UserReport, UserReportsResponse

UserPet.model_rebuild()
UserReport.model_rebuild()
UserPetsResponse.model_rebuild()
UserReportsResponse.model_rebuild()
PetOwners.model_rebuild()
PetOwnersResponse.model_rebuild()
PetReports.model_rebuild()
PetReportsResponse.model_rebuild()
