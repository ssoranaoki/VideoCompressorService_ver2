import asyncio
import datetime
import inspect
import json
import os

from mmp_protocol import (
    create_mmp_body,
    create_mmp_header,
    parse_mmp_body,
    parse_mmp_header,
)


class Client:
    def __init__(self) -> None:
        # 接続情報
        self.host = "127.0.0.1"
        self.port = 8888
        # プロトコル情報
        self.header_bytes_int: int = 8
        #
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

        # レスポンスデータ保存場所
        self.response_dir = "./response_data/"
        os.makedirs(self.response_dir, exist_ok=True)

    async def connect(self):
        """
        サーバーへ接続
        """
        # 接続を作成
        self.reader, self.writer = await asyncio.open_connection(host=self.host, port=self.port)
        print(f"サーバーに接続中 host: {self.host} port: {self.port}")

    async def create_request(self, json_data: dict, media_type: str, payload: bytes):
        """
        MMPリクエストの作成

        Args
            json_data [dict]
                どのようにファイルを処理するかが記載されている指示
            media_type [str]
                ファイルタイプ 例）mp4、mp3、json、avi ...
            payload [bytes]
                動画データ

        Returns
            header_data_bytes
            body_data_bytes
        """
        # 各データのサイズを取得
        # json
        json_string = json.dumps(json_data)
        json_size = len(json_string.encode("utf-8"))
        # media
        media_type_size = len(media_type.encode("utf-8"))
        # payload
        payload_size = len(payload)

        # ヘッダーデータ作成
        header_data_bytes = create_mmp_header(json_size=json_size, media_type_size=media_type_size, payload_size=payload_size)

        # ボディデータ作成
        body_data_bytes = create_mmp_body(json_data=json_data, media_type=media_type, payload=payload)

        return header_data_bytes, body_data_bytes

    async def send_request(self, header_data_bytes: bytes, body_data_bytes: bytes):
        """
        MMPリクエストをサーバーへ送信

        Args
            header_data_bytes [bytes] ヘッダーデータ
            body_data_bytes [bytes] ボディデータ
        """
        # サーバーとの接続確認
        if self.writer is None:
            raise ConnectionError("サーバーと通信できていません。再度接続してください")

        self.writer.write(header_data_bytes)
        self.writer.write(body_data_bytes)
        await self.writer.drain()

        print("リクエスト送信完了")

    async def receive_response(self):
        """サーバーからのレスポンスデータの受信

        Raises
            ConnectionError サーバーとの接続状態の確認

        Returns
            tuple [json_data, media_type, payload]
        """
        # サーバーとの接続確認
        if self.reader is None:
            raise ConnectionError("サーバーと通信できていません。再度接続してください")

        # ヘッダーデータの受信
        header_data_bytes: bytes = await self.reader.readexactly(self.header_bytes_int)

        # ヘッダーデータの解析
        json_size, media_type_size, payload_size= parse_mmp_header(header_bytes=header_data_bytes)

        # ボディデータの受信
        body_data_bytes = await self.reader.readexactly(json_size + media_type_size + payload_size)

        # ボディデータの解析
        json_data, media_type, payload = parse_mmp_body(body_bytes=body_data_bytes, json_size=json_size, media_type_size=media_type_size, payload_size=payload_size)
        print("レスポンスデータの受信完了")

        return json_data, media_type, payload

    async def send_ping(self) -> None:
        """
        サーバーと疎通確認を行う
        """
        # pingリクエストデータを準備
        json_data = {"action": "ping", "message": "connection_start"}
        media_type = "text/plain"
        payload = b""

        # リクエストデータの作成
        header_data_bytes, body_data_bytes = await self.create_request(json_data=json_data, media_type=media_type, payload=payload)

        # リクエストデータの送信
        await self.send_request(header_data_bytes=header_data_bytes, body_data_bytes=body_data_bytes)

        # レスポンスデータの受信
        response_json, _, _ = await self.receive_response()

        if response_json.get("status") == "success":
            print("サーバーとの疎通確認が完了しました。")
        elif response_json.get("status") == "error":
            print("サーバーとの疎通確認が失敗しました。")

    async def get_media_type(self, file_path: str) -> str:
        """
        ファイルパスから拡張子を取得してメディアタイプを返す

        Args:
            file_path [str] ファイルパス（例）video.mp4

        Returns:
            media_type [str] メディアタイプ （例）video/mp4
        """
        # 拡張子とメディアタイプの関係性を辞書で管理
        extension_map = {
            ".mp4": "video/mp4",
            ".avi": "video/avi",
            ".mov": "video/mov",
            ".mp3": "audio/mp3"
        }

        # ファイルから拡張子を抽出
        _, ext =  os.path.splitext(file_path)

        # 拡張子に合ったメディアタイプを取得
        media_type = extension_map.get(ext)

        if media_type is None:
            raise ValueError(f"{ext} 拡張子は対応しておりません")
        else:
            return media_type

    async def upload_video_file(self, operation: str, file_path: str, parameters: dict) -> None:
        """
        サーバーへ動画ファイルをアップロード

        Args
            operation [str] 処理内容
            file_path [str] ファイルパス
            parameters dict[str, str] 追加パラメーター
        """

        # json作成
        json_data = {
            "action": "upload",
            "file_name": os.path.basename(file_path),
            "operation": operation,
            "parameters": parameters
        }

        # メディアタイプを取得
        media_type = await self.get_media_type(file_path=file_path)

        # バイナリモードで読込
        with open(file=file_path, mode="rb") as f:
            payload = f.read()

        # リクエストデータの作成
        header_data_bytes, body_data_bytes = await self.create_request(json_data=json_data, media_type=media_type, payload=payload)

        # リクエストデータの送信
        await self.send_request(header_data_bytes=header_data_bytes, body_data_bytes=body_data_bytes)

    async def get_user_input(self):
        """
        ユーザーから対話形式で入力を受け取る

        Returns
            [tuple] (operation, file_path, parameters)
        """

        print("\n=== 処理を選択してください ===")
        print("1. 圧縮(compress)")
        print("2. 解像度変更(resize)")
        print("3. アスペクト比変更(aspect)")
        print("4. 音声抽出(convert)")
        print("5. GIF/WEBM作成(trim)")

        operations: dict[str, str] = {
            "1": "compress",
            "2": "resize",
            "3": "aspect",
            "4": "convert",
            "5": "trim"
        }

        # 選択内容の入力
        operation: str | None = ""
        while True:
            choice: str= input("\n番号を入力してください (1-5):").strip()

            # 入力内容の確認
            if choice != "":
                operation = operations.get(choice)

                if operation is not None:
                    break
                else:
                    print("エラー: 番号1~5を入力してください")
            else:
                print("エラー: 未入力です")

        # アップロードファイルの入力
        file_path: str = ""
        while True:
            file_path = input("\nファイルパスを入力してください:").strip()

            # 入力内容確認
            if file_path != "":
                # ファイルの存在確認
                if not os.path.exists(file_path):
                    print("ファイルが存在しません")
                else:
                    break
            else:
                print("エラー: 未入力です")

        parameters: dict[str, str] = {}
        # 追加パラメーターの設定
        if operation == "resize": # 解像度変更
            print("\n===解像度を選択してください")
            print("1. 1900*1080")
            print("2. 1280*720")
            print("3. 640*480")
            while True:
                choice: str= input("\n番号を入力してください (1-3):").strip()
                # 未入力の確認
                if choice != "":
                    # 入力内容の確認
                    if choice in ["1", "2", "3"]:
                        parameters["size"] = choice
                        break
                    else:
                        print("エラー: 番号1~3を入力してください")
                else:
                    print("エラー: 未入力です")

        elif operation == "aspect": # アスペクト比変更
            print("\n===アスペクト比を選択してください")
            print("1. 16:9")
            print("2. 4:3")
            print("3. 1:1")
            while True:
                choice: str= input("\n番号を入力してください (1-3):").strip()
                # 未入力の確認
                if choice != "":
                    # 入力内容の確認
                    if choice in ["1", "2", "3"]:
                        parameters["ratio"] = choice
                        break
                    else:
                        print("エラー: 番号1~3を入力してください")
                else:
                    print("エラー: 未入力です")

            print("\n===フィット方法を選択してください")
            print("1. letterbox: 元の映像を維持し、余白を黒で埋める")
            print("2. stretch: 元の映像を引き延ばして目標アスペクト比に合わせる")
            while True:
                choice: str= input("\n番号を入力してください (1-2):").strip()
                # 未入力の確認
                if choice != "":
                    # 入力内容の確認
                    if choice in ["1", "2"]:
                        parameters["fit_mode"] = choice
                        break
                    else:
                        print("エラー: 番号1~2を入力してください")
                else:
                    print("エラー: 未入力です")

        elif operation == "trim": # gif or webmの作成
            print("\n===GIF or WEBMを選択してください")
            print("1. GIF")
            print("2. WEBM")
            while True:
                choice: str= input("\n番号を入力してください (1-2):").strip()
                # 未入力の確認
                if choice != "":
                    # 入力内容の確認
                    if choice in ["1", "2"]:
                        if choice == "1":
                            parameters["type"] = "gif"
                        else:
                            parameters["type"] = "webm"
                        break
                    else:
                        print("エラー: 番号1~2を入力してください")
                else:
                    print("エラー: 未入力です")

            while True:
                choice: str= input("\n切り取りを始める開始時間を入力してください。(例: 00:00:10 または 10):").strip()
                # 未入力の確認
                if choice != "":
                    parameters["start_time"] = choice
                    break
                else:
                    print("エラー: 未入力です")

            while True:
                choice: str= input("\n切り取り時間を入力してください。(例: 00:00:5 または 5):").strip()
                # 未入力の確認
                if choice != "":
                    parameters["duration"] = choice
                    break
                else:
                    print("エラー: 未入力です")

        return operation, file_path, parameters



    async def response_data_analysis(self):
        """
        レスポンスデータの受信と解析
        """
        # レスポンスデータの受信
        response_json, response_media_type, response_payload = await self.receive_response()

        # レスポンスデータの確認
        if response_json.get("status") == "success":

            # 指示内容のデータの確認
            operation: str | None = response_json.get("operation")
            if operation is None:
                raise ValueError("指示内容が存在しません。再度処理を行ってください")

            # 圧縮、音声抽出...ごとに処理を行う
            match operation:
                case "compress": # 圧縮
                    # レスポンスデータの保存パスを作成
                    save_file_path = await self.save_file_path_creation(operation=operation)

                    # 圧縮処理されたレスポンスデータを書き込む
                    with open(save_file_path, mode="wb") as f:
                        f.write(response_payload)
                        print(f"圧縮ファイルを {save_file_path} へ保存しました")

                case "resize": # 解像度変更
                    # レスポンスデータの保存パスを作成
                    save_file_path = await self.save_file_path_creation(operation=operation)

                    # 解像度変更されたレスポンスデータを書き込む
                    with open(save_file_path, mode="wb") as f:
                        f.write(response_payload)
                        print(f"解像度が変更されたファイルを {save_file_path} へ保存しました")

                case "aspect": # アスペクト比変更
                    # レスポンスデータの保存パスを作成
                    save_file_path = await self.save_file_path_creation(operation=operation)

                    # アスペクト比変更されたレスポンスデータを書き込む
                    with open(save_file_path, mode="wb") as f:
                        f.write(response_payload)
                        print(f"アスペクト比が変更されたファイルを {save_file_path} へ保存しました")

                case "convert": # コンバート
                    # レスポンスデータの保存パスを作成
                    save_file_path = await self.save_file_path_creation(operation=operation)

                    # コンバートされたレスポンスデータを書き込む
                    with open(save_file_path, mode="wb") as f:
                        f.write(response_payload)
                        print(f"コンバートファイルを {save_file_path} へ保存しました")

                case "trim": # gif or webm
                    # レスポンスデータの保存パスを作成
                    save_file_path = await self.save_file_path_creation(operation=operation, media_type=response_media_type)

                    # コンバートされたレスポンスデータを書き込む
                    with open(save_file_path, mode="wb") as f:
                        f.write(response_payload)
                        print(f"コンバートファイルを {save_file_path} へ保存しました")

        elif response_json.get("status") == "error":
            print("エラーが発生しました")

    async def upload_and_receive(self):
        """
        アップロード処理

        レスポンスデータ受信と解析
        """
        # ユーザーの入力処理
        operation, file_path, parameters = await self.get_user_input()

        # サーバーへファイルアップロード処理
        await self.upload_video_file(operation=operation, file_path=file_path, parameters=parameters)

        # サーバーからのレスポンスデータの受信と解析
        await self.response_data_analysis()

    async def save_file_path_creation(self, operation: str, media_type: str = "") -> str:
        """
        保存場所の作成をするヘルパーメソッド
            指示内容ごとに保存用ファイル名を作成
            ファイル名には秒まで含む日付データを連結させる

        Args
            operation [str] 指示内容 (例: compress, convert...)
            media_type [str] ファイルの種類 (例: video/mp3, video/mp4, video/gif)
        Returns
            save_file_path [str] ファイルの保存先
        """
        now = datetime.datetime.now()
        time_stamp_str = now.strftime("%Y%m%d_%H%M%S")

        match operation:
            case "compress": # 圧縮
                save_file_name = f"compressed_video_{time_stamp_str}.mp4"
                save_file_path = os.path.join(self.response_dir, save_file_name)

            case "resize": # 解像度変更
                save_file_name = f"resized_video_{time_stamp_str}.mp4"
                save_file_path = os.path.join(self.response_dir, save_file_name)

            case "aspect": # アスペクト比変更
                save_file_name = f"changed_aspect_video_{time_stamp_str}.mp4"
                save_file_path = os.path.join(self.response_dir, save_file_name)

            case "convert": # コンバート
                save_file_name = f"converted_video_{time_stamp_str}.mp3"
                save_file_path = os.path.join(self.response_dir, save_file_name)

            case "trim": # gif or webm
                if media_type != "":
                    if media_type == "video/gif":
                        save_file_name = f"changed_gif_video_{time_stamp_str}.gif"
                        save_file_path = os.path.join(self.response_dir, save_file_name)
                    elif media_type == "video/webm":
                        save_file_name = f"changed_webm_video_{time_stamp_str}.webm"
                        save_file_path = os.path.join(self.response_dir, save_file_name)

        return save_file_path

    async def execute_request(self, request_func, *args, **kwargs) -> None:
        """
        リクエストを実行するヘルパーメソッド
        - 接続 → リクエスト → 切断 を自動で行う

        Args
            request_fund 実行するメソッド (例: send_ping, upload_video...)
            args メソッドの位置引数
            kwargs メソッドのキーワード引数
        """
        # サーバーへ接続
        await self.connect()

        # リクエスト処理
        await request_func(*args, **kwargs)

        # 接続を閉じる
        await self.close()

    async def close(self):
        """
        サーバーとの接続を閉じる
        """
        # サーバーと接続していない場合は何もしない
        if self.writer is None:
            return

        # 接続を閉じる
        self.writer.close()
        await self.writer.wait_closed()
        print("サーバーとの接続を閉じました。")

    async def main(self):
        try:
            # サーバーとの疎通確認
            await self.execute_request(self.send_ping)

            # サーバーへファイルをアップロード処理とレスポンスデータの受信と解析
            await self.execute_request(self.upload_and_receive)

        except Exception as e:
            print(f"{inspect.currentframe().f_code.co_name}関数でエラー発生") # type: ignore
            print(f"エラー内容：{e}")

if __name__ == "__main__":
    client = Client()
    try:
        asyncio.run(client.main())
    except KeyboardInterrupt:
        print("\nサーバーへの接続を終了します")