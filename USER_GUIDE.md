# VideoCompressorService User Guide

## Overview

VideoCompressorService is a client-server application that allows you to upload video files and perform various processing operations. The service uses a custom binary protocol (MMP - Multiple Media Protocol) over TCP for reliable communication between client and server.

## Features

The service supports the following video processing operations:

1. **Compress** - Reduce video file size with automatic quality optimization
2. **Resize** - Change video resolution to standard formats
3. **Aspect Ratio** - Modify video aspect ratio with letterbox or stretch modes
4. **Convert to Audio** - Extract audio from video and save as MP3
5. **Create Clips** - Generate GIF or WEBM clips from specific time ranges

All video processing is performed using FFmpeg, supporting all formats that FFmpeg supports.

## Requirements

### System Requirements

- Python 3.10 or higher
- FFmpeg installed and available in system PATH

### Python Dependencies

- asyncio (built-in)
- Standard library modules: json, os, datetime, subprocess

### Installing FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

Verify installation:
```bash
ffmpeg -version
```

## Setup

### 1. Clone or Download the Repository

```bash
git clone <repository-url>
cd VideoCompressorService_ver2
```

### 2. Verify Files

Ensure the following files are present:
- `server.py` - Server application
- `client.py` - Client application
- `mmp_protocol.py` - Protocol implementation
- `ffmpeg_function.py` - Video processing functions

### 3. Configure Connection (Optional)

By default, the service uses:
- Host: `127.0.0.1` (localhost)
- Port: `8888`

To change these settings, edit the `__init__` methods in both `client.py` and `server.py`:

```python
self.host = "127.0.0.1"  # Change to your desired host
self.port = 8888         # Change to your desired port
```

## Usage

### Starting the Server

1. Open a terminal and navigate to the project directory
2. Start the server:

```bash
python server.py
```

You should see:
```
サーバー起動： ip 127.0.0.1 port 8888
```

The server will continue running and wait for client connections. Keep this terminal open.

### Running the Client

1. Open a **new terminal** (keep the server running in the first terminal)
2. Navigate to the project directory
3. Run the client:

```bash
python client.py
```

### Using the Client Interface

The client provides an interactive menu to select operations:

```
=== 処理を選択してください ===
1. 圧縮(compress)
2. 解像度変更(resize)
3. アスペクト比変更(aspect)
4. 音声抽出(convert)
5. GIF/WEBM作成(trim)
```

## Operation Details

### 1. Compress Video

**Purpose:** Reduce video file size while maintaining good quality.

**Steps:**
1. Select option `1` from the menu
2. Enter the path to your video file
3. Wait for processing to complete

**Example:**
```
番号を入力してください (1-5): 1
ファイルパスを入力してください: /path/to/video.mp4
```

**Output:** Compressed video saved to `./response_data/compress_video_TIMESTAMP.mp4`

**Technical Details:**
- Uses H.264 codec with CRF 28
- Audio is removed to maximize compression
- Automatically optimizes for file size reduction

### 2. Resize Video Resolution

**Purpose:** Change video dimensions to standard resolutions.

**Steps:**
1. Select option `2` from the menu
2. Enter the path to your video file
3. Choose target resolution:
   - `1` - 1920x1080 (Full HD)
   - `2` - 1280x720 (HD)
   - `3` - 640x480 (SD)

**Example:**
```
番号を入力してください (1-5): 2
ファイルパスを入力してください: /path/to/video.mp4

===解像度を選択してください
1. 1900*1080
2. 1280*720
3. 640*480

番号を入力してください (1-3): 2
```

**Output:** Resized video saved to `./response_data/resize_video_TIMESTAMP.mp4`

### 3. Change Aspect Ratio

**Purpose:** Modify video aspect ratio with different fitting modes.

**Steps:**
1. Select option `3` from the menu
2. Enter the path to your video file
3. Choose target aspect ratio:
   - `1` - 16:9 (Widescreen)
   - `2` - 4:3 (Standard)
   - `3` - 1:1 (Square)
4. Choose fit mode:
   - `1` - Letterbox (adds black bars, preserves original content)
   - `2` - Stretch (distorts to fill frame)

**Example:**
```
番号を入力してください (1-5): 3
ファイルパスを入力してください: /path/to/video.mp4

===アスペクト比を選択してください
1. 16:9
2. 4:3
3. 1:1

番号を入力してください (1-3): 1

===フィット方法を選択してください
1. letterbox: 元の映像を維持し、余白を黒で埋める
2. stretch: 元の映像を引き延ばして目標アスペクト比に合わせる

番号を入力してください (1-2): 1
```

**Output:** Modified video saved to `./response_data/aspect_video_TIMESTAMP.mp4`

### 4. Convert Video to Audio (MP3)

**Purpose:** Extract audio track from video and save as MP3.

**Steps:**
1. Select option `4` from the menu
2. Enter the path to your video file
3. Wait for processing to complete

**Example:**
```
番号を入力してください (1-5): 4
ファイルパスを入力してください: /path/to/video.mp4
```

**Output:** Audio file saved to `./response_data/convert_video_TIMESTAMP.mp3`

**Technical Details:**
- Uses libmp3lame codec
- Maintains original audio quality

### 5. Create GIF or WEBM Clip

**Purpose:** Extract a portion of video and convert to GIF or WEBM format.

**Steps:**
1. Select option `5` from the menu
2. Enter the path to your video file
3. Choose output format:
   - `1` - GIF
   - `2` - WEBM
4. Enter start time (format: `HH:MM:SS` or seconds)
5. Enter duration (format: `HH:MM:SS` or seconds)

**Example:**
```
番号を入力してください (1-5): 5
ファイルパスを入力してください: /path/to/video.mp4

===GIF or WEBMを選択してください
1. GIF
2. WEBM

番号を入力してください (1-2): 1

切り取りを始める開始時間を入力してください。(例: 00:00:10 または 10): 10

切り取り時間を入力してください。(例: 00:00:5 または 5): 5
```

**Output:** Clip saved to `./response_data/trim_video_TIMESTAMP.gif` or `.webm`

**Technical Details:**
- GIF: 10 fps, scaled to 320px width (maintains aspect ratio)
- WEBM: Uses VP9 codec with CRF 30

## File Locations

### Input Files

You can place your video files anywhere on your system. When prompted, provide the full or relative path to the file.

**Examples:**
- Absolute path: `/home/user/videos/sample.mp4`
- Relative path: `./videos/sample.mp4`
- Current directory: `sample.mp4`

### Output Files

All processed files are automatically saved to the `./response_data/` directory, which is created automatically in the same location as `client.py`.

**Output file naming pattern:**
- Compress: `compress_video_YYYYMMDD_HHMMSS.mp4`
- Resize: `resize_video_YYYYMMDD_HHMMSS.mp4`
- Aspect: `aspect_video_YYYYMMDD_HHMMSS.mp4`
- Convert: `convert_video_YYYYMMDD_HHMMSS.mp3`
- Trim: `trim_video_YYYYMMDD_HHMMSS.gif` or `.webm`

### Temporary Files

The server stores uploaded and processed files temporarily in the `./upload/` directory. These files are automatically deleted after the response is sent to the client.

## Supported File Formats

The service supports all video formats that FFmpeg supports, including:

**Video Formats:**
- MP4 (.mp4)
- AVI (.avi)
- MOV (.mov)
- MKV (.mkv)
- FLV (.flv)
- WMV (.wmv)
- And many more

**Output Formats:**
- Video: MP4
- Audio: MP3
- Clips: GIF, WEBM

## Troubleshooting

### Server Won't Start

**Problem:** `Address already in use` error

**Solution:** Another process is using port 8888. Either:
1. Stop the other process
2. Change the port in both `server.py` and `client.py`

### Client Can't Connect

**Problem:** `Connection refused` error

**Solution:**
1. Verify the server is running
2. Check that host and port match in both client and server
3. Check firewall settings if using remote connection

### File Not Found Error

**Problem:** Client reports file doesn't exist

**Solution:**
1. Verify the file path is correct
2. Use absolute paths if relative paths don't work
3. Check file permissions

### FFmpeg Errors

**Problem:** Processing fails with FFmpeg error

**Solution:**
1. Verify FFmpeg is installed: `ffmpeg -version`
2. Check that the input file is not corrupted
3. Ensure the file format is supported
4. Check server terminal for detailed error messages

### Processing Takes Too Long

**Problem:** Video processing is very slow

**Solution:**
- Large files take longer to process
- Compression and resolution changes are CPU-intensive
- Consider using smaller files for testing
- Check system resources (CPU, memory)

### Output File Quality Issues

**Problem:** Compressed video quality is poor

**Solution:**
- Compression uses CRF 28 for good balance of size/quality
- For higher quality, you would need to modify the FFmpeg parameters in `ffmpeg_function.py`

## Advanced Configuration

### Modifying FFmpeg Parameters

To customize video processing parameters, edit the functions in `ffmpeg_function.py`:

**Example - Change compression quality:**
```python
# In compress_video_file function
# Change CRF value (lower = better quality, larger file)
"-crf", "28",  # Change to "23" for higher quality
```

### Running on Different Machines

To run the server on one machine and client on another:

1. **On the server machine:**
   - Edit `server.py` to bind to all interfaces:
     ```python
     self.host = "0.0.0.0"
     ```
   - Note the server's IP address

2. **On the client machine:**
   - Edit `client.py` with the server's IP:
     ```python
     self.host = "192.168.1.100"  # Server's IP address
     ```

3. Ensure firewall allows connections on port 8888

## Protocol Information (MMP)

The service uses a custom Multiple Media Protocol (MMP) for communication:

**Header (8 bytes):**
- JSON size (2 bytes) - Size of JSON metadata
- Media type size (1 byte) - Size of media type string
- Payload size (5 bytes) - Size of file data

**Body (variable):**
- JSON data - Operation instructions and parameters
- Media type - File format (e.g., "video/mp4")
- Payload - Binary file data

**Maximum Sizes:**
- JSON: 65,535 bytes (64 KB)
- Media type: 255 bytes
- Payload: 1,099,511,627,775 bytes (~1 TB)

## Security Considerations

1. **Local Use Only:** By default, the server only accepts connections from localhost (127.0.0.1)
2. **No Authentication:** The service does not implement authentication. Do not expose to untrusted networks.
3. **Temporary Storage:** All files are deleted after processing
4. **File Size Limits:** Be aware of disk space when processing large files

## Performance Notes

- The server can handle multiple operations sequentially
- Each operation runs in a separate thread to avoid blocking
- Processing time depends on:
  - File size
  - Video resolution
  - Operation type
  - System CPU performance

## Stopping the Service

### Stop the Client

The client automatically disconnects after each operation completes.

### Stop the Server

Press `Ctrl+C` in the server terminal:
```
^C
サーバーを停止しました
```

## Example Workflow

Here's a complete example of compressing a video:

1. **Start the server:**
   ```bash
   python server.py
   ```
   Output: `サーバー起動： ip 127.0.0.1 port 8888`

2. **Run the client (in a new terminal):**
   ```bash
   python client.py
   ```

3. **Select compress operation:**
   ```
   番号を入力してください (1-5): 1
   ```

4. **Enter file path:**
   ```
   ファイルパスを入力してください: ./my_video.mp4
   ```

5. **Wait for processing:**
   ```
   サーバーに接続中 host: 127.0.0.1 port: 8888
   サーバーとの疎通確認が完了しました。
   リクエスト送信完了
   レスポンスデータの受信完了
   圧縮ファイルを ./response_data/compress_video_20231027_153045.mp4 へ保存しました
   ```

6. **Find your processed video:**
   ```bash
   ls ./response_data/
   ```

## Getting Help

If you encounter issues not covered in this guide:

1. Check the server terminal for detailed error messages
2. Verify all requirements are installed correctly
3. Test with a small, simple video file first
4. Ensure FFmpeg is working: `ffmpeg -version`

## License and Credits

This service uses FFmpeg for all video processing operations. FFmpeg is licensed under the LGPL or GPL depending on configuration.
