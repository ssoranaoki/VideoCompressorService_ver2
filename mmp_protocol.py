import json


def create_mmp_header(
        json_size: int,
        media_type_size: int,
        payload_size: int,
    ) -> bytes:
    """
    MMPヘッダーを作成（8バイト）
    """

    # ヘッダーサイズ
    HEADER_BYTES = 8

    # 各フィールドをバイト列に変換
    json_bytes = json_size.to_bytes(2, byteorder='big')
    media_type_bytes = media_type_size.to_bytes(1, byteorder='big')
    payload_bytes = payload_size.to_bytes(5, byteorder='big')

    mmp_header_bytes = json_bytes + media_type_bytes + payload_bytes

    # 8バイトであることを確認
    if len(mmp_header_bytes) != HEADER_BYTES:
        raise ValueError(f"ヘッダーのサイズが8バイトではありません。実際: {len(mmp_header_bytes)}バイト")

    return mmp_header_bytes


def create_mmp_body(
        json_data: dict,
        media_type: str,
        payload: bytes
) -> bytes:
    """
    MMPボディを作成
    """

    # 定数定義
    MAX_JSON_SIZE = 2 ** 16 - 1
    MAX_MEDIA_TYPE_SIZE = 2 ** 8 - 1
    MAX_PAYLOAD_SIZE = 2 ** 40 - 1


    # jsonデータのコンバート
    json_string = json.dumps(json_data, ensure_ascii=False)
    converted_json_data = json_string.encode("utf-8")

    # media_typeデータのコンバート
    if not media_type:
        raise ValueError("メディアタイプが空です")
    else:
        converted_media_type_data = media_type.encode("utf-8")

    # サイズチェック
    if len(converted_json_data) > MAX_JSON_SIZE:
        raise ValueError(f"JSONサイズが上限を超えています: {len(converted_json_data)} > {MAX_JSON_SIZE}")
    if len(converted_media_type_data) > MAX_MEDIA_TYPE_SIZE:
        raise ValueError(f"メディアタイプサイズが上限を超えています: {len(converted_media_type_data)} > {MAX_MEDIA_TYPE_SIZE}")
    if len(payload) > MAX_PAYLOAD_SIZE:
        raise ValueError(f"ペイロードサイズが上限を超えています: {len(payload)} > {MAX_PAYLOAD_SIZE}")

    return converted_json_data + converted_media_type_data + payload


def parse_mmp_header(header_bytes: bytes) -> tuple[int, int, int]:
    """
    MMPヘッダーを解析（8バイト）

    Returns:
        (json_size, media_type_size, payload_size)
    """

    # ヘッダーサイズの確認
    if len(header_bytes) != 8:
        raise ValueError(f"ヘッダーは8バイト必要です（受信: {len(header_bytes)}バイト）")

    # バイト列から各フィールドを抽出
    json_size = int.from_bytes(header_bytes[0:2], byteorder="big")
    media_type_size = int.from_bytes(header_bytes[2:3], byteorder="big")
    payload_size = int.from_bytes(header_bytes[3:8], byteorder="big")

    return (json_size, media_type_size, payload_size)

def parse_mmp_body(
    body_bytes: bytes,
    json_size: int,
    media_type_size: int,
    payload_size: int
) -> tuple[dict, str, bytes]:
    """
    MMPボディを解析

    Returns:
        (json_data, media_type, payload)
    """

    # 期待されるボディサイズを計算
    expected_body_size = json_size + media_type_size + payload_size
    if len(body_bytes) != expected_body_size:
        raise ValueError(f"ボディサイズが不一致です（期待: {expected_body_size}、受信: {len(body_bytes)}）")

    # バイト列で現在、読み込んでいる位置
    current_position = 0

    # バイト列から各部分を抽出
    # json
    json_bytes = body_bytes[current_position:current_position + json_size]
    json_data = json.loads(json_bytes.decode("utf-8"))
    current_position += json_size
    # media
    media_type_bytes = body_bytes[current_position:current_position + media_type_size]
    media_type = media_type_bytes.decode("utf-8")
    current_position += media_type_size
    # payload
    payload = body_bytes[current_position:current_position + payload_size]

    return (json_data, media_type, payload)


# def parse_mmp_message(message_bytes: bytes) -> tuple[dict, str, bytes]:
#     """
#     完全なMMPメッセージを解析

#     Returns:
#         (json_data, media_type, payload)
#     """
#     pass