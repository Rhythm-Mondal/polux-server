MAX_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_MIME_TYPES = {
    # Text & Data
    "text/plain",
    "text/html",
    "text/css",
    "text/csv",
    "text/xml",
    "application/json",
    "application/xml",
    "application/x-www-form-urlencoded",
    # Images
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
    "image/bmp",
    "image/tiff",
    # Video
    "video/mp4",
    "video/webm",
    "video/ogg",
    "video/quicktime",
    # Audio
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
    "audio/webm",
    "audio/aac",
    # Documents
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    # Archives
    "application/zip",
    "application/x-7z-compressed",
    "application/x-rar-compressed",
    "application/gzip",
    "application/x-tar",
    # Other
    "application/octet-stream",
    "application/javascript",
    "application/wasm",
}
MIME_ALIASES = {
    "image/jpg": "image/jpeg",
    "audio/mp3": "audio/mpeg",
    "application/x-pdf": "application/pdf",
}
