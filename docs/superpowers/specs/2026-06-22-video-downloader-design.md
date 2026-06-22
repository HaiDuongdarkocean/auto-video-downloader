# Video Downloader Design

**Date:** 2026-06-22
**Status:** Draft

## Overview

Ứng dụng quản lý tải video từ website với GUI hiện đại, hỗ trợ:
- Tải video từ streaming sites (m3u8 → mp4)
- Batch download với giới hạn số lượng song song
- Resume download nếu bị ngắt
- Chọn chất lượng video (tự động lấy cao nhất nếu nhỏ hơn mặc định)
- Tracking tập mới với scheduler cron-like
- Auto-download hoặc queue download cho tập mới
- Desktop + in-app notifications

## Architecture

### Project Structure

```
auto-video-downloader/
├── src/
│   ├── gui/              # PyQt GUI
│   │   ├── __init__.py
│   │   ├── main_window.py      # Cửa sổ chính
│   │   ├── download_dialog.py  # Dialog chọn video
│   │   ├── settings_dialog.py  # Dialog cài đặt
│   │   └── tracking_dialog.py  # Dialog quản lý tracking
│   ├── core/             # Logic nghiệp vụ
│   │   ├── __init__.py
│   │   ├── video_extractor.py  # Extract link từ selector
│   │   ├── history_manager.py  # Quản lý lịch sử JSON
│   │   ├── quality_selector.py # Chọn chất lượng video
│   │   ├── download/           # Download logic (deep modules)
│   │   │   ├── __init__.py
│   │   │   ├── m3u8_downloader.py      # Download m3u8
│   │   │   ├── video_converter.py      # Convert sang mp4
│   │   │   └── download_coordinator.py # Batch coordination
│   │   ├── tracking/          # Tracking logic (deep modules)
│   │   │   ├── __init__.py
│   │   │   ├── watch_list_manager.py   # Watch list CRUD
│   │   │   ├── episode_tracker.py      # Update detection
│   │   │   └── scheduler_manager.py    # Scheduler lifecycle
│   │   └── ports/             # External dependency ports
│   │       ├── __init__.py
│   │       ├── ffmpeg_port.py          # FFmpeg interface
│   │       ├── http_port.py            # HTTP interface
│   │       └── scheduler_port.py       # Scheduler interface
│   └── utils/            # Helper functions
│       ├── __init__.py
│       ├── path_helper.py      # Xử lý đường dẫn thư mục
│       └── notification_helper.py # Desktop notifications
├── tests/               # Tests
│   ├── unit/            # Unit tests
│   └── integration/     # Integration tests
├── main.py               # Entry point
├── requirements.txt      # Dependencies
└── config.json           # Cấu hình mặc định
```

### Principles

- GUI chỉ hiển thị và nhận input, không chứa logic nghiệp vụ
- Core module độc lập, có thể test mà không cần GUI
- Utils chứa các hàm tái sử dụng, không phụ thuộc vào module khác
- Tách biệt rõ ràng giữa UI và logic
- **Deep modules**: Small interface, focused implementation, high leverage
- **Ports & Adapters**: External dependencies injected through ports for testability

## Module: GUI

### main_window.py - Cửa sổ chính

**Features:**
- Modern dark theme hoặc light theme tùy chọn
- Card-based layout với rounded corners
- Input fields: URL, CSS selector với placeholder và icons
- Button: "Extract videos" → mở dialog chọn video
- Progress bar với percentage và speed indicator
- Menu bar với icons
- Menu: Settings → mở dialog cài đặt, Tracking → mở dialog tracking

**Responsibilities:**
- Nhận input từ user
- Gọi core module để extract và download
- Hiển thị progress updates
- Hiển thị in-app notifications

### download_dialog.py - Dialog chọn video

**Features:**
- List view với modern styling
- Custom checkbox với animation
- "Select all" button với icon
- Dropdown chọn chất lượng (nếu có nhiều)
- Smooth scroll cho danh sách dài
- Button: "Download selected"

**Responsibilities:**
- Hiển thị danh sách video tìm được
- Cho phép user chọn video muốn tải
- Trả về selection cho main window

### settings_dialog.py - Dialog cài đặt

**Features:**
- Form layout với spacing phù hợp
- Spinbox cho số lượng concurrent downloads
- Radio buttons hoặc combo box cho chất lượng mặc định
- Toggle switch cho "Stream convert" (mặc định unchecked)
- Save/Cancel buttons với modern styling

**Responsibilities:**
- Cho phép user cấu hình ứng dụng
- Lưu cấu hình vào config.json

### tracking_dialog.py - Dialog quản lý tracking

**Features:**
- Hiển thị danh sách series đang tracking
- Add/remove watch list
- Edit schedule (cron expression)
- Edit auto-download, notify per series
- Manual check for updates button

**Responsibilities:**
- Quản lý watch list
- Trigger manual check for updates
- Edit tracking settings per series

## Module: Core

### video_extractor.py - Extract link từ selector

**Functions:**
- `extract_video_links(url, selector) -> List[VideoInfo]`
  - Input: URL trang web, CSS selector
  - Output: Danh sách video với url, title, m3u8_link
  - Sử dụng requests + BeautifulSoup
  - Parse HTML theo CSS selector
  - Xử lý pagination nếu cần

**Data Structures:**
```python
class VideoInfo:
    url: str
    title: str
    m3u8_link: str
```

### download/ - Download logic (deep modules)

#### m3u8_downloader.py - Download m3u8

**Interface:**
- `download(m3u8_url, output_path, progress_callback) -> None`
  - Download m3u8 sử dụng FFmpegPort
  - Hỗ trợ resume (check file temp tồn tại)
  - Callback progress cho GUI update

**Responsibilities:**
- Download m3u8 streams
- Resume logic
- Progress reporting

#### video_converter.py - Convert sang mp4

**Interface:**
- `convert(input_path, output_path, progress_callback) -> None`
  - Convert video sang mp4 sử dụng FFmpegPort
  - Xóa file temp sau khi convert thành công
  - Callback progress cho GUI update

**Responsibilities:**
- Convert video formats
- Temp file cleanup
- Progress reporting

#### download_coordinator.py - Batch coordination

**Interface:**
- `download_videos(videos, max_concurrent, progress_callback) -> None`
  - Batch download với thread pool
  - Điều phối m3u8_downloader và video_converter
  - Tổng hợp progress từ tất cả downloads

**Responsibilities:**
- Batch coordination
- Thread pool management
- Progress aggregation

### history_manager.py - Quản lý lịch sử JSON

**Functions:**
- `is_downloaded(video_url) -> bool`
- `mark_downloaded(video_url, metadata)`
- `get_history() -> List[DownloadRecord]`

**Storage:**
- File JSON ở thư mục app
- Format: `{video_url: {timestamp, title, path, quality}}`

### quality_selector.py - Chọn chất lượng video

**Functions:**
- `get_available_qualities(m3u8_url) -> List[str]`
- `select_quality(qualities, default_quality) -> str`
  - Nếu chất lượng mong muốn không có, lấy cao nhất

**Responsibilities:**
- Phát hiện các chất lượng có sẵn
- Chọn chất lượng theo logic: default hoặc cao nhất

### tracking/ - Tracking logic (deep modules)

#### watch_list_manager.py - Watch list CRUD

**Interface:**
- `add_watch_list(url, selector, schedule, auto_download, notify) -> watch_id`
- `remove_watch_list(watch_id) -> bool`
- `get_watch_list(watch_id) -> WatchListEntry`
- `get_all_watch_lists() -> List[WatchListEntry]`

**Responsibilities:**
- Watch list persistence (JSON)
- CRUD operations
- Validation

#### episode_tracker.py - Update detection

**Interface:**
- `check_for_updates(watch_list_entry) -> List[NewEpisode]`
  - Sử dụng HTTPPort để fetch HTML
  - Sử dụng video_extractor để extract episodes
  - So sánh với known_episodes để tìm tập mới

**Responsibilities:**
- Update detection logic
- Episode comparison
- New episode identification

#### scheduler_manager.py - Scheduler lifecycle

**Interface:**
- `start_scheduler() -> None`
- `stop_scheduler() -> None`
- `add_job(watch_id, schedule, callback) -> None`
- `remove_job(watch_id) -> None`

**Responsibilities:**
- Scheduler lifecycle management
- Job scheduling sử dụng SchedulerPort
- Start/stop background thread

## Module: Ports

### ports/ - External dependency ports

#### ffmpeg_port.py - FFmpeg interface

**Interface:**
```python
class FFmpegPort(ABC):
    @abstractmethod
    def check_available(self) -> bool: pass

    @abstractmethod
    def get_path(self) -> str: pass

    @abstractmethod
    def run_command(self, args: List[str], progress_callback: Callable) -> subprocess.CompletedProcess: pass
```

**Adapters:**
- `FFmpegAdapter` - Production adapter using subprocess
- `MockFFmpegAdapter` - Test adapter for unit tests

**Dependency Category:** True external (mock for tests)

#### http_port.py - HTTP interface

**Interface:**
```python
class HTTPPort(ABC):
    @abstractmethod
    def get(self, url: str, timeout: int = 30) -> HTTPResponse: pass

    @abstractmethod
    def post(self, url: str, data: Dict, timeout: int = 30) -> HTTPResponse: pass
```

**Adapters:**
- `RequestsAdapter` - Production adapter using requests library
- `MockHTTPAdapter` - Test adapter for unit tests

**Dependency Category:** True external (mock for tests)

#### scheduler_port.py - Scheduler interface

**Interface:**
```python
class SchedulerPort(ABC):
    @abstractmethod
    def start(self) -> None: pass

    @abstractmethod
    def shutdown(self) -> None: pass

    @abstractmethod
    def add_job(self, func: Callable, trigger: str, **kwargs) -> str: pass

    @abstractmethod
    def remove_job(self, job_id: str) -> None: pass
```

**Adapters:**
- `APSchedulerAdapter` - Production adapter using APScheduler
- `MockSchedulerAdapter` - Test adapter for unit tests

**Dependency Category:** True external (mock for tests)

## Module: Utils

### path_helper.py - Xử lý đường dẫn thư mục

**Functions:**
- `create_output_path(base_url, video_title) -> str`
  - Tạo thư mục theo cấu trúc: `website_name/video_title/`
  - Sanitize filename (loại bỏ ký tự không hợp lệ)
  - Đảm bảo đường dẫn tồn tại

**Responsibilities:**
- Tạo cấu trúc thư mục tự động
- Sanitize filenames

### notification_helper.py - Desktop notifications

**Functions:**
- `show_desktop_notification(title, message)` - Windows toast
- `show_in_app_notification(message)` - GUI notification

**Responsibilities:**
- Gửi desktop notifications
- Gửi in-app notifications

## Data Flow

### Flow 1: Extract videos

1. User nhập URL + selector → GUI
2. GUI gọi `video_extractor.extract_video_links()`
3. Extractor fetch HTML, parse selector, trả List[VideoInfo]
4. GUI mở dialog hiển thị danh sách

### Flow 2: Download single video

1. User chọn video + chất lượng → GUI
2. GUI check `history_manager.is_downloaded()` → nếu đã tải, skip
3. GUI gọi `download_coordinator.download_videos()` với callback progress
4. Coordinator tạo output path qua `path_helper`
5. Coordinator gọi `m3u8_downloader.download()` với FFmpegPort
6. Downloader chạy FFmpeg download m3u8 → file temp (.ts hoặc .mp4)
7. Nếu `stream_convert = false`: Coordinator gọi `video_converter.convert()` → .mp4, xóa temp
8. Nếu `stream_convert = true`: Downloader stream convert trực tiếp → .mp4
9. FFmpeg output parsed → callback progress → GUI update
10. Hoàn thành → GUI gọi `history_manager.mark_downloaded()`

### Flow 3: Batch download

1. User chọn nhiều video → GUI
2. GUI gọi `download_coordinator.download_videos()` với max_concurrent
3. Coordinator tạo thread pool với max_workers
4. Mỗi thread gọi `m3u8_downloader.download()` + `video_converter.convert()`
5. Coordinator tổng hợp progress từ tất cả threads
6. GUI hiển thị tổng progress

### Flow 4: Tracking + Auto-download

1. User add watch list với schedule → GUI
2. GUI gọi `watch_list_manager.add_watch_list()`
3. GUI gọi `scheduler_manager.add_job()` với callback
4. Scheduler background thread check định kỳ qua SchedulerPort
5. Khi đến schedule: callback gọi `episode_tracker.check_for_updates()`
6. Episode tracker sử dụng HTTPPort + video_extractor
7. So sánh với known_episodes, tìm tập mới
8. Nếu có tập mới:
   - Nếu auto_download = true: Thêm vào download_coordinator
   - Nếu notify = true: Gửi desktop + in-app notification
9. Download queue chạy như Flow 2/3

## Error Handling

### Network errors

- Timeout khi fetch HTML → retry 3 lần, sau đó báo lỗi
- Invalid URL → validate trước khi gọi, báo lỗi user-friendly
- Connection lost → resume download nếu có file temp

### FFmpeg errors

- FFmpeg không tìm thấy → báo lỗi, hướng dẫn cài đặt
- Invalid m3u8 URL → báo lỗi, cho phép retry
- Convert failed → giữ file temp để debug, báo lỗi

### File system errors

- Disk full → báo lỗi, dừng download
- Permission denied → báo lỗi, kiểm tra thư mục
- Invalid path → sanitize lại, báo lỗi nếu vẫn fail

### GUI errors

- Thread crash → log error, không crash GUI
- Progress callback fail → ignore, tiếp tục download
- Dialog close khi đang download → confirm dialog

**Logging:**
- Tất cả errors có logging
- User-friendly error messages

## Dependencies

- Python 3.8+
- PyQt6 (GUI)
- requests (HTTP)
- beautifulsoup4 (HTML parsing)
- APScheduler (scheduler)
- pytest (testing)
- FFmpeg (external, cần cài đặt)
- abc (for port interfaces)

## Configuration

**config.json:**
```json
{
  "concurrent_downloads": 3,
  "default_quality": "1080p",
  "stream_convert": false,
  "ffmpeg_path": "",
  "output_dir": "./downloads"
}
```

## Testing Strategy

### Unit tests

- `test_video_extractor.py` - Mock HTML responses, test selector parsing
- `test_downloader.py` - Mock FFmpeg, test download logic, resume
- `test_history_manager.py` - Test JSON read/write, duplicate detection
- `test_quality_selector.py` - Test quality selection logic
- `test_tracker.py` - Test scheduler, update detection
- `test_path_helper.py` - Test path sanitization, folder creation

### Integration tests

- Test flow: extract → download → history update
- Test batch download với thread pool
- Test tracking + auto-download flow

### GUI tests

- Manual testing (PyQt hard để test tự động)
- Test các dialog interactions
- Test progress updates

**Test framework:** pytest
