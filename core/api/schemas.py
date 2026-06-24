from datetime import datetime

from ninja import Schema

from core.choices import BlogPostStatus, ReviewCadence, ReviewOutcome


class SubmitFeedbackIn(Schema):
    feedback: str
    page: str


class SubmitFeedbackOut(Schema):
    success: bool
    message: str


class BlogPostIn(Schema):
    title: str
    description: str = ""
    slug: str
    tags: str = ""
    content: str
    icon: str | None = None  # URL or base64 string
    image: str | None = None  # URL or base64 string
    status: BlogPostStatus = BlogPostStatus.DRAFT


class BlogPostOut(Schema):
    status: str  # API response status: 'success' or 'failure'
    message: str


class ProfileSettingsOut(Schema):
    has_pro_subscription: bool


class UserSettingsOut(Schema):
    profile: ProfileSettingsOut


class DeleteSitemapOut(Schema):
    success: bool
    message: str


class BulkUpdatePagesIn(Schema):
    page_ids: list[int]
    needs_review: bool


class BulkUpdatePagesOut(Schema):
    success: bool
    message: str
    updated_count: int


class AddEmailIn(Schema):
    email_address: str


class AddEmailOut(Schema):
    success: bool
    message: str
    email_id: int | None = None


class ToggleEmailIn(Schema):
    enabled: bool


class ToggleEmailOut(Schema):
    success: bool
    message: str


class DeleteEmailOut(Schema):
    success: bool
    message: str


class ErrorOut(Schema):
    code: str
    detail: str


class PaginationOut(Schema):
    limit: int
    offset: int
    total: int
    has_more: bool


class AgentSitemapCreateIn(Schema):
    sitemap_url: str
    client_label: str = ""
    pages_per_review: int | None = None
    review_cadence: ReviewCadence | None = None


class AgentSitemapOut(Schema):
    id: int
    uuid: str
    sitemap_url: str
    client_label: str
    pages_per_review: int
    review_cadence: str
    is_active: bool
    import_status: str
    last_import_message: str
    last_import_started_at: datetime | None
    last_import_finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AgentSitemapListOut(Schema):
    items: list[AgentSitemapOut]
    pagination: PaginationOut


class AgentSitemapArchiveOut(Schema):
    success: bool
    archived_pages: int
    sitemap: AgentSitemapOut


class AgentSitemapRefreshOut(Schema):
    success: bool
    queued: bool
    sitemap: AgentSitemapOut


class AgentClientOut(Schema):
    client_label: str
    active_site_count: int


class AgentClientListOut(Schema):
    items: list[AgentClientOut]
    pagination: PaginationOut


class AgentPageOut(Schema):
    id: int
    uuid: str
    url: str
    sitemap_id: int
    sitemap_url: str
    client_label: str
    review_cadence: str
    is_active: bool
    needs_review: bool
    reviewed: bool
    reviewed_at: datetime | None
    last_review_email_sent_at: datetime | None
    review_queue_attempts: int
    review_outcome: str
    review_note: str
    review_outcome_at: datetime | None
    is_due: bool
    review_url: str
    created_at: datetime
    updated_at: datetime


class AgentPageListOut(Schema):
    items: list[AgentPageOut]
    pagination: PaginationOut


class AgentPageSelectionOut(Schema):
    page: AgentPageOut | None


class AgentPageReviewIn(Schema):
    outcome: ReviewOutcome
    note: str = ""


class AgentPageReviewOut(Schema):
    success: bool
    page: AgentPageOut
