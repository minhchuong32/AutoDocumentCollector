# Auto Document Collector

Auto Document Collector là chương trình Python tự động đọc RSS, lọc các liên kết tài liệu, kiểm tra nguồn và tải PDF/EPUB được phép vào máy tính cá nhân. Mỗi tài liệu được ghi trạng thái trong SQLite để tránh tải lại và hỗ trợ theo dõi lỗi.

Phiên bản hiện tại là v1.0, xử lý URL tải trực tiếp và chuyển đổi công khai URL abstract của arXiv (`/abs/...`) sang endpoint PDF canonical. Chương trình không đăng nhập, không vượt CAPTCHA, không phá DRM và không tải tài liệu từ domain chưa được cấu hình cho phép.

## 1. Luồng xử lý

Mỗi lần chạy, `src.main` thực hiện các bước sau:

```text
RSS_URLS
	-> RSSReader đọc feed
	-> DocumentFilter lọc từ khóa và đuôi .pdf/.epub
	-> URLValidator kiểm tra HTTPS và ALLOWED_DOMAINS
	-> DocumentResolver xác nhận URL tải trực tiếp hoặc URL arXiv /abs/...
	-> Downloader kiểm tra HTTP, MIME, dung lượng, chữ ký file
	-> downloads/raw/pdf hoặc downloads/raw/epub
	-> SQLite + collector.log
```

Một tài liệu lỗi không làm dừng các tài liệu còn lại. Lỗi RSS của một feed cũng chỉ làm feed đó thất bại; các feed tiếp theo vẫn được xử lý.

## 2. Cấu trúc thư mục

```text
AutoDocumentCollector/
|
|-- config/
|   |-- .env.example       Mau cau hinh, co the sao chep thanh .env
|   `-- settings.py        Doc bien moi truong va tao duong dan
|
|-- data/
|   `-- collector.db       SQLite, tu tao khi chay lan dau
|
|-- downloads/raw/
|   |-- pdf/                Tai lieu PDF da tai xong
|   `-- epub/               Tai lieu EPUB da tai xong
|
|-- logs/
|   `-- collector.log      Log cua cac lan chay
|
|-- src/
|   |-- main.py             Orchestrator/pipeline chinh
|   |-- services/
|   |   |-- rss_reader.py       Doc RSS thanh FeedItem
|   |   |-- document_filter.py  Loc tu khoa va loai tai lieu
|   |   |-- url_validator.py    Kiem tra HTTPS/domain
|   |   |-- document_resolver.py  Resolve link trực tiếp và arXiv /abs/...
|   |   `-- downloader.py       Tai file theo chunk va ghi file tam
|   |-- database/
|   |   |-- db.py               Khoi tao schema SQLite
|   |   `-- document_repository.pyCRUD document va chong trung
|   `-- utils/
|       |-- logger.py            Cau hinh logging
|       `-- file_manager.py      Tao thu muc luu tru
|
|-- tests/                  Test khong can Internet that
|-- requirements.txt
|-- .env                    Cau hinh may cuc bo, khong commit
`-- README.md
```

`data`, `downloads` và `.env` được loại khỏi Git theo `.gitignore`. Các thư mục cần thiết được tạo tự động bởi `Settings.ensure_directories()`.

## 3. Giải thích các module

### `config/settings.py`

Đọc `.env` bằng `python-dotenv`, sau đó tạo đối tượng `Settings` chứa RSS, domain, từ khóa, đường dẫn, timeout và giới hạn dung lượng. Tất cả đường dẫn tương đối đều tính từ thư mục project, nên Task Scheduler phải đặt đúng **Start in**.

### `src/services/rss_reader.py`

Gửi request đến RSS bằng `requests`, phân tích nội dung bằng `feedparser` và trả về các `FeedItem` gồm `title`, `url`, `published`. Feed lỗi hoặc không hợp lệ sẽ được ghi log bởi pipeline.

### `src/services/document_filter.py`

Chỉ nhận URL có phần mở rộng `.pdf` hoặc `.epub`. Nếu có `KEYWORDS`, từ khóa được tìm trong tiêu đề và URL. Khi `KEYWORDS` rỗng, mọi tài liệu đúng định dạng đều qua bước từ khóa.

### `src/services/url_validator.py`

Chỉ chấp nhận URL `https://`. Host phải trùng domain trong `ALLOWED_DOMAINS` hoặc là subdomain của domain đó. Allowlist rỗng đồng nghĩa với không cho tải URL nào.

### `src/services/document_resolver.py`

Resolver nhận URL PDF/EPUB trực tiếp. Ngoài ra, URL arXiv dạng `https://arxiv.org/abs/<id>` hoặc `https://export.arxiv.org/abs/<id>` được chuyển thành `https://export.arxiv.org/pdf/<id>`. Resolver không bóc tách link từ trang HTML và không theo redirect tự do.

### `src/services/downloader.py`

Downloader thực hiện các kiểm tra sau:

- Từ chối HTTP status từ 300 trở lên và không tự theo redirect.
- Kiểm tra `Content-Type` tương ứng với PDF/EPUB.
- Kiểm tra `Content-Length` nếu server cung cấp.
- Đọc theo chunk, không vượt `MAX_FILE_SIZE`.
- Kiểm tra chữ ký file: PDF phải bắt đầu bằng `%PDF`, EPUB phải là ZIP bắt đầu bằng `PK`.
- Ghi vào `.part`, chỉ đổi tên thành file hoàn chỉnh sau khi tải thành công.

### `src/database/`

`db.py` tạo hai bảng `documents` và `feeds`. `document_repository.py` dùng `source_url` là khóa duy nhất để chống trùng và cập nhật trạng thái.

Các trạng thái dùng trong v1:

| Trạng thái   | Ý nghĩa                              |
| ------------ | ------------------------------------ |
| `DISCOVERED` | Đã thấy trong RSS                    |
| `VALIDATED`  | Đã qua filter, validator và resolver |
| `DOWNLOADED` | Tải xong, có `file_path`             |
| `SKIPPED`    | Không phù hợp hoặc không được phép   |
| `FAILED`     | Có lỗi khi xử lý hoặc tải            |

## 4. Cài đặt lần đầu trên Windows

Mở PowerShell và đi tới đúng thư mục project:

```powershell
Set-Location "G:\hcmute\ThucTap\NSX\auto_download_doc_tool\AutoDocumentCollector"
```

Khuyến nghị Python 3.12 hoặc 3.13. Kiểm tra Python và tạo virtualenv:

```powershell
python --version
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Nếu PowerShell chặn activate script, có thể chạy trực tiếp Python trong virtualenv mà không cần activate:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 5. Cấu hình thật

Tạo file `.env` từ mẫu:

```powershell
Copy-Item config\.env.example .env
notepad .env
```

Ví dụ cấu hình:

```dotenv
RSS_URLS=https://example.org/feed.xml,https://export.arxiv.org/rss/cs.SE
ALLOWED_DOMAINS=example.org,export.arxiv.org
KEYWORDS=software engineering,computer science
DOWNLOAD_DIR=downloads/raw
DATABASE_PATH=data/collector.db
LOG_PATH=logs/collector.log
MAX_FILE_SIZE=31457280
REQUEST_TIMEOUT=30
```

Ý nghĩa biến:

| Biến              | Bắt buộc | Mô tả                                              |
| ----------------- | -------- | -------------------------------------------------- |
| `RSS_URLS`        | Có       | Danh sách RSS, phân tách bằng dấu phẩy             |
| `ALLOWED_DOMAINS` | Có       | Domain được phép tải, phân tách bằng dấu phẩy      |
| `KEYWORDS`        | Không    | Từ khóa trong tiêu đề hoặc URL                     |
| `DOWNLOAD_DIR`    | Không    | Thư mục lưu PDF/EPUB                               |
| `DATABASE_PATH`   | Không    | Đường dẫn SQLite                                   |
| `LOG_PATH`        | Không    | Đường dẫn log                                      |
| `MAX_FILE_SIZE`   | Không    | Dung lượng tối đa, tính bằng byte; mặc định 30 MiB |
| `REQUEST_TIMEOUT` | Không    | Timeout request, tính bằng giây; mặc định 30       |

### Lưu ý về Google Alerts

Google Alerts thường trả về URL bài viết hoặc URL trung gian, không bảo đảm là link tải PDF/EPUB trực tiếp. Ngoại lệ hiện tại là URL arXiv `/abs/<id>` được resolver chuyển sang endpoint PDF công khai. Các trang HTML của nguồn khác vẫn có trạng thái `SKIPPED`; đây là hành vi chủ ý để không tự động phân tích trang web hoặc vượt cơ chế truy cập.

Khi triển khai thật, cần dùng RSS có link tải trực tiếp hợp pháp và thêm domain của nguồn đó vào `ALLOWED_DOMAINS`. Không thêm `google.com` vào allowlist chỉ để cố tải URL trung gian.

## 6. Chạy thủ công

Luôn chạy từ thư mục `AutoDocumentCollector`:

```powershell
.\venv\Scripts\python.exe -m src.main
```

Kết quả cần kiểm tra:

- PDF nằm trong `downloads/raw/pdf`.
- EPUB nằm trong `downloads/raw/epub`.
- Database nằm tại `data/collector.db`.
- Log nằm tại `logs/collector.log`.

Có thể xem log cuối cùng bằng PowerShell:

```powershell
Get-Content logs\collector.log -Tail 50
```

Mỗi lần chạy cũng in một bộ đếm dạng:

```text
{'feeds': 1, 'discovered': 10, 'downloaded': 2, 'skipped': 7, 'failed': 1}
```

Các số này lần lượt là feed đọc thành công, kết quả có URL, tải thành công, bỏ qua và thất bại.

## 7. Kiểm thử

Test dùng response giả và database tạm, không cần tải tài liệu Internet:

```powershell
.\venv\Scripts\python.exe -m pytest -v
```

Các nhóm test hiện có:

- Lọc đuôi file và từ khóa.
- HTTPS, domain chính và subdomain.
- Tải PDF hợp lệ.
- Từ chối chữ ký file sai.
- Từ chối file vượt giới hạn.
- Xóa file `.part` khi tải lỗi.
- Chống bản ghi trùng trong SQLite.

## 8. Kiểm tra SQLite

Nếu có SQLite CLI, xem các tài liệu đã xử lý bằng:

```powershell
sqlite3 data\collector.db "SELECT id, title, file_type, status, file_path FROM documents ORDER BY id DESC;"
```

Hoặc dùng Python:

```powershell
python -c "import sqlite3; c=sqlite3.connect('data/collector.db'); print(*c.execute('SELECT title,status,file_path FROM documents'), sep='\n')"
```

## 9. Thiết lập Windows Task Scheduler

### Cách làm bằng giao diện

1. Mở **Task Scheduler** và chọn **Create Task**.
2. Tab **General**: đặt tên `Auto Document Collector`.
3. Tab **Triggers**: tạo lịch chạy mỗi 15 phút hoặc theo nhu cầu.
4. Tab **Actions**:
   - **Program/script**: đường dẫn tuyệt đối tới `venv\Scripts\python.exe`.
   - **Add arguments**: `-m src.main`.
   - **Start in**: đường dẫn tuyệt đối tới thư mục `AutoDocumentCollector`.
5. Tab **Settings**: bật chạy lại khi lỗi và chọn không khởi động task mới nếu task trước vẫn đang chạy.
6. Chọn **Run** để test, sau đó xem **History** và `logs\collector.log`.

Ví dụ giá trị thực tế:

```text
Program:  G:\hcmute\ThucTap\NSX\auto_download_doc_tool\AutoDocumentCollector\venv\Scripts\python.exe
Arguments: -m src.main
Start in: G:\hcmute\ThucTap\NSX\auto_download_doc_tool\AutoDocumentCollector
```

Task Scheduler không thay thế máy chủ. Máy phải bật, virtualenv và file `.env` phải còn tại đúng đường dẫn, đồng thời máy cần có Internet lúc task chạy.

## 10. Xử lý sự cố

### Không tải được tài liệu

Kiểm tra URL có bắt đầu bằng `https://`, có đuôi `.pdf`/`.epub`, domain có nằm trong `ALLOWED_DOMAINS` và server có trả MIME phù hợp hay không.

### Tất cả tài liệu đều bị `SKIPPED`

Kiểm tra `KEYWORDS`, `ALLOWED_DOMAINS` và link trong RSS. Nếu RSS chỉ chứa link trang HTML hoặc link redirect, v1 sẽ bỏ qua.

### Task chạy nhưng không tạo dữ liệu

Kiểm tra **Start in**, đường dẫn Python, file `.env`, quyền ghi thư mục và log. Không dùng đường dẫn tương đối trong Task Scheduler nếu chưa đặt **Start in**.

### Chạy lại sau lỗi

Các bản ghi `FAILED` không được coi là đã tải thành công, nên có thể được thử lại ở lần chạy sau. Không xóa database để xử lý lỗi thông thường; hãy xem `collector.log` để xác định nguyên nhân.

## 11. Giới hạn và hướng mở rộng

V1 chưa phân tích trang HTML để tìm link tài liệu, chưa hỗ trợ đăng nhập, chưa gửi thông báo và chưa có dashboard. Có thể mở rộng `DocumentResolver` ở phiên bản sau, nhưng vẫn phải giữ allowlist domain, giới hạn dung lượng và nguyên tắc chỉ tải tài liệu được phép truy cập.
