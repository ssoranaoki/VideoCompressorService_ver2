import asyncio
import datetime
import inspect
import json
import os

import ffmpeg_function
from mmp_protocol import (
    create_mmp_body,
    create_mmp_header,
    parse_mmp_body,
    parse_mmp_header,
)


class Server:
    def __init__(self) -> None:
        self.host = "127.0.0.1"
        self.port = 8888
        self.header_bytes_int: int = 8

        # 動画ファイルのアップロード先
        self.upload_dir = "./upload/"
        # 動画ファイルのアップロード先の作成（存在する場合は何もしない）
        os.makedirs(self.upload_dir, exist_ok=True)

        # マイクロ秒まで含んだ値
        # 例: 20231027_153045_123456
        # 一時保存ファイルに連結させて一意性を保つ
        now = datetime.datetime.now()
        self.time_stamp_str = now.strftime("%Y%m%d_%H%M%S_%f")

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """

        """
        client_address = writer.get_extra_info('peername')
        print(f"クライアント接続： {client_address}")

        header_bytes = await reader.readexactly(self.header_bytes_int)
        print(f"ヘッダー受信 {len(header_bytes)}バイト")

        # ヘッダーを解析
        json_size, media_type_size, payload_size = parse_mmp_header(header_bytes=header_bytes)
        print(f"解析結果: JSON={json_size}B, media_type={media_type_size}B, payload={payload_size}B")

        # ボディデータのサイズを計算
        body_size = json_size + media_type_size + payload_size
        body_bytes = await reader.readexactly(body_size)
        print(f"ボディデータ受信: {len(body_bytes)}バイト")

        # ボディデータを解析
        json_data, media_type, payload = parse_mmp_body(
            body_bytes=body_bytes,
            json_size=json_size,
            media_type_size=media_type_size,
            payload_size=payload_size
        )
        # デバッグ
        # print(f"JSON: {json_data}")
        # print(f"media_type: {media_type}")
        # print(f"payload: {payload}")

        # 一時保存ファイルのパスリスト
        # 一時ファイルの削除処理で使用
        tmp_files_path = []

        # # クライアントからのデータを確認して応答データの作成を行う
        match json_data.get("action"):
            # 疎通時
            case "ping":
                    response_json, response_media_type, response_payload = self.create_success_response(operation="ping")

            # ファイルアップロード時
            case "upload":
                # ファイル名取得
                upload_file_name: str | None = json_data.get("file_name")

                # ファイル名が存在しない場合はエラー内容をレスポンス
                if upload_file_name is None:
                    response_json, response_media_type, response_payload = self.create_error_response()

                else:
                    # ファイルの保存先のフルパスを作成
                    upload_file_path = os.path.join(self.upload_dir, upload_file_name)

                    # ファイルパスの保存
                    tmp_files_path.append(upload_file_path)

                    try:
                        # ファイルをバイナリデータで保存
                        with open(upload_file_path, "wb") as f:
                            f.write(payload)
                        print(f"ファイル保存完了: {upload_file_path}")

                        # 指示を確認して圧縮、音声抽出...などの処理を行う
                        match json_data.get("operation"):
                            case "compress": # 圧縮
                                # 出力ファイルパスの作成
                                output_file_name = f"compressed_video_{self.time_stamp_str}.mp4"
                                output_file_path = os.path.join(self.upload_dir, output_file_name)

                                # ファイルパスの保存
                                tmp_files_path.append(output_file_path)

                                # 別スレッドで圧縮を実行
                                success = await asyncio.to_thread(
                                    ffmpeg_function.compress_video_file,
                                    upload_file_path, # input_path
                                    "28",             # crf_number
                                    output_file_path  # output_path
                                )

                                # 結果を確認
                                if success:
                                    # 圧縮済ファイルを読み込んでレスポンスに含める
                                    with open(output_file_path, mode="rb") as f:
                                        # レスポンス作成
                                        response_json, response_media_type, response_payload = self.create_success_response(operation="compress", media_type="video/mp4", payload=f.read())
                                        print(f"{upload_file_name} の圧縮に成功")
                                else:
                                    # エラー内容レスポンス
                                    response_json, response_media_type, response_payload = self.create_error_response()

                            case "convert": # コンバート
                                # 出力ファイルパスの作成
                                output_file_name = f"converted_video_{self.time_stamp_str}.mp3"
                                output_file_path = os.path.join(self.upload_dir, output_file_name)

                                # ファイルパスの保存
                                tmp_files_path.append(output_file_path)

                                # 別スレッドでコンバートを実行
                                success = await asyncio.to_thread(
                                    ffmpeg_function.convert_to_mp3file,
                                    upload_file_path, # input_path
                                    output_file_path, # output_path
                                    "mp3"             # target_format
                                )

                                # 結果を確認
                                if success:
                                    # コンバート済ファイルを読み込んでレスポンスに含める
                                    with open(output_file_path, mode="rb") as f:
                                        # レスポンス作成
                                        response_json, response_media_type, response_payload = self.create_success_response(operation="convert", media_type="video/mp3", payload=f.read())
                                        print(f"{upload_file_name} をmp3形式へコンバートに成功")
                                else:
                                    # エラー内容レスポンス
                                    response_json, response_media_type, response_payload = self.create_error_response()

                            case "resize": # 解像度変更
                                # 出力ファイルパスの作成
                                output_file_name = f"resize_video_{self.time_stamp_str}.mp4"
                                output_file_path = os.path.join(self.upload_dir, output_file_name)

                                # ファイルパスの保存
                                tmp_files_path.append(output_file_path)

                                # 別スレッドで解像度変更を実行
                                success = await asyncio.to_thread(
                                    ffmpeg_function.resize_video_resolution,
                                    upload_file_path, # input_path
                                    "1",              # target_format
                                    output_file_path  # output_path
                                )

                                # 結果を確認
                                if success:
                                    # 処理されたファイルデータをレスポンスに含める
                                    with open(output_file_path, mode="rb") as f:
                                        # レスポンス作成
                                        response_json, response_media_type, response_payload = self.create_success_response(operation="resize", media_type="video/mp4", payload=f.read())
                                        print(f"{upload_file_name} の解像度変更に成功")
                                else:
                                    # エラー内容レスポンス
                                    response_json, response_media_type, response_payload = self.create_error_response()


                    except Exception as e:
                        print(f"{inspect.currentframe().f_code.co_name}関数でエラー発生") # type: ignore
                        print(f"エラー内容: {e}")
                        # エラー内容レスポンス
                        response_json, response_media_type, response_payload = self.create_error_response()

        # JSONサイズ
        response_json_string = json.dumps(response_json)
        response_json_size = len(response_json_string.encode("utf-8"))
        # Mediaサイズ
        response_media_type_size = len(response_media_type.encode("utf-8"))
        # Payloadサイズ
        response_payload_size = len(response_payload)

        # MMPプロトコルのヘッダー作成
        response_header= create_mmp_header(
            json_size=response_json_size,
            media_type_size=response_media_type_size,
            payload_size=response_payload_size
        )

        # MMPプロトコルのボディデータ作成
        response_body = create_mmp_body(
            json_data=response_json,
            media_type=response_media_type,
            payload=response_payload
        )

        # クライアントに送信
        writer.write(response_header)
        writer.write(response_body)
        await writer.drain()
        print("クライアントに送信完了")

        # 接続を閉じる
        writer.close()
        await writer.wait_closed()

        # 一時保存ファイルの削除
        await self.clean_up_files(tmp_files_path=tmp_files_path)

    async def server_start(self):
        """
        サーバーを起動する
        """
        try:
            server: asyncio.Server = await asyncio.start_server(self.handle_client, self.host, self.port)
            print(f"サーバー起動： ip {self.host} port {self.port}")

            async with server:
                await server.serve_forever()
        except KeyboardInterrupt:
            server.close()

    async def clean_up_files(self, tmp_files_path: list):
        """
        アップロードファイル、処理済ファイルの削除

        Args
            files [list]
            アップロードされた元ファイル、圧縮処理などを行ったファイル
        """
        try:
            for file in tmp_files_path:
                if os.path.exists(file):
                    os.remove(file)
                    print(f"一時保存ファイルの削除完了: {file}")

        except Exception as e:
            print(f"{inspect.currentframe().f_code.co_name}関数でエラー発生") # type: ignore
            print(f"エラー内容: {e}")

    def create_success_response(self, operation: str, media_type: str = "text/plain", payload: bytes = b""):
        """
        成功時のレスポンスデータの作成

        Args
            operation [str]
                指示内容
            media_type [str]
                初期値 = "text/plain"
                ファイル形式
            payload_data [bytes]
                初期値 = b""
                動画ファイルデータ

        Return
            tuple [response_json, response_media_type, response_payload]
        """
        response_json = {"status": "success", "operation": operation}
        response_media_type = media_type
        response_payload = payload

        return response_json, response_media_type, response_payload


    def create_error_response(self):
        """
        エラー時のレスポンスデータの作成

        Return
            tuple [response_json, response_media_type, response_payload]
        """
        response_json = {"status": "error"}
        response_media_type = "text/plain"
        response_payload = b""

        return response_json, response_media_type, response_payload



if __name__ == "__main__":
    server = Server()
    asyncio.run(server.server_start())