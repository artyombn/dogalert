from .user import User, UserPet, UserReport, UserListResponse, UserPetsResponse, UserReportsResponse
from .pet import Pet, PetPhoto, PetOwners, PetListResponse, PetOwnersResponse, PetReportsResponse, PetPhotosResponse
from .report import Report, ReportUpdate, ReportCreate, ReportPhoto, ReportBase, ReportListResponse, ReportPhotoBase, ReportPhotoCreate, ReportPhotosResponse, ReportPhotoUpdate, ReportStatus

UserPet.model_rebuild()
UserReport.model_rebuild()
UserPetsResponse.model_rebuild()
UserReportsResponse.model_rebuild()
PetOwners.model_rebuild()
PetOwnersResponse.model_rebuild()
PetReportsResponse.model_rebuild()