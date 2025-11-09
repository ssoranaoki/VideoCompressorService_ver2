import inspect
import subprocess


def compress_video_file(input_path: str, output_path: str) -> bool:
    """動画を圧縮する

    Args
        input_path [str] 入力動画ファイルパス
        output_path [str] 出力動画ファイルパス
    """
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-i",
                input_path,
                "-vcodec",
                "libx264",
                "-crf",
                "28",
                "-preset",
                "medium",
                "-tune",
                "film",
                "-an",  # 音声を削除
                "-f",
                "mp4",
                output_path,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return True
        else:
            print(f"{inspect.currentframe().f_code.co_name}関数でffmpegエラーが発生しました: {result.stderr}") # type: ignore
            return False

    except Exception as e:
        print(f"{inspect.currentframe().f_code.co_name}関数でエラーが発生しました: {e}") # type: ignore
        return False


def resize_video_resolution(input_path: str, resolution: str, output_path: str) -> bool:
    """動画の解像度を変更する

    Args
        input_path [str] 入力動画ファイルパス
        resolution [str] 変更したい解像度 (例: "1" 1900*1080 "2" 1280*720 "3" 640*480)
        output_path [str] 出力動画ファイルパス
    """
    try:
        if resolution == "1":
            width = 1920
            height = 1080
        elif resolution == "2":
            width = 1280
            height = 720
        elif resolution == "3":
            width = 640
            height = 480
        elif resolution == "4":
            width = 320
            height = 240

        result = subprocess.run(
            [
                "ffmpeg",
                "-i",
                input_path,
                "-vf",
                f"scale={width}:{height}",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "23",
                "-c:a",
                "copy",
                "-f",
                "mp4",
                output_path,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return True
        else:
            print(f"{inspect.currentframe().f_code.co_name}関数でffmpegエラーが発生しました: {result.stderr}") # type: ignore
            return False

    except Exception as e:
        print(f"{inspect.currentframe().f_code.co_name}関数でエラーが発生しました: {e}") # type: ignore
        return False


def change_video_aspect_ratio(input_path: str, aspect_ratio: str, output_path: str, fit_mode: str) -> bool:
    """動画のアスペクト比を変更する

    Args
        input_path [str] 入力動画ファイルパス
        aspect_ratio [str] アスペクト比 "1" (16:9), "2" (4:3), "3" (1:1)
        output_path [str] 出力動画ファイルパス
        fit_mode [str] フィット方法
            "1" (letterbox: 元の映像を維持し、余白を黒で埋める)
            "2" ("stretch: 元の映像を引き延ばして目標アスペクト比に合わせる)
    """

    # アスペクト比の設定
    if aspect_ratio == "1":
        width_ratio = 16
        height_ratio = 9
    elif aspect_ratio == "2":
        width_ratio = 4
        height_ratio = 3
    elif aspect_ratio == "3":
        width_ratio = 1
        height_ratio = 1

    try:
        # アスペクト比を計算
        target_aspect = float(width_ratio) / float(height_ratio)

        if fit_mode == "1":
            # letterbox: 元の映像を維持し、余白を黒で埋める
            scale_filter = f"scale=iw*min(1\\,if(sar\\,1/sar\\,1)*{target_aspect}/dar):ih*min(1\\,dar/({target_aspect}*if(sar\\,sar\\,1))),pad=iw*{target_aspect}/dar:ih:x=(ow-iw)/2:y=(oh-ih)/2:color=black"
        elif fit_mode == "2":
            # stretch: 元の映像を引き延ばして目標アスペクト比に合わせる
            scale_filter = f"scale=iw:ih,setsar={aspect_ratio}"
        else:
            print(f"不正なfit_mode: {fit_mode}. 'letterbox', 'stretch'のいずれかを指定してください")
            return False

        result = subprocess.run(
            [
                "ffmpeg",
                "-i",
                input_path,
                "-vf",
                scale_filter,
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "23",
                "-c:a",
                "copy",
                "-f",
                "mp4",
                output_path,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return True
        else:
            print(f"{inspect.currentframe().f_code.co_name}関数でffmpegエラーが発生しました: {result.stderr}") # type: ignore
            return False

    except Exception as e:
        print(f"{inspect.currentframe().f_code.co_name}関数でエラーが発生しました: {e}") # type: ignore
        return False


def convert_to_mp3file(input_path: str, output_path: str) -> bool:
    """MP3形式へ変換する

        input_path [str] 入力動画ファイルパス
        output_path [str] 出力動画ファイルパス
    """
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-i",
                input_path,
                "-vn",
                "-acodec",
                "libmp3lame",
                "-f",
                "mp3",
                output_path,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return True
        else:
            print(f"{inspect.currentframe().f_code.co_name}関数でffmpegエラーが発生しました: {result.stderr}") # type: ignore
            return False

    except Exception as e:
        print(f"{inspect.currentframe().f_code.co_name}関数でエラーが発生しました: {e}") # type: ignore
        return False


def trim_video_to_gif_webm(
    input_path: str,
    start_time: str,
    duration: str,
    output_path: str,
    output_format: str,
) -> bool:
    """時間範囲を指定して動画を切り取り、GIFまたはWEBMフォーマットに変換する

    Args
        input_path [str] 入力動画ファイルのパス
        start_time [str] 開始時間 (例: "00:00:10" または "10")
        duration [str] 切り取り時間の長さ (例: "00:00:05" または "5")
        output_path [str] 出力ファイルのパス
        output_format [str] 出力フォーマット ("gif" または "webm")

    Returns
        [bool] 成功時True、失敗時False
    """
    try:
        if output_format.lower() == "gif": # GIF変換用のffmpegコマンド
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    input_path,
                    "-ss",
                    start_time,
                    "-t",
                    duration,
                    "-vf",
                    "fps=10,scale=320:-1:flags=lanczos",
                    "-c:v",
                    "gif",
                    "-y",  # 既存ファイルを上書き
                    output_path,
                ],
                capture_output=True,
                text=True,
            )
        elif output_format.lower() == "webm": # WEBM変換用のffmpegコマンド
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    input_path,
                    "-ss",
                    start_time,
                    "-t",
                    duration,
                    "-c:v",
                    "libvpx-vp9",
                    "-crf",
                    "30",
                    "-b:v",
                    "0",
                    "-an",  # 音声を削除
                    "-y",  # 既存ファイルを上書き
                    output_path,
                ],
                capture_output=True,
                text=True,
            )
        else:
            print(f"サポートされていないフォーマット: {output_format}")
            return False

        if result.returncode == 0:
            print(f"動画切り取り・変換成功: {output_path}")
            return True
        else:
            print(f"{inspect.currentframe().f_code.co_name}関数でffmpegエラーが発生しました: {result.stderr}") # type: ignore
            return False

    except Exception as e:
        print(f"{inspect.currentframe().f_code.co_name}関数でエラーが発生しました: {e}") # type: ignore
        return False
