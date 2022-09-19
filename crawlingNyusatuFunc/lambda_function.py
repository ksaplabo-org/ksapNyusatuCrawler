import crawlingBid
import boto3
import os

s3_client = boto3.client('s3')
s3_bucket = boto3.resource('s3').Bucket(os.environ['s3_bucket'])


def get_s3_file_list(s3_path):

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
    
    # 前処理
    s3_download_to_tmp('url')
    s3_download_to_tmp('output/before')
    s3_download_to_tmp('output/difference')
    s3_download_to_tmp('log')
    
    crawlingBid.main('None')
    
    # 後処理
    s3_upload_from_tmp('output/before', all_del=True)
    s3_upload_from_tmp('output/difference', all_del=True)
    s3_upload_from_tmp('mail_file')
    s3_upload_from_tmp('log')
    
