import crawlingBid
import boto3
import os

s3_client = boto3.client('s3')
s3_bucket = boto3.resource('s3').Bucket(os.environ['s3_bucket'])


def get_s3_file_list(s3_path):
    """s3ファイル一覧取得
        環境変数「s3_bucket」のバケットを参照する

    Args:
        s3_path (str): 取得先のフォルダパス

    Returns:
        list: ファイル名（Key）の一覧
    """

    # ファイル一覧取得
    file_list = s3_client.list_objects_v2(
        Bucket=os.environ['s3_bucket'],
        Prefix=s3_path)
    Keys = [d['Key'] for d in file_list['Contents']]

    # フォルダを除く
    Keys.remove(s3_path)

    # 一覧を返却
    return Keys


def s3_download_to_tmp(folder_name):
    """s3ファイルのダウンロード（ローカル/tmpへ）
        環境変数「s3_bucket」のバケットに対して処理する

    Args:
        folder_name (str): ダウンロード元の(bucket下の)フォルダ名
    """

    # フォルダ作成
    tmp_path = '/tmp/' + folder_name + '/'
    s3_path = folder_name + '/'
    os.makedirs(tmp_path, exist_ok=True)

    # ファイル一覧取得
    file_list = get_s3_file_list(s3_path)
    for file in file_list:
        file_name = file[len(s3_path):]
        s3_bucket.download_file(file, tmp_path + file_name)


def s3_upload_from_tmp(folder_name, all_del=False):
    """s3ファイルのアップロード（ローカル/tmpから）
        環境変数「s3_bucket」のバケットに対して処理する

    Args:
        folder_name (str): アップロード元（/tmp下の）フォルダ名
        all_del (bool): アップロード前にフォルダ内の
                        ファイルを削除（Default：False）
    """

    tmp_path = '/tmp/' + folder_name + '/'
    s3_path = folder_name + '/'

    if all_del:
        file_list = get_s3_file_list(s3_path)
        for file in file_list:
            s3_client.delete_object(
                Bucket=os.environ['s3_bucket'],
                Key=file)

    for file in os.listdir(tmp_path):
        s3_bucket.upload_file(
            tmp_path + file,
            s3_path + file)


def lambda_handler(event, context):
    """lambda起動ハンドラ

    Args:
        event (any): 未使用
        context (any): 未使用
    """

    # 前処理
    # s3のファイルをローカル/tmpにダウンロード
    s3_download_to_tmp('url')
    s3_download_to_tmp('output/before')
    s3_download_to_tmp('output/difference')
    s3_download_to_tmp('log')

    # クローリングを実行する
    crawlingBid.main()

    # 後処理
    # ローカル/tmpをs3にアップロード
    s3_upload_from_tmp('output/before', all_del=True)
    s3_upload_from_tmp('output/difference', all_del=True)
    s3_upload_from_tmp('mail_file')
    s3_upload_from_tmp('log')
